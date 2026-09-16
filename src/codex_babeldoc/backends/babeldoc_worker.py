"""BabelDOC worker process entry point.

Run as::

    python -m codex_babeldoc.backends.babeldoc_worker <request.json>

Protocol (see :mod:`codex_babeldoc.backends.worker_protocol`):

- request:  versioned JSON document on disk
- progress: JSONL ``{"type": "progress", ...}`` lines on stderr
- result:   one JSON document on stdout (completed) or failure JSON
- exit:     0 completed / 2 invalid request / 3 translation failed / 4 crashed

Plain ``print`` output from third-party libraries is redirected to stderr
before any heavy import happens, so stdout carries protocol data only.

stderr channel classification:

- BabelCodex ``logging`` diagnostics (for example gateway validation-retry
  warnings) are routed to ``worker-diagnostics.log`` inside the job working
  directory so the stderr channel stays machine-readable.
- Third-party diagnostics printed directly to stderr by BabelDOC
  (per-paragraph fallback tracebacks, PyMuPDF deprecation notices) are
  non-protocol output; :mod:`codex_babeldoc.backends.worker_protocol`
  parsing ignores them, and they are preserved as failure evidence by the
  worker client.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from codex_babeldoc.backends.worker_protocol import (
    EXIT_COMPLETED,
    EXIT_CRASHED,
    EXIT_REQUEST_INVALID,
    EXIT_TRANSLATION_FAILED,
    WorkerError,
    WorkerRequest,
    WorkerResult,
    encode_progress,
)

_ERROR_EXIT_BY_CODE = {"WORKER_REQUEST_INVALID": EXIT_REQUEST_INVALID}

#: Name of the diagnostics log file created inside the job working directory.
DIAGNOSTICS_LOG_FILENAME = "worker-diagnostics.log"


def _configure_worker_logging(working_dir: Path) -> None:
    """Route worker diagnostics to a file so stderr stays protocol-clean.

    The worker protocol carries JSONL progress on stderr. Without a handler,
    our library ``logging`` warnings (gateway validation-retry diagnostics and
    similar) reach stderr through Python's ``lastResort`` handler and pollute
    the protocol channel. This helper sends WARNING+ records to
    :data:`DIAGNOSTICS_LOG_FILENAME` inside the job working directory instead.
    Best-effort: if the file cannot be opened, the previous behavior is kept.
    """
    try:
        working_dir.mkdir(parents=True, exist_ok=True)
        target = working_dir / DIAGNOSTICS_LOG_FILENAME
    except OSError:
        return
    root = logging.getLogger()
    for existing in root.handlers:
        if isinstance(existing, logging.FileHandler) and existing.baseFilename == str(target):
            return
    try:
        handler = logging.FileHandler(target, encoding="utf-8")
    except OSError:
        return
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.WARNING)


def _redirect_stdout_to_stderr() -> object:
    """Redirect plain stdout writes to stderr so stdout carries protocol data only.

    Must run before any heavy third-party import (BabelDOC, ONNX, ...)
    because those libraries may ``print`` uncontrolled output. Returns the
    real stdout stream for writing the final protocol JSON.
    """
    real_stdout = sys.__stdout__
    sys.stdout = sys.stderr
    return real_stdout if real_stdout is not None else sys.stderr


def _emit(worker_error: WorkerError, protocol_stdout) -> int:
    protocol_stdout.write(worker_error.to_json() + "\n")
    protocol_stdout.flush()
    if worker_error.code in _ERROR_EXIT_BY_CODE:
        return _ERROR_EXIT_BY_CODE[worker_error.code]
    if worker_error.category == "worker":
        return EXIT_CRASHED
    return EXIT_TRANSLATION_FAILED


def _parse_pdf_request(raw: dict):
    from codex_babeldoc.backends.base import PdfTranslateRequest

    return PdfTranslateRequest(
        protocol_version=1,
        job_id=str(raw["job_id"]),
        source_path=Path(raw["source_path"]),
        output_dir=Path(raw["output_dir"]),
        working_dir=Path(raw["working_dir"]),
        lang_in=str(raw["lang_in"]),
        lang_out=str(raw["lang_out"]),
        backend_name=str(raw.get("backend_name", "babeldoc")),
        backend_version=str(raw.get("backend_version", "")),
        produce_mono=bool(raw.get("produce_mono", True)),
        produce_dual=bool(raw.get("produce_dual", True)),
        config_fingerprint=str(raw.get("config_fingerprint", "")),
        qps=int(raw.get("qps", 1)),
        min_text_length=int(raw.get("min_text_length", 5)),
        watermark_output_mode=str(raw.get("watermark_output_mode", "no_watermark")),
        auto_extract_glossary=bool(raw.get("auto_extract_glossary", False)),
        ocr_workaround=bool(raw.get("ocr_workaround", False)),
        auto_enable_ocr_workaround=bool(raw.get("auto_enable_ocr_workaround", True)),
        enhance_compatibility=bool(raw.get("enhance_compatibility", True)),
        translate_table_text=bool(raw.get("translate_table_text", False)),
    )


def _run(worker_request: WorkerRequest, protocol_stdout) -> int:
    started = time.monotonic()
    try:
        from codex_babeldoc.backends.babeldoc_v064 import BabelDocV064Backend
        from codex_babeldoc.backends.worker_protocol import WorkerArtifact
        from codex_babeldoc.translators.factory import build_gateway_translator

        def on_progress(event) -> None:
            sys.stderr.write(encode_progress(event) + "\n")
            sys.stderr.flush()

        pdf_request = _parse_pdf_request(worker_request.request)
        translator = build_gateway_translator(worker_request.translator)
        backend = BabelDocV064Backend()
        result = backend.translate(pdf_request, lambda: translator, on_progress=on_progress)

        artifacts = [
            WorkerArtifact(
                artifact_type=str(getattr(a.artifact_type, "value", a.artifact_type)),
                path=str(a.path),
                size=int(a.size),
            )
            for a in result.artifacts
        ]
        worker_result = WorkerResult(
            job_id=result.job_id,
            artifacts=artifacts,
            total_seconds=time.monotonic() - started,
            backend_name=result.backend_name,
            backend_version=result.backend_version,
        )
        protocol_stdout.write(worker_result.to_json() + "\n")
        protocol_stdout.flush()
        return EXIT_COMPLETED
    except Exception as exc:
        if isinstance(exc, KeyboardInterrupt):
            raise
        from codex_babeldoc.core.errors import classify_exception

        error = classify_exception(exc)
        return _emit(
            WorkerError(
                category=str(getattr(error.category, "value", error.category)),
                code=str(getattr(error.code, "value", error.code)),
                safe_message=error.safe_message,
                retryable=error.retryable,
                technical_message=error.technical_message,
            ),
            protocol_stdout,
        )


def main(
    argv: list[str] | None = None,
    protocol_stdout=None,
) -> int:
    """Entry point: parse the request file and run one translate operation."""
    if argv is None:
        argv = sys.argv[1:]
    if protocol_stdout is None:
        protocol_stdout = _redirect_stdout_to_stderr()

    if len(argv) != 1:
        return _emit(
            WorkerError(
                category="worker",
                code="WORKER_REQUEST_INVALID",
                safe_message="Worker requires exactly one request file argument.",
            ),
            protocol_stdout,
        )

    try:
        worker_request = WorkerRequest.from_json(Path(argv[0]).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - any parse failure is an invalid request
        return _emit(
            WorkerError(
                category="worker",
                code="WORKER_REQUEST_INVALID",
                safe_message="Worker request could not be parsed.",
                technical_message=str(exc),
            ),
            protocol_stdout,
        )

    _configure_worker_logging(Path(str(worker_request.request.get("working_dir", "."))))

    return _run(worker_request, protocol_stdout)


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from codex_babeldoc.core.artifacts import Artifact


def file_sha256(path: Path) -> str:
    """Return a streaming SHA-256 digest without retaining artifact contents."""
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_artifacts(
    artifacts: list[Artifact], output_dir: Path, *, update: bool = True
) -> tuple[bool, list[dict[str, object]]]:
    """Validate job-owned output artifacts and optionally refresh their manifest.

    The caller supplies persisted artifact paths rather than arbitrary user paths.
    Every artifact must resolve inside ``output_dir``. A non-empty persisted hash
    is treated as a content-integrity assertion and is never silently replaced.
    """
    output_root = output_dir.resolve()
    results: list[dict[str, object]] = []
    all_valid = bool(artifacts)

    for artifact in artifacts:
        path = Path(artifact.path).expanduser().resolve()
        try:
            path.relative_to(output_root)
        except ValueError:
            result = {
                "path": str(path),
                "exists": False,
                "size": 0,
                "sha256": "",
                "validated": False,
                "reason": "outside_output_directory",
            }
            results.append(result)
            all_valid = False
            if update:
                artifact.validated = False
            continue

        exists = path.is_file()
        actual_size = path.stat().st_size if exists else 0
        actual_hash = file_sha256(path) if exists else ""
        pdf_valid = path.suffix.lower() != ".pdf" or _looks_like_pdf(path)
        hash_matches = not artifact.sha256 or artifact.sha256 == actual_hash
        valid = exists and pdf_valid and hash_matches
        reason = ""
        if not exists:
            reason = "missing"
        elif not pdf_valid:
            reason = "invalid_pdf_header"
        elif not hash_matches:
            reason = "hash_mismatch"

        if update:
            artifact.size = actual_size
            if not artifact.sha256 and exists:
                artifact.sha256 = actual_hash
            artifact.validated = valid
        results.append(
            {
                "path": str(path),
                "exists": exists,
                "size": actual_size,
                "sha256": actual_hash,
                "validated": valid,
                "reason": reason or None,
            }
        )
        all_valid = all_valid and valid

    return all_valid, results


def _looks_like_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(5) == b"%PDF-"
    except OSError:
        return False

"""Error-category retry policy: pure resolution plus orchestrator no-loop gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from codex_babeldoc.application.service import (
    BabelCodexService,
    StartTranslationCommand,
)
from codex_babeldoc.core.config import AppConfig
from codex_babeldoc.core.errors import (
    DEFAULT_RETRY_LIMITS,
    BabelCodexError,
    ErrorCategory,
    ErrorCode,
    resolve_retry_limits,
    retry_limit_for,
)
from codex_babeldoc.core.state import JobStatus


def test_auth_input_and_validation_categories_default_to_single_attempt():
    limits = resolve_retry_limits(None, default_max=3)
    assert limits[ErrorCategory.AUTH] == 1
    assert limits[ErrorCategory.CONFIG] == 1
    assert limits[ErrorCategory.INPUT] == 1
    assert limits[ErrorCategory.VALIDATION] == 1
    assert limits[ErrorCategory.TRANSLATION] == 3


def test_global_max_retries_is_the_ceiling_for_category_limits():
    limits = resolve_retry_limits({"translation": 5}, default_max=2)
    assert limits[ErrorCategory.TRANSLATION] == 2
    assert retry_limit_for(ErrorCategory.TRANSLATION, {"translation": 5}, 2) == 2


def test_operator_policy_lowers_a_category_and_ignores_unknown_keys():
    limits = resolve_retry_limits({"auth": 2, "bogus": 9}, default_max=3)
    assert limits[ErrorCategory.AUTH] == 2
    assert limits[ErrorCategory.UNKNOWN] == DEFAULT_RETRY_LIMITS[ErrorCategory.UNKNOWN]


def test_retry_limit_for_uses_defaults_for_unlisted_categories():
    assert retry_limit_for(ErrorCategory.BABELDOC, {"auth": 1}, 3) == 2
    assert retry_limit_for(ErrorCategory.AUTH, None, 3) == 1


def _failing_service(
    tmp_path: Path,
    *,
    category: ErrorCategory,
    code: ErrorCode,
    retryable: bool,
) -> BabelCodexService:
    cfg = AppConfig(root=tmp_path)
    cfg.translation.translator = "mock"
    cfg.translation.max_retries = 3
    cfg.babeldoc.worker_mode = "inprocess"
    cfg.resolve_paths()
    cfg.ensure_dirs()
    service = BabelCodexService(cfg)

    class _FailingBackend:
        def translate(self, *_args, **_kwargs):
            raise BabelCodexError(
                category=category,
                code=code,
                safe_message="injected failure",
                retryable=retryable,
            )

    service.orchestrator.backend = _FailingBackend()
    return service


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "doc.pdf"
    source.write_bytes(b"%PDF-test")
    return source


def _load_failed_job(service: BabelCodexService, source: Path):
    return service.orchestrator.state.load(source, config_fingerprint=service.config.fingerprint())


def test_auth_failure_never_auto_loops_even_if_marked_retryable(tmp_path, monkeypatch):
    monkeypatch.setattr("codex_babeldoc.core.orchestrator.time.sleep", lambda _seconds: None)
    service = _failing_service(
        tmp_path,
        category=ErrorCategory.AUTH,
        code=ErrorCode.CODEX_NOT_LOGGED_IN,
        retryable=True,
    )
    source = _source(tmp_path)
    with pytest.raises(RuntimeError):
        service.start_translation(StartTranslationCommand(source_path=source))
    job = _load_failed_job(service, source)
    assert job.status is JobStatus.FAILED
    assert job.error_category is ErrorCategory.AUTH
    assert job.attempts == 1


def test_transient_translation_error_retries_to_category_limit(tmp_path, monkeypatch):
    monkeypatch.setattr("codex_babeldoc.core.orchestrator.time.sleep", lambda _seconds: None)
    service = _failing_service(
        tmp_path,
        category=ErrorCategory.TRANSLATION,
        code=ErrorCode.CODEX_TIMEOUT,
        retryable=True,
    )
    source = _source(tmp_path)
    with pytest.raises(RuntimeError):
        service.start_translation(StartTranslationCommand(source_path=source))
    job = _load_failed_job(service, source)
    assert job.status is JobStatus.FAILED
    assert job.attempts == 3


def test_operator_policy_caps_translation_attempts(tmp_path, monkeypatch):
    monkeypatch.setattr("codex_babeldoc.core.orchestrator.time.sleep", lambda _seconds: None)
    service = _failing_service(
        tmp_path,
        category=ErrorCategory.TRANSLATION,
        code=ErrorCode.CODEX_TIMEOUT,
        retryable=True,
    )
    service.config.translation.retry_policy = {"translation": 2}
    source = _source(tmp_path)
    with pytest.raises(RuntimeError):
        service.start_translation(StartTranslationCommand(source_path=source))
    job = _load_failed_job(service, source)
    assert job.status is JobStatus.FAILED
    assert job.attempts == 2


def test_pipeline_meta_is_recorded_and_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr("codex_babeldoc.core.orchestrator.time.sleep", lambda _seconds: None)
    service = _failing_service(
        tmp_path,
        category=ErrorCategory.AUTH,
        code=ErrorCode.CODEX_NOT_LOGGED_IN,
        retryable=False,
    )
    source = _source(tmp_path)
    with pytest.raises(RuntimeError):
        service.start_translation(StartTranslationCommand(source_path=source))
    job = _load_failed_job(service, source)
    assert job.pipeline_meta["part_resume_supported"] is False
    assert job.pipeline_meta["backend"] == "python-internal"
    assert job.pipeline_meta["babeldoc_version"] == "0.6.4"
    assert "note" in job.pipeline_meta

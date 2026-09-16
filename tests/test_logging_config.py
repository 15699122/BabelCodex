from pathlib import Path

from codex_babeldoc.core.config import LoggingConfig
from codex_babeldoc.core.logging_config import (
    configure_logging,
    redact_log_text,
    release_file_handlers,
)


def test_logging_levels_and_silent_mode(tmp_path: Path):
    path = configure_logging(tmp_path, LoggingConfig(level="debug", max_files=5), stream=False)
    assert path is not None and path.is_file()
    release_file_handlers()
    assert (
        configure_logging(tmp_path, LoggingConfig(level="silent", max_files=5), stream=False)
        is None
    )
    release_file_handlers()


def test_logging_prunes_old_files_before_creating_new_session(tmp_path: Path):
    for index in range(5):
        old = tmp_path / f"old-{index}.log"
        old.write_text(str(index), encoding="utf-8")
        old.touch()
    path = configure_logging(tmp_path, LoggingConfig(level="info", max_files=3), stream=False)
    assert path is not None
    release_file_handlers()
    assert len(list(tmp_path.glob("*.log"))) <= 3


def test_log_diagnostics_redact_credential_like_values():
    text = "authorization=Bearer secret-token api_key: abc123 ordinary=ok"
    redacted = redact_log_text(text)
    assert "secret-token" not in redacted
    assert "abc123" not in redacted
    assert "ordinary=ok" in redacted

from codex_babeldoc.core.artifacts import Artifact, ArtifactType
from codex_babeldoc.core.errors import (
    BabelCodexError,
    ErrorCategory,
    ErrorCode,
    classify_exception,
)
from codex_babeldoc.core.state import JobStage, JobStatus, StateStore, job_id_for


def test_job_state_v2_roundtrip(tmp_path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-test")
    store = StateStore(tmp_path / "state")
    job = store.load(pdf, config_fingerprint="cfg1")
    job.status = JobStatus.RUNNING
    job.stage = JobStage.TRANSLATING
    job.translator_name = "mock"
    job.backend_name = "python-internal"
    job.artifacts = [
        Artifact(
            artifact_type=ArtifactType.MONO_PDF,
            path=str(tmp_path / "mono.pdf"),
            size=10,
            validated=True,
        )
    ]
    store.save(job)
    again = store.load(pdf, config_fingerprint="cfg1")
    assert again.schema_version == 2
    assert again.job_id == job.job_id
    assert again.status is JobStatus.RUNNING
    assert again.stage is JobStage.TRANSLATING
    assert again.translator_name == "mock"
    assert again.config_fingerprint == "cfg1"
    assert again.artifacts[0].artifact_type is ArtifactType.MONO_PDF


def test_legacy_state_json_migrates(tmp_path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-test")
    from codex_babeldoc.core.state import file_fingerprint

    source_fp = file_fingerprint(pdf)
    legacy = {
        "source": str(pdf),
        "fingerprint": source_fp,
        "status": "completed",
        "attempts": 2,
        "last_error": None,
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    import json

    store = StateStore(tmp_path / "state")
    legacy_path = store.root / f"{source_fp}.json"
    legacy_path.write_text(json.dumps(legacy), encoding="utf-8")

    migrated = store.load(pdf, config_fingerprint="cfg2")
    assert migrated.status is JobStatus.COMPLETED
    assert migrated.stage is JobStage.COMPLETED
    assert migrated.config_fingerprint == "cfg2"
    assert migrated.attempts == 2


def test_job_id_depends_on_config_fingerprint():
    assert job_id_for("abc", "cfg1") != job_id_for("abc", "cfg2")
    assert len(job_id_for("abc", "cfg1")) == 64


def test_classify_known_and_unknown_exceptions():
    known = BabelCodexError(
        category=ErrorCategory.AUTH,
        code=ErrorCode.CODEX_NOT_LOGGED_IN,
        safe_message="Not logged in.",
        retryable=False,
    )
    assert classify_exception(known) is known

    missing = classify_exception(FileNotFoundError("nope"))
    assert missing.code is ErrorCode.INPUT_NOT_FOUND
    assert missing.category is ErrorCategory.INPUT

    unknown = classify_exception(RuntimeError("boom"))
    assert unknown.code is ErrorCode.UNKNOWN
    assert unknown.category is ErrorCategory.UNKNOWN


def test_config_fingerprint_stable_and_sensitive_to_change():
    from pathlib import Path as P

    from codex_babeldoc.core.config import (
        AppConfig,
        BabelDocConfig,
        TranslationConfig,
    )

    a = AppConfig(root=P("."))
    b = AppConfig(root=P("."))
    assert a.fingerprint() == b.fingerprint()

    c = AppConfig(
        root=P("."),
        translation=TranslationConfig(lang_out="en"),
    )
    assert a.fingerprint() != c.fingerprint()

    d = AppConfig(
        root=P("."),
        babeldoc=BabelDocConfig(working_dir=P("/different/path")),
    )
    # working_dir must be excluded from the fingerprint.
    assert a.fingerprint() == d.fingerprint()


def test_atomic_save_no_tmp_left_and_file_is_json(tmp_path):
    from json import JSONDecodeError, loads

    pdf = tmp_path / "y.pdf"
    pdf.write_bytes(b"%PDF")
    store = StateStore(tmp_path / "state")
    job = store.load(pdf, config_fingerprint="f")
    job.status = JobStatus.COMPLETED
    store.save(job)

    leftovers = list(store.root.glob("*.tmp"))
    assert leftovers == []

    for path in store.root.glob("*.json"):
        try:
            loads(path.read_text(encoding="utf-8"))
        except JSONDecodeError as exc:
            raise AssertionError(f"{path} is not valid JSON: {exc}")


def test_list_jobs_skips_corrupt_state(tmp_path):
    pdf = tmp_path / "z.pdf"
    pdf.write_bytes(b"%PDF")
    store = StateStore(tmp_path / "state")
    job = store.load(pdf, config_fingerprint="f")
    store.save(job)

    bad = (
        store.root
        / "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff.json"
    )
    bad.write_text("{ not json", encoding="utf-8")

    jobs = store.list_jobs()
    assert all(j.job_id == job.job_id for j in jobs)

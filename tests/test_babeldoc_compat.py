"""Tests for the BabelDOC 0.6.x compatibility layer (no BabelDOC runtime needed)."""

from pathlib import Path

import pytest

from codex_babeldoc.backends import babeldoc_v064 as v064
from codex_babeldoc.backends.babeldoc_internal import BabelDocInternalBackend
from codex_babeldoc.core.errors import BabelCodexError, ErrorCode


class TestVersionDetection:
    def test_is_supported_version_table(self) -> None:
        assert v064.is_supported_version("0.6.4") is True
        assert v064.is_supported_version("0.6.13") is True
        assert v064.is_supported_version("0.7.0") is False
        assert v064.is_supported_version("1.0.0") is False
        assert v064.is_supported_version("") is False
        assert v064.is_supported_version(None) is False
        assert v064.is_supported_version("garbage") is False

    def test_assert_supported_returns_version(self) -> None:
        assert v064.assert_supported("0.6.4") == "0.6.4"

    def test_assert_supported_none(self) -> None:
        with pytest.raises(BabelCodexError) as excinfo:
            v064.assert_supported(None)
        assert excinfo.value.code is ErrorCode.BABELDOC_NOT_INSTALLED

    def test_assert_supported_unsupported(self) -> None:
        with pytest.raises(BabelCodexError) as excinfo:
            v064.assert_supported("0.7.0")
        assert excinfo.value.code is ErrorCode.BABELDOC_VERSION_UNSUPPORTED

    def test_backend_availability_reflects_detection(self, monkeypatch) -> None:
        backend = v064.BabelDocV064Backend()
        monkeypatch.setattr(v064, "detect_version", lambda: "0.6.4")
        assert backend.is_available() is True
        assert backend.version == "0.6.4"
        monkeypatch.setattr(v064, "detect_version", lambda: None)
        assert backend.is_available() is False
        assert backend.version == "unavailable"


class TestWatermarkMapping:
    @pytest.mark.parametrize(
        ("mode", "expected"),
        [
            ("watermarked", "Watermarked"),
            ("no_watermark", "NoWatermark"),
            ("both", "Both"),
        ],
    )
    def test_known_modes(self, mode: str, expected: str) -> None:
        assert v064.normalize_watermark_mode(mode) == expected

    def test_unknown_mode(self) -> None:
        with pytest.raises(BabelCodexError) as excinfo:
            v064.normalize_watermark_mode("fancy")
        assert excinfo.value.code is ErrorCode.CONFIG_INVALID


class TestProgressConversion:
    def test_ignores_finish_and_error(self) -> None:
        assert v064.convert_progress({"type": "finish"}) is None
        assert v064.convert_progress({"type": "error"}) is None

    def test_converts_stage_progress(self) -> None:
        event = v064.convert_progress(
            {
                "type": "progress_update",
                "stage": "translate",
                "stage_current": 12,
                "stage_total": 50,
                "overall_progress": 0.42,
                "message": "working",
            }
        )
        assert event is not None
        assert event.stage == "translate"
        assert event.stage_current == 12
        assert event.stage_total == 50
        assert event.overall_progress == pytest.approx(0.42)
        assert event.message == "working"

    def test_missing_fields_default_to_none(self) -> None:
        event = v064.convert_progress({})
        assert event is not None
        assert event.stage == "unknown"
        assert event.stage_current is None
        assert event.stage_total is None
        assert event.overall_progress is None
        assert event.message is None


class TestArtifactsFromResult:
    def test_extracts_existing_files(self, tmp_path: Path) -> None:
        mono = tmp_path / "mono.pdf"
        dual = tmp_path / "dual.pdf"
        mono.write_bytes(b"mono")
        dual.write_bytes(b"dual-pdf-bytes")

        class FakeResult:
            mono_pdf_path = mono
            dual_pdf_path = dual

        artifacts = v064.artifacts_from_result(FakeResult())
        assert [a.artifact_type.value for a in artifacts] == ["mono_pdf", "dual_pdf"]
        assert artifacts[0].size == 4
        assert artifacts[1].size == 14

    def test_skips_missing_paths(self) -> None:
        class FakeResult:
            mono_pdf_path = None
            dual_pdf_path = None

        assert v064.artifacts_from_result(FakeResult()) == []

    def test_keeps_missing_file_with_zero_size(self, tmp_path: Path) -> None:
        class FakeResult:
            mono_pdf_path = tmp_path / "does-not-exist.pdf"
            dual_pdf_path = None

        artifacts = v064.artifacts_from_result(FakeResult())
        assert len(artifacts) == 1
        assert artifacts[0].size == 0


class TestLegacyFacade:
    def test_facade_maps_kwargs_to_request(self, tmp_path: Path, monkeypatch) -> None:
        captured: dict = {}

        class FakeBackend:
            name = "babeldoc"
            version = "0.6.4"

            def translate(self, request, translator_factory):
                captured["request"] = request
                captured["factory"] = translator_factory

                class Raw:
                    mono_pdf_path = None
                    dual_pdf_path = None
                    glossary = None

                raw = Raw()
                return v064.PdfTranslateResult(
                    job_id=request.job_id,
                    backend_name="babeldoc",
                    backend_version="0.6.4",
                    raw=raw,
                )

        monkeypatch.setattr(
            "codex_babeldoc.backends.babeldoc_internal.BabelDocV064Backend",
            FakeBackend,
        )
        facade = BabelDocInternalBackend()

        def factory() -> object:
            return object()

        raw = facade.translate(
            tmp_path / "input.pdf",
            tmp_path / "out",
            lang_in="en",
            lang_out="zh",
            translator_factory=factory,
            no_mono=False,
            no_dual=True,
            qps=2,
            min_text_length=7,
            working_dir=tmp_path / "work",
            watermark_output_mode="both",
            auto_extract_glossary=True,
            ocr_workaround=True,
            auto_enable_ocr_workaround=False,
            enhance_compatibility=False,
            translate_table_text=True,
        )
        assert raw is not None
        request = captured["request"]
        assert request.produce_mono is True
        assert request.produce_dual is False
        assert request.qps == 2
        assert request.min_text_length == 7
        assert request.watermark_output_mode == "both"
        assert request.auto_extract_glossary is True
        assert request.ocr_workaround is True
        assert request.auto_enable_ocr_workaround is False
        assert request.enhance_compatibility is False
        assert request.translate_table_text is True
        assert captured["factory"] is factory

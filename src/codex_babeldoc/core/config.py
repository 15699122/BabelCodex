from __future__ import annotations

import json
import tomllib
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from pathlib import Path


@dataclass(slots=True)
class ProjectConfig:
    input_dir: Path = Path("incoming")
    output_dir: Path = Path("translated")
    state_dir: Path = Path("state")
    log_dir: Path = Path("logs")


@dataclass(slots=True)
class TranslationConfig:
    lang_in: str = "en"
    lang_out: str = "zh"
    translator: str = "codex-sdk"
    model: str = ""
    effort: str = "low"
    qps: int = 1
    min_text_length: int = 5
    no_mono: bool = False
    no_dual: bool = False
    watermark_output_mode: str = "no_watermark"
    auto_extract_glossary: bool = False
    max_retries: int = 3


@dataclass(slots=True)
class BabelDocConfig:
    backend: str = "python-internal"
    working_dir: Path = Path("state/babeldoc-work")
    translate_table_text: bool = False
    ocr_workaround: bool = False
    auto_enable_ocr_workaround: bool = True
    enhance_compatibility: bool = True


@dataclass(slots=True)
class CodexConfig:
    thread_mode: str = "per-document"
    sandbox: str = "read_only"
    strict_output: bool = True
    context_prompt: str = (
        "Translate faithfully and preserve terminology. Do not explain the translation."
    )


@dataclass(slots=True)
class AppConfig:
    root: Path
    project: ProjectConfig = field(default_factory=ProjectConfig)
    translation: TranslationConfig = field(default_factory=TranslationConfig)
    babeldoc: BabelDocConfig = field(default_factory=BabelDocConfig)
    codex: CodexConfig = field(default_factory=CodexConfig)

    def resolve_paths(self) -> None:
        for obj, names in [
            (self.project, ("input_dir", "output_dir", "state_dir", "log_dir")),
            (self.babeldoc, ("working_dir",)),
        ]:
            for name in names:
                value = getattr(obj, name)
                if not value.is_absolute():
                    setattr(obj, name, self.root / value)

    def ensure_dirs(self) -> None:
        for path in (
            self.project.input_dir,
            self.project.output_dir,
            self.project.state_dir,
            self.project.log_dir,
            self.babeldoc.working_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def fingerprint(self) -> str:
        """Hash translation-affecting configuration without machine-specific paths."""
        values = {
            "translation": asdict(self.translation),
            "babeldoc": {
                key: value for key, value in asdict(self.babeldoc).items() if key != "working_dir"
            },
            "codex": asdict(self.codex),
        }
        payload = json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()


def _construct(cls, values: dict):
    return cls(**values)


def load_config(path: str | Path) -> AppConfig:
    path = Path(path).resolve()
    with path.open("rb") as f:
        raw = tomllib.load(f)
    cfg = AppConfig(
        root=path.parent.parent if path.parent.name == "config" else path.parent,
        project=_construct(ProjectConfig, raw.get("project", {})),
        translation=_construct(TranslationConfig, raw.get("translation", {})),
        babeldoc=_construct(BabelDocConfig, raw.get("babeldoc", {})),
        codex=_construct(CodexConfig, raw.get("codex", {})),
    )
    # Dataclass accepts strings for Path annotations; normalize them here.
    for obj, names in [
        (cfg.project, ("input_dir", "output_dir", "state_dir", "log_dir")),
        (cfg.babeldoc, ("working_dir",)),
    ]:
        for name in names:
            setattr(obj, name, Path(getattr(obj, name)))
    cfg.resolve_paths()
    return cfg

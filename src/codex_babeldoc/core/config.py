"""YAML configuration and portable runtime path model.

Relative paths are resolved against the portable root supplied by the config
file, never against the process current working directory.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from codex_babeldoc.core.private_data import ensure_private_dir

CONFIG_SCHEMA_VERSION = 1
DEFAULT_CONFIG_NAME = "config.yaml"
SUPPORTED_LOG_LEVELS = ("error", "warning", "info", "debug", "silent")


@dataclass(slots=True)
class ProjectConfig:
    input_dir: Path = Path("cache/incoming")
    output_dir: Path = Path("output")
    state_dir: Path = Path("cache/state")
    log_dir: Path = Path("logs")
    glossary_dir: Path = Path("config/glossary")
    context_dir: Path = Path("config/context")
    cache_dir: Path = Path("cache")
    resource_dir: Path = Path("resource")


@dataclass(slots=True)
class LoggingConfig:
    level: str = "info"
    max_files: int = 5

    def validate(self) -> None:
        if self.level not in SUPPORTED_LOG_LEVELS:
            raise ValueError(f"unsupported log level: {self.level}")
        if self.max_files < 1:
            raise ValueError("logging.max_files must be at least 1")


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
    retry_policy: dict[str, int] = field(default_factory=dict)
    cache_enabled: bool = True
    cache_store_plaintext: bool = False
    cache_ttl_seconds: int | None = None


@dataclass(slots=True)
class BabelDocConfig:
    backend: str = "python-internal"
    working_dir: Path = Path("cache/work")
    cache_dir: Path = Path("cache/babeldoc")
    resource_dir: Path = Path("resource/babeldoc")
    worker_mode: str = "subprocess"
    translate_table_text: bool = False
    ocr_workaround: bool = False
    auto_enable_ocr_workaround: bool = True
    enhance_compatibility: bool = True
    work_retention_days: int = 7


@dataclass(slots=True)
class CodexConfig:
    thread_mode: str = "per-document"
    sandbox: str = "read_only"
    strict_output: bool = True
    context_prompt: str = (
        "Translate faithfully and preserve terminology. Do not explain the translation."
    )
    context_max_chars: int = 4000
    max_turns_before_compact: int = 0


@dataclass(slots=True)
class AppConfig:
    root: Path
    config_path: Path | None = field(default=None, repr=False, compare=False)
    schema_version: int = CONFIG_SCHEMA_VERSION
    project: ProjectConfig = field(default_factory=ProjectConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    translation: TranslationConfig = field(default_factory=TranslationConfig)
    babeldoc: BabelDocConfig = field(default_factory=BabelDocConfig)
    codex: CodexConfig = field(default_factory=CodexConfig)

    def resolve_paths(self) -> None:
        for obj, names in [
            (
                self.project,
                (
                    "input_dir",
                    "output_dir",
                    "state_dir",
                    "log_dir",
                    "glossary_dir",
                    "context_dir",
                    "cache_dir",
                    "resource_dir",
                ),
            ),
            (self.babeldoc, ("working_dir", "cache_dir", "resource_dir")),
        ]:
            for name in names:
                value = Path(getattr(obj, name))
                if not value.is_absolute():
                    value = self.root / value
                setattr(obj, name, value)

    def ensure_dirs(self, *, include_output: bool = True) -> None:
        paths = [
            self.project.input_dir,
            self.project.state_dir,
            self.project.log_dir,
            self.project.glossary_dir,
            self.project.context_dir,
            self.project.cache_dir,
            self.babeldoc.working_dir,
            self.babeldoc.cache_dir,
        ]
        if include_output:
            paths.append(self.project.output_dir)
        private = {
            self.project.state_dir,
            self.project.log_dir,
            self.project.glossary_dir,
            self.project.context_dir,
            self.project.cache_dir,
            self.babeldoc.working_dir,
            self.babeldoc.cache_dir,
        }
        for path in paths:
            if path in private:
                ensure_private_dir(path)
            else:
                path.mkdir(parents=True, exist_ok=True)

    def fingerprint(self) -> str:
        """Hash translation-affecting configuration without machine-specific paths."""
        translation_values = asdict(self.translation)
        translation_values.pop("retry_policy", None)
        values = {
            "translation": translation_values,
            "babeldoc": {
                key: value
                for key, value in asdict(self.babeldoc).items()
                if key not in ("working_dir", "cache_dir", "resource_dir", "work_retention_days")
            },
            "codex": asdict(self.codex),
        }
        payload = json.dumps(
            values, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
        )
        return sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        def normalize(value: Any) -> Any:
            if isinstance(value, Path):
                try:
                    return value.relative_to(self.root).as_posix()
                except ValueError:
                    return str(value)
            if isinstance(value, dict):
                return {str(k): normalize(v) for k, v in value.items()}
            if isinstance(value, list):
                return [normalize(v) for v in value]
            return value

        values = asdict(self)
        values.pop("root", None)
        values.pop("config_path", None)
        return normalize(values)


def _mapping(raw: Any, name: str) -> dict[str, Any]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise TypeError(f"configuration section {name!r} must be a mapping")
    return raw


def _construct(cls: type[Any], values: Any) -> Any:
    return cls(**_mapping(values, cls.__name__))


def load_config(path: str | Path) -> AppConfig:
    """Load YAML configuration; TOML input is deliberately rejected."""
    path = Path(path).resolve()
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError(f"configuration must be YAML (.yaml/.yml): {path.name}")
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency resolution gate
        raise RuntimeError("PyYAML is required to load BabelCodex configuration") from exc
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise TypeError("configuration root must be a mapping")
    schema_version = int(raw.get("schema_version", CONFIG_SCHEMA_VERSION))
    if schema_version != CONFIG_SCHEMA_VERSION:
        raise ValueError(f"unsupported configuration schema version: {schema_version}")
    root = path.parent.parent if path.parent.name == "config" else path.parent
    config = AppConfig(
        root=root,
        config_path=path,
        schema_version=schema_version,
        project=_construct(ProjectConfig, raw.get("project")),
        logging=_construct(LoggingConfig, raw.get("logging")),
        translation=_construct(TranslationConfig, raw.get("translation")),
        babeldoc=_construct(BabelDocConfig, raw.get("babeldoc")),
        codex=_construct(CodexConfig, raw.get("codex")),
    )
    config.resolve_paths()
    config.logging.validate()
    return config


def save_config(config: AppConfig, path: str | Path | None = None) -> Path:
    """Atomically save YAML configuration and retain a single backup."""
    import yaml

    target = (
        Path(path).resolve()
        if path is not None
        else config.config_path or config.root / "config" / DEFAULT_CONFIG_NAME
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    config.logging.validate()
    payload = yaml.safe_dump(config.to_dict(), allow_unicode=True, sort_keys=False)
    backup = target.with_suffix(target.suffix + ".bak")
    if target.exists():
        os.replace(target, backup)
    with NamedTemporaryFile(
        "w", encoding="utf-8", dir=target.parent, prefix=".config-", suffix=".tmp", delete=False
    ) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    try:
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def load_or_create_config(path: str | Path) -> AppConfig:
    """Load an existing YAML file or create the default portable configuration."""
    target = Path(path).resolve()
    if target.exists():
        return load_config(target)
    root = target.parent.parent if target.parent.name == "config" else target.parent
    config = AppConfig(root=root)
    config.config_path = target
    config.resolve_paths()
    save_config(config, target)
    return config

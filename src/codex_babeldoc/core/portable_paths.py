"""Portable Windows directory layout helpers.

The resolver is platform-neutral so Linux can validate the layout without
pretending to validate native Windows shell or known-folder behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PortableLayout:
    """Fixed writable/read-only directories relative to a portable root."""

    root: Path

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def cache(self) -> Path:
        return self.root / "cache"

    @property
    def incoming(self) -> Path:
        return self.cache / "incoming"

    @property
    def state(self) -> Path:
        return self.cache / "state"

    @property
    def babeldoc_cache(self) -> Path:
        return self.cache / "babeldoc"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def output(self) -> Path:
        return self.root / "output"

    @property
    def resource(self) -> Path:
        return self.root / "resource"

    def relative_paths(self) -> dict[str, str]:
        return {
            name: path.relative_to(self.root).as_posix()
            for name, path in {
                "root": self.root,
                "config": self.config,
                "cache": self.cache,
                "incoming": self.incoming,
                "state": self.state,
                "babeldoc_cache": self.babeldoc_cache,
                "logs": self.logs,
                "output": self.output,
                "resource": self.resource,
            }.items()
        }


def resolve_portable_root(config_path: str | Path) -> Path:
    """Resolve a config file to its portable application root."""
    path = Path(config_path).resolve()
    return path.parent.parent if path.parent.name == "config" else path.parent


def portable_layout(config_path: str | Path) -> PortableLayout:
    """Build the fixed layout associated with a YAML config file."""
    return PortableLayout(resolve_portable_root(config_path))

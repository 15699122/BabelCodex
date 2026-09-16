"""Regression guard for the GUI Tauri capability flavor boundary.

Background
----------
Windows WDIO revalidation (WVQ-017) exposed that running the E2E/MCP
prepare step left a generated ``e2e.json`` / ``mcp-debug.json`` in
``gui/src-tauri/capabilities/``. Tauri's build script validates *every*
file in that directory against the compiled ACL manifests, so a stale
flavor capability referencing ``wdio:default`` / ``mcp-bridge:default``
broke unrelated ``cargo check`` invocations (default and ``mcp-dev``).

Fix in ``dev``: flavor capabilities are now *inlined* as
``CapabilityEntry::Inlined`` objects directly inside ``tauri.e2e.conf.json``
and ``tauri.mcp.conf.json`` via the ``--config`` merge, and the
``prepare-e2e-rust.mjs`` capability-generation step was removed. This
test asserts that boundary so it can never silently regress.

These are pure file-inspection checks: no Tauri binary is built or run,
and the test is not marked ``integration``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GUI = REPO / "gui"
ST = GUI / "src-tauri"
CAPS = ST / "capabilities"

# Permissions that may only live behind a Cargo feature gate. If they ever
# appear in a committed capability file in the shared directory, a default
# cargo check on a machine without that feature will fail.
FORBIDDEN_IN_COMMITTED_CAPS = ("wdio:", "mcp-bridge:", "wdio-webdriver:")

# The mutual-exclusion compile_error! that keeps the two dev control planes
# apart in the same binary.
MUTUAL_EXCLUSION_RE = re.compile(
    r'#\[cfg\(all\(feature\s*=\s*"mcp-dev",\s*feature\s*=\s*"e2e"\)\)\]\n'
    r'\s*compile_error!\("features `mcp-dev` and `e2e` are mutually exclusive"\);'
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def test_shared_capabilities_directory_contains_only_default() -> None:
    """No flavor capability file is ever generated into the shared dir."""
    assert CAPS.exists(), CAPS
    names = sorted(p.name for p in CAPS.glob("*.json"))
    assert names == ["default.json"], f"unexpected committed capability files: {names}"


def test_default_capability_has_no_flavor_permissions() -> None:
    """The production main capability must not reference wdio/mcp permissions."""
    default = _load(CAPS / "default.json")
    blob = json.dumps(default)
    for forbidden in FORBIDDEN_IN_COMMITTED_CAPS:
        assert forbidden not in blob, f"default.json references {forbidden!r}"
    assert default["identifier"] == "main-capability"


def _inline_cap(config_path: Path) -> dict:
    caps = _load(config_path)["app"]["security"]["capabilities"]
    inlines = [c for c in caps if isinstance(c, dict)]
    # Exactly the flavor capability plus a reference to main-capability.
    refs = [c for c in caps if isinstance(c, str)]
    assert refs == ["main-capability"], (config_path, refs)
    assert len(inlines) == 1, (config_path, inlines)
    return inlines[0]


def test_e2e_flavor_capability_is_inlined_and_allowlisted() -> None:
    """The E2E capability is inlined in the flavor config, not a file on disk."""
    cap = _load(ST / "tauri.e2e.conf.json")["app"]["security"]["capabilities"]
    identifiers = {c["identifier"] for c in cap if isinstance(c, dict)}
    assert "e2e-capability" in identifiers

    inline = _inline_cap(ST / "tauri.e2e.conf.json")
    assert inline["identifier"] == "e2e-capability"
    perms = json.dumps(inline["permissions"])
    assert "wdio:default" in perms
    assert "wdio-webdriver:default" in perms

    # The sidecar config allowlist must point only at the E2E config so the
    # production config.yaml can never be launched by the test binary.
    spawn = next(
        p
        for p in inline["permissions"]
        if isinstance(p, dict) and p.get("identifier") == "shell:allow-spawn"
    )
    validators = []
    for rule in spawn["allow"]:
        for arg in rule.get("args", []):
            if isinstance(arg, dict) and "validator" in arg:
                validators.append(arg["validator"])
    assert validators == [r"\.\./config/e2e\.yaml"], validators
    assert not (CAPS / "e2e.json").exists()


def test_mcp_flavor_capability_is_inlined() -> None:
    inline = _inline_cap(ST / "tauri.mcp.conf.json")
    assert inline["identifier"] == "mcp-debug-capability"
    perms = json.dumps(inline["permissions"])
    assert "mcp-bridge:default" in perms
    assert not (CAPS / "mcp-debug.json").exists()


def test_package_json_scripts_no_longer_generate_capability_files() -> None:
    """No npm script may reference the removed capability-generation step."""
    pkg = _load(GUI / "package.json")
    scripts = pkg["scripts"]
    for name, body in scripts.items():
        assert "prepare-e2e-rust" not in body, (name, body)
        assert "BABELCODEX_TAURI_FLAVOR" not in body, (name, body)
    # mcp:prepare was removed because capability injection is gone.
    assert "mcp:prepare" not in scripts
    assert "tauri:prepare" not in scripts


def test_mcp_dev_and_e2e_features_remain_mutually_exclusive() -> None:
    """The compile-time guard that forbids both dev control planes is intact."""
    lib = (ST / "src" / "lib.rs").read_text()
    assert MUTUAL_EXCLUSION_RE.search(lib), "mutual-exclusion compile_error! missing"
    carg = (ST / "Cargo.toml").read_text()
    assert 'mcp-dev = ["dep:tauri-plugin-mcp-bridge"]' in carg
    assert "tauri-plugin-wdio" in carg


def test_gitignore_does_not_list_generated_flavor_capabilities() -> None:
    """Stale ignore rules for generated files must not linger."""
    lines = (REPO / ".gitignore").read_text().splitlines()
    offenders = [
        ln
        for ln in lines
        if ln.strip()
        in {"gui/src-tauri/capabilities/e2e.json", "gui/src-tauri/capabilities/mcp-debug.json"}
    ]
    assert not offenders, f"stale gitignore entries: {offenders}"

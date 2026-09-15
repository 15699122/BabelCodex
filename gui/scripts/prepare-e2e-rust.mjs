// Prepare the Rust-side capabilities directory for a specific build flavor.
//
// Tauri's build script validates every file in the capabilities directory, and
// each test capability references permissions from its own optional plugin
// (wdio:default, mcp-bridge:default). If those files are present in
// src-tauri/capabilities/ while the corresponding Cargo feature is disabled,
// the build fails.
//
// To keep the directory clean, we keep template capabilities in
// scripts/capabilities/ and copy only the ones required for the current flavor
// into src-tauri/capabilities/ before the build.

import { copyFile, rm, mkdir, access, constants } from "node:fs/promises";
import { resolve, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const repoRoot = resolve(__dirname, "..");
const capabilitiesDir = join(repoRoot, "src-tauri", "capabilities");
const templatesDir = join(__dirname, "capabilities");

const FLAVORS = {
  default: [],
  "mcp-dev": ["mcp-debug"],
  e2e: ["e2e"],
};

const fileExists = async (target) => {
  try {
    await access(target, constants.F_OK);
    return true;
  } catch {
    return false;
  }
};

const main = async () => {
  const flavor = process.env.BABELCODEX_TAURI_FLAVOR ?? "default";
  const extra = FLAVORS[flavor];
  if (!extra) {
    throw new Error(`unknown Tauri flavor: ${flavor}`);
  }

  // Remove any flavor-specific capabilities from previous runs. This makes
  // switching between default, MCP, and E2E builds deterministic on both
  // Linux shells and Windows PowerShell/cmd invocations.
  for (const name of Object.values(FLAVORS).flat()) {
    const target = join(capabilitiesDir, `${name}.json`);
    if (await fileExists(target)) {
      await rm(target);
    }
  }
  await mkdir(capabilitiesDir, { recursive: true });

  // Add the capabilities required by the active flavor.
  for (const name of extra) {
    const source = join(templatesDir, `${name}.json`);
    const target = join(capabilitiesDir, `${name}.json`);
    if (!(await fileExists(source))) {
      throw new Error(`missing capability template: ${source}`);
    }
    await copyFile(source, target);
  }
};

main().catch((error) => {
  console.error(`[prepare-e2e-rust] ${error.message}`);
  process.exit(1);
});

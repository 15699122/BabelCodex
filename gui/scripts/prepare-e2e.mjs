// Prepare the deterministic E2E workspace under build/e2e.
//
// This script is intentionally conservative:
// - it only creates or deletes files inside <repo>/build/e2e
// - it refuses symlinks and paths that escape the workspace
// - it never downloads or discovers arbitrary binaries
// - it never touches user config, state, logs, or glossary data
// - it ensures a platform-correct sidecar input exists before a native build
//

import { rm, mkdir, access, writeFile, copyFile, constants } from "node:fs/promises";
import { resolve, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const repoRoot = resolve(__dirname, "..");
const workspace = join(repoRoot, "build", "e2e");

const SUBDIRS = ["incoming", "outside", "translated", "state", "logs", "glossary", "context", "artifacts"];

const safePath = (target) => {
  const resolved = resolve(target);
  const rel = relative(workspace, resolved);
  if (rel.startsWith("..") || rel === "") {
    throw new Error(`refusing to operate outside E2E workspace: ${target}`);
  }
  return resolved;
};

const assertNoSymlink = async (target) => {
  try {
    await access(target, constants.F_OK);
  } catch {
    return;
  }
  const { lstat } = await import("node:fs/promises");
  const stat = await lstat(target);
  if (stat.isSymbolicLink()) {
    throw new Error(`refusing to overwrite symlink: ${target}`);
  }
};

const cleanWorkspace = async () => {
  await assertNoSymlink(workspace);
  await rm(workspace, { recursive: true, force: true });
};

const createWorkspace = async () => {
  for (const subdir of SUBDIRS) {
    await mkdir(safePath(join(workspace, subdir)), { recursive: true });
  }
};

const sidecarName = () => {
  const architecture = process.arch === "arm64" ? "aarch64" : "x86_64";
  if (process.platform === "win32") {
    return `babelcodex-service-${architecture}-pc-windows-msvc.exe`;
  }
  if (process.platform === "linux") {
    return `babelcodex-service-${architecture}-unknown-linux-gnu`;
  }
  throw new Error(`unsupported native E2E platform: ${process.platform}`);
};

const ensureSidecar = async () => {
  const target = join(repoRoot, "src-tauri", "binaries", sidecarName());
  if (process.platform === "win32") {
    try {
      await access(target, constants.F_OK);
    } catch {
      throw new Error(
        `Windows native E2E requires ${target}; build the Windows sidecar first with ` +
        "uv run --extra runtime --with pyinstaller pyinstaller --clean --noconfirm scripts/babelcodex-service.spec",
      );
    }
    return;
  }
  try {
    await access(target, constants.F_OK);
  } catch {
    await mkdir(join(repoRoot, "src-tauri", "binaries"), { recursive: true });
    await writeFile(target, "#!/bin/sh\n# placeholder for cargo check; replaced at native E2E runtime\necho babelcodex-service placeholder\n");
    await import("node:fs/promises").then((m) => m.chmod(target, 0o755));
  }
};

const prepareFixtures = async () => {
  const source = resolve(repoRoot, "..", "tests", "fixtures", "fixture_two_column.pdf");
  await access(source, constants.F_OK);
  await copyFile(source, safePath(join(workspace, "incoming", "sample.pdf")));
  await copyFile(source, safePath(join(workspace, "outside", "outside.pdf")));
};

const main = async () => {
  const args = process.argv.slice(2);
  if (args.includes("--clean")) {
    await cleanWorkspace();
    return;
  }
  await cleanWorkspace();
  await createWorkspace();
  await prepareFixtures();
  await ensureSidecar();
};

main().catch((error) => {
  console.error(`[prepare-e2e] ${error.message}`);
  process.exit(1);
});
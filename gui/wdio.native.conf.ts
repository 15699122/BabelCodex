// WebdriverIO native embedded mode: drive the real Tauri WebView through the
// embedded WebDriver server provided by tauri-plugin-wdio-webdriver.
//
// This exercises the actual Tauri host, plugin-shell, the Python sidecar
// lifecycle, and the JSONL handshake. It requires:
//   - a desktop session (DISPLAY/WAYLAND_DISPLAY)
//   - npm run e2e:build (which produces the e2e-feature binary)
//   - the fixed Python sidecar resolved from the repository root

import path from "node:path";
import { fileURLToPath } from "node:url";
import { sharedConfig } from "./wdio.shared.conf.js";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

process.env.BABELCODEX_E2E_MODE = "native";

const binaryName =
  process.platform === "win32" ? "babelcodex-gui.exe" : "babelcodex-gui";

const appBinaryPath = path.resolve(
  __dirname,
  "src-tauri",
  "target",
  "debug",
  binaryName,
);

const commonSpecs = path.join(
  __dirname,
  "tests",
  "e2e",
  "native",
  "**",
  "*.spec.ts",
);

const windowsSpecs = path.join(
  __dirname,
  "tests",
  "e2e",
  "windows",
  "**",
  "*.spec.ts",
);

export const config = {
  ...sharedConfig,

  specs: process.platform === "win32"
    ? [commonSpecs, windowsSpecs]
    : [commonSpecs],

  services: [
    [
      "@wdio/tauri-service",
      {
        driverProvider: "embedded",
        appBinaryPath,
        captureFrontendLogs: true,
        captureBackendLogs: true,
        waitForIPC: true,
        idleTimeout: 30,
      },
    ],
  ],

  capabilities: [
    {
      browserName: "tauri",
      "tauri:options": {
        application: appBinaryPath,
        arguments: [],
      },
      "wdio:enforceWebDriverTimeout": true,
    },
  ],

  beforeSession: function (_capabilities, _specs, _browser) {
    if (process.env.VITE_E2E !== "1") {
      throw new Error(
        "VITE_E2E=1 is required for native mode; run npm run e2e:build first",
      );
    }
  },

  before: async function () {
    // Windows has a native desktop without DISPLAY/WAYLAND_DISPLAY. Linux
    // needs an explicitly targetable X11 or Wayland session.
    if (process.platform === "win32") return;
    const display = process.env.DISPLAY ?? process.env.WAYLAND_DISPLAY;
    if (!display) {
      throw new Error(
        "No DISPLAY or WAYLAND_DISPLAY found; native E2E needs a targetable desktop",
      );
    }
  },
};

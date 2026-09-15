// WebdriverIO external provider mode: diagnostic fallback only.
//
// The embedded provider is the default acceptance path. This config is used
// when the embedded driver hangs or fails in a way that points at the driver
// layer itself. On Windows it relies on the service to manage the Edge
// WebDriver; on Linux it requires a separately installed WebKitWebDriver.

import path from "node:path";
import { fileURLToPath } from "node:url";
import { sharedConfig } from "./wdio.shared.conf.js";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

process.env.BABELCODEX_E2E_MODE = "external";

const binaryName =
  process.platform === "win32" ? "babelcodex-gui.exe" : "babelcodex-gui";

const appBinaryPath = path.resolve(
  __dirname,
  "src-tauri",
  "target",
  "debug",
  binaryName,
);

export const config = {
  ...sharedConfig,

  specs: [path.join(__dirname, "tests", "e2e", "native", "smoke.spec.ts")],

  services: [
    [
      "@wdio/tauri-service",
      {
        driverProvider: "external",
        appBinaryPath,
        captureFrontendLogs: true,
        captureBackendLogs: true,
        waitForIPC: true,
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
    },
  ],

  beforeSession: function (_capabilities, _specs, _browser) {
    if (process.env.VITE_E2E !== "1") {
      throw new Error("VITE_E2E=1 is required for external mode");
    }
    if (process.platform === "linux") {
      console.warn(
        "[wdio] external mode on linux requires webkit2gtk-driver; " +
          "install it before running this config",
      );
    }
  },
};

// WebdriverIO browser mode: run the Tauri frontend in Chrome against a Vite
// dev server. No Tauri binary, no native WebDriver.
//
// Use this for fast feedback on the renderer while iterating on UI. It uses the
// browser fallback MockSidecarTransport, so it never touches a real sidecar.

import path from "node:path";
import { fileURLToPath } from "node:url";
import { sharedConfig } from "./wdio.shared.conf.js";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

process.env.BABELCODEX_E2E_MODE = "browser";

export const config = {
  ...sharedConfig,

  specs: [path.join(__dirname, "tests", "e2e", "browser", "**", "*.spec.ts")],

  baseUrl: process.env.E2E_BROWSER_URL ?? "http://127.0.0.1:5173",

  services: [
    [
      "@wdio/tauri-service",
      {
        mode: "browser",
        devServerUrl: process.env.E2E_BROWSER_URL ?? "http://127.0.0.1:5173",
        devServer: {
          command: "npm run dev -- --host 127.0.0.1 --port 5173",
          cwd: __dirname,
          timeoutMs: 60_000,
          reuseExistingServer: true,
        },
        clearMocks: true,
        captureFrontendLogs: true,
      },
    ],
  ],

  capabilities: [
    {
      browserName: "tauri",
      "goog:chromeOptions": {
        args: [
          "--no-sandbox",
          "--disable-gpu",
          "--window-size=1280,800",
          ...(process.env.E2E_BROWSER_HEADLESS === "1"
            ? ["--headless=new"]
            : []),
        ],
      },
    },
  ],

};

// Shared WebdriverIO configuration for BabelCodex GUI E2E tests.
//
// Browser, native, and external configs extend this. The shared file keeps
// framework, reporter, timeout, and artifact settings in one place so the
// per-mode configs only differ in how they reach the application under test.

import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

export const sharedConfig = {
  runner: "local" as const,
  maxInstances: 1,

  framework: "mocha",

  reporters: ["spec"],

  logLevel: (process.env.WDIO_LOG_LEVEL ?? "info") as
    | "trace"
    | "debug"
    | "info"
    | "warn"
    | "error"
    | "silent",

  waitforTimeout: 15_000,
  connectionRetryTimeout: 120_000,
  connectionRetryCount: 0,

  mochaOpts: {
    ui: "bdd",
    timeout: 120_000,
    bail: true,
  },

  specs: [],
  exclude: [],

  onPrepare: function () {
    // Surface the active mode before the first spec starts.
    const mode = process.env.BABELCODEX_E2E_MODE ?? "unknown";
    console.log(`[wdio] starting E2E run in ${mode} mode`);
  },

  afterTest: async function (_test, _context, { passed }) {
    if (!passed && process.env.BABELCODEX_E2E_SCREENSHOTS !== "0") {
      const dir = path.resolve("build", "e2e", "artifacts");
      await browser.saveScreenshot(
        path.join(dir, `failure-${Date.now()}.png`),
      );
    }
  },
};

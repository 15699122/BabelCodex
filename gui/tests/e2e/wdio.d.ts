// Native E2E specs use the public Tauri service API supplied by
// @wdio/native-types. Captured backend/frontend logs are written by the
// service logger; they are not browser.tauri methods in v1.4.0.

import type { TauriServiceAPI } from "@wdio/native-types";

declare global {
  namespace WebdriverIO {
    interface Browser {
      tauri: TauriServiceAPI;
    }
  }
}

export {};
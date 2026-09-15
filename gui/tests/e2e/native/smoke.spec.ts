// Native embedded smoke test: the real Tauri WebView boots, the embedded
// WebDriver server answers, and the WDIO Tauri plugin is available.

import { browser, expect } from "@wdio/globals";

describe("BabelCodEx GUI native embedded smoke", () => {
  it("renders the main window body", async () => {
    const body = await $("body");
    await expect(body).toBeDisplayed();
  });

  it("exposes the main window through the Tauri API", async () => {
    const windows = await browser.tauri.listWindows();
    expect(windows.length).toBeGreaterThan(0);
    expect(windows).toContain("main");
  });

  it("shows the ready connection state from the E2E transport", async () => {
    const status = await $(".connection");
    await expect(status).toBeDisplayed();
    await browser.waitUntil(async () => {
      const value = await status.getAttribute("data-status");
      return value === "ready";
    }, { timeout: 30_000, timeoutMsg: "sidecar did not become ready" });
    await expect(status).toHaveAttribute("data-status", "ready");
  });

  it("exposes the service-supported Tauri API surface", async () => {
    expect(typeof browser.tauri.execute).toBe("function");
    expect(typeof browser.tauri.listWindows).toBe("function");
  });
});
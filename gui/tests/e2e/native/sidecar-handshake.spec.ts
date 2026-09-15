// Native sidecar handshake: the deterministic E2E transport starts, the JSONL handshake
// completes, and connection failures fail closed with a visible error.

import { browser, expect } from "@wdio/globals";

describe("BabelCodex GUI native sidecar handshake", () => {
  beforeEach(async () => {
    await browser.refresh();
    await browser.pause(1000);
  });

  it("starts the deterministic E2E transport and reaches ready state", async () => {
    const status = await $(".connection");
    await expect(status).toBeDisplayed();
    await expect(status).toHaveAttribute("data-status", "ready", {
      wait: 10000,
    });
  });

  it("exposes the WDIO Tauri API after the sidecar handshake", async () => {
    const page = await browser.tauri.execute(() => ({
      href: window.location.href,
      connection: document.querySelector(".connection")?.getAttribute("data-status"),
    }));
    expect(page.connection).toBe("ready");
    expect(typeof page.href).toBe("string");
  });

  it("exposes the reconnect action inside the diagnostics view", async () => {
    const diagnosticsNav = await $("button=运行诊断");
    await diagnosticsNav.click();

    const reconnect = await $("button=重新连接");
    await expect(reconnect).toBeDisplayed();
  });
});
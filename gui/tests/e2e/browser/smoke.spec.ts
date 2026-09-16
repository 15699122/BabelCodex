// Browser-mode smoke test: renderer boots, mock sidecar connects, and the
// shell renders its primary states without uncaught errors.
//
// This spec runs against a Vite dev server in Chrome, not against a Tauri
// binary, so it exercises the full React component tree and the browser
// fallback MockSidecarTransport only.

import { browser, expect } from "@wdio/globals";

describe("BabelCodex GUI browser smoke", () => {
  it("loads the intake view by default", async () => {
    await browser.url("/");

    const heading = await $("h2=选择 PDF，开始本地翻译");
    await expect(heading).toBeDisplayed();
  });

  it("connects the mock sidecar and reports a ready connection", async () => {
    await browser.url("/");

    const status = await $(".connection");
    await expect(status).toBeDisplayed();
    await expect(status).toHaveAttribute("data-status", "ready");
  });

  it("shows and dismisses the handshake notice", async () => {
    await browser.url("/");

    const notice = await $(".notice-banner");
    await expect(notice).toBeDisplayed();

    const dismiss = await $("button=关闭提示");
    await dismiss.click();
    await expect(notice).not.toBeDisplayed();
  });

  it("exposes no uncaught frontend errors during boot", async () => {
    await browser.url("/");
    await browser.pause(500);

    const errors = await browser.execute(() => {
      return Boolean((window as unknown as { __e2eErrors?: unknown[] }).__e2eErrors?.length);
    });
    await expect(errors).toBe(false);
  });
});

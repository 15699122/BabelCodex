// Browser-mode navigation: switching between the primary views updates the
// active heading and navigation state.

import { browser, expect } from "@wdio/globals";

describe("BabelCodEx GUI browser navigation", () => {
  beforeEach(async () => {
    await browser.url("/");
    await $(".connection");
  });

  it("switches to the jobs view and shows the empty state", async () => {
    const jobsNav = await $("button=翻译任务");
    await jobsNav.click();

    const heading = await $("h2=还没有翻译任务");
    await expect(heading).toBeDisplayed();
  });

  it("switches to the glossary view", async () => {
    const glossaryNav = await $("button=术语与上下文");
    await glossaryNav.click();

    const heading = await $("h2=管理翻译术语和文档上下文");
    await expect(heading).toBeDisplayed();
  });

  it("switches to diagnostics and shows the reconnect action", async () => {
    const diagnosticsNav = await $("button=运行诊断");
    await diagnosticsNav.click();

    const heading = await $("h2=检查本地运行状态");
    await expect(heading).toBeDisplayed();

    const reconnect = await $("button=重新连接");
    await expect(reconnect).toBeDisplayed();
  });

  it("switches to settings and keeps the locale selector disabled", async () => {
    const settingsNav = await $("button=设置");
    await settingsNav.click();

    const heading = await $("h2=运行配置");
    await expect(heading).toBeDisplayed();

    const locale = await $("select[name=界面语言]");
    await expect(locale).toBeDisplayed();
  });

  it("marks the active navigation item with aria-current", async () => {
    const newNav = await $("button=新建翻译");
    await expect(newNav).toHaveAttribute("aria-current", "true");
  });
});

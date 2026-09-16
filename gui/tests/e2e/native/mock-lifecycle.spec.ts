// Native mock lifecycle: a real fixture PDF submitted to the mock translator
// progresses through stages, can be cancelled, and survives a GUI restart.
//
// This is the slowest native spec. Run it explicitly:
//   npm run e2e:native:mock
//
// It relies on ../config/e2e.yaml (translator = "mock") and the deterministic
// workspace produced by npm run e2e:prepare.

import path from "node:path";
import { browser, expect } from "@wdio/globals";

const fixturePdf = path.resolve("build", "e2e", "incoming", "sample.pdf");

const choosePdf = async (filePath: string): Promise<void> => {
  await browser.execute((selectedPath: string) => {
    window.localStorage.setItem("babelcodex:e2e:selected-path", selectedPath);
    const input = document.querySelector("input[type=file]") as HTMLInputElement | null;
    if (!input) throw new Error("file input not found");
    const name = selectedPath.split(/[\\/]/).pop() ?? "sample.pdf";
    const file = new File(["e2e fixture"], name, { type: "application/pdf" });
    const transfer = new DataTransfer();
    transfer.items.add(file);
    input.files = transfer.files;
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }, filePath);
  await expect($(".drop-zone span")).toHaveText(filePath, { wait: 5000 });
};
describe("BabelCodEx GUI native mock lifecycle", () => {
  before(async () => {
    await browser.tauri.execute(() => {
      window.localStorage.removeItem("babelcodex:e2e:mock-state");
    });
    await browser.refresh();
  });

  beforeEach(async () => {
    await browser.refresh();
    await expect($(".connection[data-status=ready]")).toBeDisplayed({ wait: 15000 });
  });

  it("starts a mock translation job and tracks its stages", async () => {
    await choosePdf(fixturePdf);
    const submit = await $("button=加入翻译队列");
    await submit.click();
    const jobsNav = await $("button=翻译任务");
    await jobsNav.click();

    const row = await $(".job-row");
    await expect(row).toBeDisplayed({ wait: 15000 });

    const stage = await $(".stage-badge");
    await expect(stage).toBeDisplayed();
  });

  it("opens the job details panel", async () => {
    await choosePdf(fixturePdf);
    const submit = await $("button=加入翻译队列");
    await submit.click();
    const jobsNav = await $("button=翻译任务");
    await jobsNav.click();

    const row = await $(".job-row");
    await row.click();

    const details = await $(".detail-card");
    await expect(details).toBeDisplayed({ wait: 10000 });
  });

  it("cancels an in-progress job", async () => {
    await choosePdf(fixturePdf);
    const submit = await $("button=加入翻译队列");
    await submit.click();
    const jobsNav = await $("button=翻译任务");
    await jobsNav.click();

    const cancel = await $(".cancel-action");
    await cancel.click();

    const stage = await $(".stage-badge");
    await expect(stage).toHaveText(/已取消|cancelled/i, { wait: 10000 });
  });

  it("recovers job state after a GUI restart", async () => {
    await choosePdf(fixturePdf);
    const submit = await $("button=加入翻译队列");
    await submit.click();
    const jobsNav = await $("button=翻译任务");
    await jobsNav.click();

    const row = await $(".job-row");
    await expect(row).toBeDisplayed({ wait: 15000 });

    await browser.reloadSession();
    await browser.refresh();
    await expect($(".connection[data-status=ready]")).toBeDisplayed({ wait: 15000 });

    const jobsNavAfter = await $("button=翻译任务");
    await jobsNavAfter.click();

    const rowAfter = await $(".job-row");
    await expect(rowAfter).toBeDisplayed({ wait: 10000 });
  });
});

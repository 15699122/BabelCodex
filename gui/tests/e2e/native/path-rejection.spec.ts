// Native path rejection: paths outside the allowlist cannot be submitted,
// the connection stays ready, and the error notice is not overwritten by
// polling updates.

import path from "node:path";
import { browser, expect } from "@wdio/globals";

const outsidePdf = path.resolve("build/e2e/outside/outside.pdf");

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

describe("BabelCodEx GUI native path rejection", () => {
  beforeEach(async () => {
    await browser.execute(() => {
      window.localStorage.removeItem("babelcodex:e2e:mock-state");
      window.localStorage.removeItem("babelcodex:e2e:selected-path");
    });
    await browser.refresh();
    const status = await $(".connection");
    await expect(status).toHaveAttribute("data-status", "ready", { wait: 10000 });
  });

  it("disables the submit button when no PDF is selected", async () => {
    const submit = await $("button=加入翻译队列");
    await expect(submit).toBeDisplayed();
    await expect(submit).toBeDisabled();
  });

  it("rejects a real PDF outside the configured input directory", async () => {
    await choosePdf(outsidePdf);

    const submit = await $("button=加入翻译队列");
    await submit.click();

    const notice = await $(".notice-banner");
    await expect(notice).toHaveText(/outside the configured input directory/i, { wait: 10000 });
  });

  it("keeps the connection ready after a rejected path", async () => {
    await choosePdf(outsidePdf);

    const submit = await $("button=加入翻译队列");
    await submit.click();
    await browser.pause(500);

    const status = await $(".connection");
    await expect(status).toHaveAttribute("data-status", "ready");
  });

  it("does not start a translation after rejection", async () => {
    await choosePdf(outsidePdf);

    const submit = await $("button=加入翻译队列");
    await submit.click();
    const jobsNav = await $("button=翻译任务");
    await jobsNav.click();

    const empty = await $("h2=还没有翻译任务");
    await expect(empty).toBeDisplayed();
  });
});
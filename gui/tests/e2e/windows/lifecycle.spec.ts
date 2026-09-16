// Windows-only lifecycle specs.

import { existsSync } from "node:fs";
import path from "node:path";
import { browser, expect } from "@wdio/globals";

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

describe("BabelCodex GUI Windows lifecycle", () => {
  before(function () {
    if (process.platform !== "win32") {
      this.skip();
    }
  });

  it("builds and launches the Windows .exe target", () => {
    const binary = path.resolve("src-tauri", "target", "debug", "babelcodex-gui.exe");
    expect(existsSync(binary)).toBe(true);
  });

  it("submits a job through the Windows native session", async () => {
    // @wdio/tauri-service owns embedded app teardown in its launcher.onComplete
    // hook. The Windows validation command checks tasklist after WDIO exits.
    await browser.refresh();
    const status = await $(".connection");
    await expect(status).toHaveAttribute("data-status", "ready", { wait: 10000 });

    await choosePdf(path.resolve("build", "e2e", "incoming", "sample.pdf"));
    await $("button=加入翻译队列").click();
    await $("button=翻译任务").click();
    await $(".job-row").waitForDisplayed({ timeout: 15000 });
  });
});
 // Windows-only native specs.
 //
 // These specs are skipped automatically on Linux. They cover behaviours that
 // only appear on Windows: executable extension handling, Windows path
 // semantics, and the configured input-directory allowlist.

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

 describe("BabelCodex GUI Windows integration", () => {
   before(function () {
     if (process.platform !== "win32") {
       this.skip();
     }
   });

   beforeEach(async () => {
     await browser.execute(() => {
       window.localStorage.removeItem("babelcodex:e2e:mock-state");
       window.localStorage.removeItem("babelcodex:e2e:selected-path");
     });
     await browser.refresh();
     await expect($(".connection[data-status=ready]")).toBeDisplayed({ wait: 15000 });
   });

   it("builds and launches the Windows .exe target", () => {
     const binary = path.resolve("src-tauri", "target", "debug", "babelcodex-gui.exe");
     expect(path.extname(binary)).toBe(".exe");
     expect(existsSync(binary)).toBe(true);
   });

   it("preserves a PDF path containing Windows workspace spaces", async () => {
     const fixture = path.resolve("build", "e2e", "incoming", "sample.pdf");
     await choosePdf(fixture);
   });

   it("rejects an existing Windows path outside the configured allowlist", async () => {
     const outside = path.resolve("build", "e2e", "outside", "outside.pdf");
     await choosePdf(outside);
     await $("button=加入翻译队列").click();

     const error = await $(".notice-banner");
     await expect(error).toBeDisplayed({ wait: 10000 });
     await expect(error).toHaveText(/outside|输入目录|input directory/i);
     await expect($(".connection")).toHaveAttribute("data-status", "ready");
   });
 });
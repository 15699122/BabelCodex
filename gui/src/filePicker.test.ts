import { describe, expect, it } from "vitest";
import { createFilePicker, isPdfPath } from "./filePicker";

describe("PDF file picker boundary", () => {
  it("accepts only PDF paths", () => {
    expect(isPdfPath("paper.pdf")).toBe(true);
    expect(isPdfPath("PAPER.PDF")).toBe(true);
    expect(isPdfPath("paper.docx")).toBe(false);
  });

  it("maps browser files without exposing arbitrary file APIs", () => {
    const picker = createFilePicker();
    expect(picker.fromBrowserFile(new File(["pdf"], "paper.pdf", { type: "application/pdf" }))).toEqual({
      path: "paper.pdf",
      displayName: "paper.pdf",
    });
    expect(picker.fromBrowserFile(new File(["text"], "notes.txt", { type: "text/plain" }))).toBeNull();
  });
});
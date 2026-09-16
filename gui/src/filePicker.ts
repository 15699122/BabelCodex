import { open } from "@tauri-apps/plugin-dialog";

export interface PickedPdf {
  path: string;
  displayName: string;
}

export interface FilePicker {
  pickPdf(): Promise<PickedPdf | null>;
  fromBrowserFile(file: File): PickedPdf | null;
}

export const isTauriRuntime = (): boolean => typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

export const isPdfPath = (path: string): boolean => path.trim().toLowerCase().endsWith(".pdf");

export const createFilePicker = (): FilePicker => ({
  async pickPdf(): Promise<PickedPdf | null> {
    if (!isTauriRuntime()) return null;
    const selected = await open({
      multiple: false,
      directory: false,
      filters: [{ name: "PDF documents", extensions: ["pdf"] }],
    });
    if (typeof selected !== "string" || !isPdfPath(selected)) return null;
    return { path: selected, displayName: selected.split(/[\\/]/).pop() ?? selected };
  },

  fromBrowserFile(file: File): PickedPdf | null {
    if (!isPdfPath(file.name)) return null;
    // Chromium exposes only the basename for a WebDriver-assigned file. The
    // E2E build supplies the selected absolute path through localStorage so
    // native tests can exercise the same input/change path without opening a
    // real OS picker. This branch is absent from normal builds.
    const e2ePath =
      import.meta.env.VITE_E2E === "1" && typeof window !== "undefined"
        ? window.localStorage.getItem("babelcodex:e2e:selected-path")
        : null;
    return { path: e2ePath || file.name, displayName: file.name };
  },
});
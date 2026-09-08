import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("BabelCodex GUI shell", () => {
  it("renders the local translation intake by default", async () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "New translation" })).toBeTruthy();
    expect(screen.getByLabelText("Input path")).toBeTruthy();
    expect(screen.getByText("Files stay inside your configured workspace.")).toBeTruthy();
    expect(await screen.findByText("Sidecar handshake ready")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Browse" })).toBeTruthy();
  });

  it("accepts a dropped PDF and rejects a non-PDF", async () => {
    render(<App />);
    expect(await screen.findByText("Sidecar handshake ready")).toBeTruthy();
    const dropZone = screen.getByText("Drop a PDF here").parentElement!;
    fireEvent.drop(dropZone, { dataTransfer: { files: [new File(["pdf"], "dropped.pdf", { type: "application/pdf" })] } });
    expect((screen.getByLabelText("Input path") as HTMLInputElement).value).toBe("dropped.pdf");
    fireEvent.drop(dropZone, { dataTransfer: { files: [new File(["txt"], "notes.txt", { type: "text/plain" })] } });
    expect(await screen.findByText("Choose a PDF file.")).toBeTruthy();
  });

  it("switches between the task workbench views", async () => {
    render(<App />);
    expect(await screen.findByText("Sidecar handshake ready")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Jobs/ }));
    expect(screen.getByRole("heading", { name: "Recent jobs" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Diagnostics/ }));
    expect(screen.getByRole("heading", { name: "Quiet confidence" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "reconnect" })).toBeTruthy();
  });

  it("shows a live connection state and can cancel a queued mock job", async () => {
    render(<App />);
    fireEvent.change(screen.getByLabelText("Input path"), {
      target: { value: "/workspace/incoming/cancel.pdf" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Queue translation/ }));
    expect(await screen.findByRole("heading", { name: "Recent jobs" })).toBeTruthy();
    const cancel = await screen.findByRole("button", { name: "cancel" });
    fireEvent.click(cancel);
    expect(await screen.findByText("cancelled")).toBeTruthy();
  });

  it("opens job details through get_job and shows reported artifacts", async () => {
    render(<App />);
    fireEvent.change(screen.getByLabelText("Input path"), {
      target: { value: "/workspace/incoming/details.pdf" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Queue translation/ }));
    expect(await screen.findByRole("heading", { name: "Recent jobs" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Open details for mock-job-1" }));
    expect(await screen.findByRole("heading", { name: "details.pdf" })).toBeTruthy();
    expect(screen.getByText("mock-babeldoc")).toBeTruthy();
    expect(screen.getByText("mono pdf")).toBeTruthy();
    expect(screen.getByText("validated")).toBeTruthy();
    expect(screen.getByText("STAGE TIMELINE")).toBeTruthy();
    expect(screen.getByText("Prepare runtime")).toBeTruthy();
    expect(screen.getByText("in progress")).toBeTruthy();
    expect(screen.getByText("RESULT SUMMARY")).toBeTruthy();
    expect(screen.getByText("1 · 24.3 KB")).toBeTruthy();
    expect(screen.getByText("sha256 · mock-sha256")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Refresh job details" }));
    expect(await screen.findByText("Refreshed mock-job-1")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "← Back to jobs" }));
    expect(screen.getByRole("heading", { name: "Recent jobs" })).toBeTruthy();
  });

  it("queues a PDF through the transport boundary", async () => {
    render(<App />);
    fireEvent.change(screen.getByLabelText("Input path"), {
      target: { value: "/workspace/incoming/paper.pdf" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Queue translation/ }));
    expect(await screen.findByRole("heading", { name: "Recent jobs" })).toBeTruthy();
    expect(screen.getByText(/mock-job-1/)).toBeTruthy();
  });
});
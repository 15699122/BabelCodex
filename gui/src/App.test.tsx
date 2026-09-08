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
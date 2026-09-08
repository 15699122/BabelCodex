import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("BabelCodex GUI shell", () => {
  it("renders the local translation intake by default", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "New translation" })).toBeTruthy();
    expect(screen.getByLabelText("Input path")).toBeTruthy();
    expect(screen.getByText("Files stay inside your configured workspace.")).toBeTruthy();
  });

  it("switches between the task workbench views", () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /Jobs/ }));
    expect(screen.getByRole("heading", { name: "Recent jobs" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Diagnostics/ }));
    expect(screen.getByRole("heading", { name: "Quiet confidence" })).toBeTruthy();
  });

  it("queues a PDF through the transport boundary", async () => {
    render(<App />);
    fireEvent.change(screen.getByLabelText("Input path"), {
      target: { value: "/workspace/incoming/paper.pdf" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Queue translation/ }));
    expect(await screen.findByRole("heading", { name: "Recent jobs" })).toBeTruthy();
    expect(screen.getByText("Started mock-job-1")).toBeTruthy();
  });
});
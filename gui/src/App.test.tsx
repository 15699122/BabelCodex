import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("BabelCodex GUI shell", () => {
  it("renders the local translation intake by default", async () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "选择 PDF，开始本地翻译" })).toBeTruthy();
    expect(screen.getByText("将 PDF 拖放到这里")).toBeTruthy();
    expect(screen.getByText("只能选择配置输入目录中的 PDF 文件。")).toBeTruthy();
    expect(await screen.findByText("本地服务已连接")).toBeTruthy();
    expect(screen.getByRole("button", { name: "选择 PDF" })).toBeTruthy();
  });

  it("accepts a dropped PDF and rejects a non-PDF", async () => {
    render(<App />);
    expect(await screen.findByText("本地服务已连接")).toBeTruthy();
    const dropZone = screen.getByText("将 PDF 拖放到这里").parentElement!;
    fireEvent.drop(dropZone, { dataTransfer: { files: [new File(["pdf"], "dropped.pdf", { type: "application/pdf" })] } });
    expect(screen.getByText("dropped.pdf")).toBeTruthy();
    fireEvent.drop(dropZone, { dataTransfer: { files: [new File(["txt"], "notes.txt", { type: "text/plain" })] } });
    expect(await screen.findByText("请选择 PDF 文件。")).toBeTruthy();
  });

  it("switches between the task workbench views", async () => {
    render(<App />);
    expect(await screen.findByText("本地服务已连接")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /翻译任务/ }));
    expect(screen.getByRole("heading", { name: "还没有翻译任务" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /运行诊断/ }));
    expect(screen.getByRole("heading", { name: "检查本地运行状态" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "重新连接" })).toBeTruthy();
  });

  it("shows a live connection state and can cancel a queued mock job", async () => {
    render(<App />);
    const dropZone = screen.getByText("将 PDF 拖放到这里").parentElement!;
    fireEvent.drop(dropZone, { dataTransfer: { files: [new File(["pdf"], "cancel.pdf", { type: "application/pdf" })] } });
    fireEvent.click(screen.getByRole("button", { name: /加入翻译队列/ }));
    const jobId = await screen.findByText("mock-job-1", { selector: ".job-id" });
    const jobRow = jobId.closest(".job-row")!;
    expect(jobRow.textContent).toContain("mock-job-1");
    const cancel = jobRow.querySelector(".cancel-action")!;
    fireEvent.click(cancel);
    expect(await screen.findByText("已取消")).toBeTruthy();
  });

  it("opens job details through get_job and shows reported artifacts", async () => {
    render(<App />);
    const dropZone = screen.getByText("将 PDF 拖放到这里").parentElement!;
    fireEvent.drop(dropZone, { dataTransfer: { files: [new File(["pdf"], "details.pdf", { type: "application/pdf" })] } });
    fireEvent.click(screen.getByRole("button", { name: /加入翻译队列/ }));
    const jobId = await screen.findByText("mock-job-1", { selector: ".job-id" });
    const jobRow = jobId.closest(".job-row")!;
    expect(jobRow.textContent).toContain("mock-job-1");
    fireEvent.click(jobRow);
    expect(await screen.getByRole("heading", { name: "任务详情" })).toBeTruthy();
  });

  it("queues a PDF through the transport boundary", async () => {
    render(<App />);
    const dropZone = screen.getByText("将 PDF 拖放到这里").parentElement!;
    fireEvent.drop(dropZone, { dataTransfer: { files: [new File(["pdf"], "paper.pdf", { type: "application/pdf" })] } });
    fireEvent.click(screen.getByRole("button", { name: /加入翻译队列/ }));
    expect((await screen.findAllByText("mock-job-1")).length).toBeGreaterThan(0);
  });

  it("edits and saves a document glossary and context through the sidecar boundary", async () => {
    render(<App />);
    expect(await screen.findByText("本地服务已连接")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "术语与上下文" }));
    expect(screen.getByRole("heading", { name: "管理翻译术语和文档上下文", level: 2 })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "文档术语" }));
    fireEvent.change(screen.getByLabelText("文档标识"), { target: { value: "paper" } });
    fireEvent.click(screen.getByRole("button", { name: "加载" }));
    expect(await screen.findByText("术语表和文档上下文已加载")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "新增术语" }));
    fireEvent.change(screen.getByLabelText("源术语 1"), { target: { value: "model" } });
    fireEvent.change(screen.getByLabelText("目标术语 1"), { target: { value: "模型" } });
    fireEvent.click(screen.getByRole("button", { name: "保存术语表" }));
    expect(await screen.findByText("术语表已保存")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("上下文内容"), { target: { value: "论文标题\n摘要\n上下文。" } });
    fireEvent.click(screen.getByRole("button", { name: "保存上下文" }));
    expect(await screen.findByText("文档上下文已保存")).toBeTruthy();
  });

  it("requires a document stem before document glossary operations", async () => {
    render(<App />);
    expect(await screen.findByText("本地服务已连接")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "术语与上下文" }));
    fireEvent.click(screen.getByRole("button", { name: "文档术语" }));
    fireEvent.click(screen.getByRole("button", { name: "加载" }));
    expect(await screen.findByText("加载文档术语表前，请先填写文档标识。")).toBeTruthy();
  });

  it("keeps the future i18n selector visible but disabled", async () => {
    render(<App />);
    expect(await screen.findByText("本地服务已连接")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "设置" }));
    expect(screen.getByRole("heading", { name: "运行配置" })).toBeTruthy();
    const locale = screen.getByRole("combobox", { name: "界面语言" });
    expect(locale.hasAttribute("disabled")).toBe(true);
    expect(screen.getByRole("option", { name: "简体中文（当前）" })).toBeTruthy();
    expect(screen.getByText("语言切换功能将在后续版本提供。")).toBeTruthy();
  });
});

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { JobStore } from "./jobStore";
import { MockSidecarTransport } from "./sidecar";
import type { SidecarTransport } from "./protocol";

describe("JobStore", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("connects, starts polling, and applies sidecar events", async () => {
    const transports: MockSidecarTransport[] = [];
    const store = new JobStore(() => {
      const transport = new MockSidecarTransport();
      transports.push(transport);
      return transport;
    });
    await store.connect("config/test.toml");
    expect(store.getSnapshot().connection.status).toBe("ready");
    const jobId = await store.startTranslation("/workspace/incoming/paper.pdf");
    await vi.advanceTimersByTimeAsync(0);
    await store.cancel(jobId);
    const job = store.getSnapshot().jobs.find((candidate) => candidate.job_id === jobId);
    expect(job?.status).toBe("cancelled");
    expect(transports[0].requests.map((request) => request.method)).toEqual(
      expect.arrayContaining(["start", "list_jobs", "start_translation", "cancel_job", "poll_events"]),
    );
    await store.close();
  });

  it("recreates the transport and reconciles active jobs after reconnect", async () => {
    const state = { sequence: 0, jobs: [], events: [] as Array<import("./protocol").JobEvent> };
    const first = new MockSidecarTransport(state);
    const second = new MockSidecarTransport(state);
    const transports = [first, second];
    const store = new JobStore(() => transports.shift() ?? new MockSidecarTransport());
    await store.connect();
    const jobId = await store.startTranslation("/workspace/incoming/reconnect.pdf");
    const job = store.getSnapshot().jobs.find((candidate) => candidate.job_id === jobId);
    expect(job?.status).toBe("running");
    await store.reconnect();
    expect(store.getSnapshot().connection.status).toBe("ready");
    expect(second.requests.map((request) => request.method)).toContain("list_jobs");
    expect(second.requests.map((request) => request.method)).toContain("get_job");
    expect(store.getSnapshot().jobs.find((candidate) => candidate.job_id === jobId)?.status).toBe("running");
    expect(second.requests.find((request) => request.method === "poll_events")?.params.after_sequence).toBe(0);
    await store.close();
  });

  it("refreshes a selected job with optional artifact metadata", async () => {
    const transport = new MockSidecarTransport();
    const store = new JobStore(() => transport);
    await store.connect();
    const jobId = await store.startTranslation("/workspace/incoming/detail.pdf");
    const job = await store.getJob(jobId);
    expect(job?.artifacts?.[0].artifact_type).toBe("mono_pdf");
    expect(job?.qa_status).toBe("pending");
    expect(transport.requests.map((request) => request.method)).toContain("get_job");
    await store.close();
  });

  it("routes glossary and context editors through scoped sidecar methods", async () => {
    const transport = new MockSidecarTransport();
    const store = new JobStore(() => transport);
    await store.connect();
    await store.listGlossary("document", "paper");
    await store.saveGlossary("document", [{ source: "model", target: "模型", notes: "", enabled: true }], "paper");
    await store.getContext("paper");
    await store.saveContext("paper", "Paper\nAbstract\nContext.");
    expect(transport.requests.map((request) => request.method)).toEqual(
      expect.arrayContaining(["list_glossary", "save_glossary", "get_context", "save_context"]),
    );
    expect(transport.requests.find((request) => request.method === "save_glossary")?.params).toMatchObject({
      scope: "document",
      document_id: "paper",
    });
    expect(transport.requests.find((request) => request.method === "save_context")?.params).toMatchObject({
      document_id: "paper",
      text: "Paper\nAbstract\nContext.",
    });
    await store.close();
  });

  it("refreshes a watched job immediately and stops after cleanup", async () => {
    const transport = new MockSidecarTransport();
    const store = new JobStore(() => transport);
    await store.connect();
    const jobId = await store.startTranslation("/workspace/incoming/watch.pdf");
    const beforeWatch = transport.requests.filter((request) => request.method === "get_job").length;
    const stopWatching = store.watchJob(jobId, 1000);
    await Promise.resolve();
    expect(transport.requests.filter((request) => request.method === "get_job").length).toBe(beforeWatch + 1);
    await vi.advanceTimersByTimeAsync(1000);
    expect(transport.requests.filter((request) => request.method === "get_job").length).toBe(beforeWatch + 2);
    stopWatching();
    await vi.advanceTimersByTimeAsync(3000);
    expect(transport.requests.filter((request) => request.method === "get_job").length).toBe(beforeWatch + 2);
    await store.close();
  });

  it("schedules exponential reconnect after a polling failure and resets after success", async () => {
    class FlakyTransport extends MockSidecarTransport implements SidecarTransport {
      failPoll = true;

      override async request<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
        if (method === "poll_events" && this.failPoll) throw new Error("connection lost");
        return super.request<T>(method, params);
      }
    }

    const first = new FlakyTransport();
    const second = new FlakyTransport();
    first.failPoll = false;
    second.failPoll = false;
    const queued = [first, second];
    const reconnectingStore = new JobStore(() => queued.shift() ?? new FlakyTransport());
    await reconnectingStore.connect();
    first.failPoll = true;
    await vi.advanceTimersByTimeAsync(750);
    expect(reconnectingStore.getSnapshot().connection.status).toBe("reconnecting");
    expect(reconnectingStore.getSnapshot().notice).toContain("scheduled in 1s");
    await vi.advanceTimersByTimeAsync(999);
    expect(second.requests.map((request) => request.method)).not.toContain("start");
    await vi.advanceTimersByTimeAsync(1);
    await Promise.resolve();
    expect(reconnectingStore.getSnapshot().connection.status).toBe("ready");
    await reconnectingStore.close();
  });

  it("cleans a pending reconnect timer when closed", async () => {
    class FailingPollTransport extends MockSidecarTransport {
      override async request<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
        if (method === "poll_events") throw new Error("offline");
        return super.request<T>(method, params);
      }
    }

    const transport = new FailingPollTransport();
    const store = new JobStore(() => transport);
    await store.connect();
    await vi.advanceTimersByTimeAsync(750);
    expect(store.getSnapshot().connection.status).toBe("reconnecting");
    await store.close();
    await vi.advanceTimersByTimeAsync(30000);
    expect(transport.requests.filter((request) => request.method === "start")).toHaveLength(1);
  });
});
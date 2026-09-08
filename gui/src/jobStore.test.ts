import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { JobStore } from "./jobStore";
import { MockSidecarTransport } from "./sidecar";

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
});
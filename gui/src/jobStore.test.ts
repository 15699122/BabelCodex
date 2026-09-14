import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PROTOCOL_VERSION } from "./protocol";
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

  it("dismisses the current notice without changing connection state", async () => {
    const store = new JobStore(() => new MockSidecarTransport());
    await store.connect();
    expect(store.getSnapshot().notice).toBe("Sidecar handshake ready");
    store.dismissNotice();
    expect(store.getSnapshot().notice).toBe("");
    expect(store.getSnapshot().connection.status).toBe("ready");
    await store.close();
  });

  it("keeps a shared notice across polling and preserves ready state on path rejection", async () => {
    class RejectingTransport extends MockSidecarTransport implements SidecarTransport {
      override async request<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
        if (method === "start_translation") throw new Error("source_path is outside the configured input directory");
        return super.request<T>(method, params);
      }
    }

    const transport = new RejectingTransport();
    const store = new JobStore(() => transport);
    await store.connect();
    store.setNotice("selected.pdf");
    expect(store.getSnapshot().notice).toBe("selected.pdf");
    await store.getJob("mock-job-1").catch(() => undefined);
    expect(store.getSnapshot().notice).toBe("selected.pdf");

    await expect(store.startTranslation("/outside/missing.pdf")).rejects.toThrow(
      /outside the configured input directory/,
    );
    expect(store.getSnapshot().connection.status).toBe("ready");
    expect(transport.requests.filter((request) => request.method === "poll_events")).not.toContain("start");
    await store.close();
  });

  it("routes retry, artifact validation and QA through the sidecar contract", async () => {
    const state = {
      sequence: 0,
      jobs: [
        {
          job_id: "mock-job-1",
          source_path: "/workspace/incoming/failed.pdf",
          status: "failed" as const,
          stage: "completed" as const,
          attempts: 1,
          safe_error_message: "failed",
          updated_at: "2026-09-10T00:00:00.000Z",
          completed_at: "",
        },
      ],
      events: [] as Array<import("./protocol").JobEvent>,
    };
    const transport = new MockSidecarTransport(state);
    const store = new JobStore(() => transport);
    await store.connect();
    await store.retry("mock-job-1");
    await store.validateOutput("mock-job-1");
    await store.runQa("mock-job-1");
    expect(transport.requests.map((request) => request.method)).toEqual(
      expect.arrayContaining(["retry_job", "validate_output", "run_qa"]),
    );
    await store.close();
  });

  it("does not duplicate a job when a created event is replayed after list_jobs", async () => {
    const state = {
      sequence: 1,
      jobs: [
        {
          job_id: "mock-job-1",
          source_path: "/workspace/incoming/replayed.pdf",
          status: "running" as const,
          stage: "translating" as const,
          attempts: 2,
          safe_error_message: null,
          updated_at: "2026-09-10T00:00:02.000Z",
          completed_at: "",
        },
      ],
      events: [
        {
          event_type: "job_created" as const,
          job_id: "mock-job-1",
          sequence: 2,
          timestamp: "2026-09-10T00:00:03.000Z",
          payload: {
            status: "running",
            source_path: "/workspace/incoming/replayed.pdf",
          },
        },
      ],
    };
    const transport = new MockSidecarTransport(state);
    const store = new JobStore(() => transport);

    await store.connect();

    expect(store.getSnapshot().jobs).toHaveLength(1);
    expect(store.getSnapshot().jobs[0]).toMatchObject({
      job_id: "mock-job-1",
      stage: "translating",
      attempts: 2,
    });
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

  it("fails fast with a rebuild hint when the sidecar handshake is stale", async () => {
    class StaleSidecarTransport extends MockSidecarTransport implements SidecarTransport {
      override async request<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
        if (method === "get_server_info") {
          return {
            protocol_version: PROTOCOL_VERSION - 1,
            package_version: "stale-babelcodex",
            capabilities: [],
          } as T;
        }
        return super.request<T>(method, params);
      }
    }

    const transport = new StaleSidecarTransport();
    const store = new JobStore(() => transport);
    await expect(store.connect()).rejects.toThrow(/sidecar protocol mismatch/);
    const { connection } = store.getSnapshot();
    expect(connection.status).toBe("failed");
    if (connection.status !== "failed") throw new Error("expected a failed connection");
    expect(connection.error).toContain("Rebuild the bundled babelcodex-service");
  });
});
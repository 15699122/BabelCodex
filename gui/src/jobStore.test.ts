import { describe, expect, it } from "vitest";
import { JobStore } from "./jobStore";
import { MockSidecarTransport } from "./sidecar";

describe("JobStore", () => {
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
    await new Promise((resolve) => setTimeout(resolve, 0));
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
});
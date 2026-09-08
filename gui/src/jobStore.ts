import type { JobEvent, JobState, SidecarTransport } from "./protocol";
import { createSidecarTransport } from "./sidecar";

export type ConnectionState =
  | { status: "starting" }
  | { status: "ready"; protocolVersion: number }
  | { status: "reconnecting"; attempt: number }
  | { status: "failed"; error: string };

export interface JobStoreSnapshot {
  connection: ConnectionState;
  jobs: JobState[];
  lastSequence: number;
  notice: string;
}

type Listener = (snapshot: JobStoreSnapshot) => void;
type TransportFactory = () => SidecarTransport;

const TERMINAL_STATUSES = new Set<JobState["status"]>(["completed", "failed", "cancelled"]);

export class JobStore {
  private transport: SidecarTransport;
  private readonly createTransport: TransportFactory;
  private readonly listeners = new Set<Listener>();
  private pollTimer: ReturnType<typeof setInterval> | undefined;
  private configPath = "config/example.toml";
  private snapshot: JobStoreSnapshot = {
    connection: { status: "starting" },
    jobs: [],
    lastSequence: 0,
    notice: "Sidecar starting",
  };

  constructor(createTransport: TransportFactory = createSidecarTransport) {
    this.createTransport = createTransport;
    this.transport = createTransport();
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    listener(this.snapshot);
    return () => this.listeners.delete(listener);
  }

  getSnapshot(): JobStoreSnapshot {
    return this.snapshot;
  }

  async connect(configPath = this.configPath): Promise<void> {
    this.configPath = configPath;
    this.stopPolling();
    this.setSnapshot({ connection: { status: "starting" }, notice: "Starting sidecar" });
    try {
      await this.transport.start(configPath);
      await this.refreshJobs();
      if (this.snapshot.jobs.some((job) => !TERMINAL_STATUSES.has(job.status))) {
        await this.reconcileJobs();
      }
      this.setSnapshot({
        connection: { status: "ready", protocolVersion: 1 },
        notice: "Sidecar handshake ready",
      });
      this.startPolling();
      await this.pollOnce();
    } catch (error) {
      this.setSnapshot({
        connection: { status: "failed", error: this.errorMessage(error) },
        notice: "Sidecar unavailable",
      });
      throw error;
    }
  }

  async reconnect(): Promise<void> {
    const attempt = this.snapshot.connection.status === "reconnecting"
      ? this.snapshot.connection.attempt + 1
      : 1;
    this.setSnapshot({
      connection: { status: "reconnecting", attempt },
      notice: `Reconnecting to sidecar (${attempt})`,
    });
    await this.transport.close();
    this.transport = this.createTransport();
    this.setSnapshot({ lastSequence: 0 });
    await this.connect(this.configPath);
  }

  async startTranslation(sourcePath: string): Promise<string> {
    const result = await this.request<{ job_id: string }>("start_translation", { source_path: sourcePath });
    await this.refreshJobs();
    return result.job_id;
  }

  async cancel(jobId: string): Promise<void> {
    await this.request("cancel_job", { job_id: jobId });
    await this.pollOnce();
  }

  async getJob(jobId: string): Promise<JobState | null> {
    const result = await this.request<{ job: JobState | null }>("get_job", { job_id: jobId });
    if (!result.job) return null;
    const jobs = this.snapshot.jobs.map((job) => (job.job_id === jobId ? { ...job, ...result.job } : job));
    this.setSnapshot({ jobs });
    return result.job;
  }

  async close(): Promise<void> {
    this.stopPolling();
    await this.transport.close();
  }

  private startPolling(): void {
    this.stopPolling();
    this.pollTimer = setInterval(() => {
      void this.pollOnce();
    }, 750);
  }

  private stopPolling(): void {
    if (this.pollTimer !== undefined) clearInterval(this.pollTimer);
    this.pollTimer = undefined;
  }

  private async refreshJobs(): Promise<void> {
    const result = await this.request<{ jobs: JobState[] }>("list_jobs");
    const previous = new Map(this.snapshot.jobs.map((job) => [job.job_id, job]));
    const jobs = result.jobs.map((job) => ({ ...previous.get(job.job_id), ...job }));
    this.setSnapshot({ jobs });
  }

  private async reconcileJobs(): Promise<void> {
    const activeJobs = this.snapshot.jobs.filter((job) => !TERMINAL_STATUSES.has(job.status));
    const reconciled = await Promise.all(
      activeJobs.map(async (job) => {
        const result = await this.transport.request<{ job: JobState | null }>("get_job", {
          job_id: job.job_id,
        });
        return result.job ? { ...job, ...result.job } : job;
      }),
    );
    const updates = new Map(reconciled.map((job) => [job.job_id, job]));
    this.setSnapshot({ jobs: this.snapshot.jobs.map((job) => updates.get(job.job_id) ?? job) });
  }

  private async pollOnce(): Promise<void> {
    if (this.snapshot.connection.status !== "ready") return;
    try {
      const result = await this.transport.request<{ events: JobEvent[]; next_sequence: number }>(
        "poll_events",
        { after_sequence: this.snapshot.lastSequence },
      );
      let jobs = this.snapshot.jobs;
      for (const event of result.events) jobs = this.applyEvent(jobs, event);
      this.setSnapshot({ jobs, lastSequence: Math.max(this.snapshot.lastSequence, result.next_sequence) });
    } catch (error) {
      this.setSnapshot({
        connection: { status: "reconnecting", attempt: 1 },
        notice: `Sidecar reconnect required: ${this.errorMessage(error)}`,
      });
      this.stopPolling();
    }
  }

  private async request<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
    try {
      return await this.transport.request<T>(method, params);
    } catch (error) {
      this.setSnapshot({
        connection: { status: "reconnecting", attempt: 1 },
        notice: `Sidecar request failed: ${this.errorMessage(error)}`,
      });
      throw error;
    }
  }

  private applyEvent(jobs: JobState[], event: JobEvent): JobState[] {
    const index = jobs.findIndex((job) => job.job_id === event.job_id);
    if (index < 0) return jobs;
    const current = jobs[index];
    const payload = event.payload;
    const next: JobState = { ...current };
    if (event.event_type === "status_changed") {
      const status = payload.status;
      if (status === "running" || status === "retry_pending" || status === "completed" || status === "failed" || status === "cancelled") {
        next.status = status;
      }
    }
    if (event.event_type === "progress") {
      const stage = payload.stage;
      if (stage === "discovered" || stage === "preparing_runtime" || stage === "translating" || stage === "rendering" || stage === "validating_output" || stage === "completed") next.stage = stage;
    }
    if (event.event_type === "job_completed" && payload.job && typeof payload.job === "object") Object.assign(next, payload.job);
    if (event.event_type === "job_failed" && payload.error && typeof payload.error === "object") next.safe_error_message = String((payload.error as { safe_message?: unknown }).safe_message ?? "Translation failed");
    return jobs.map((job, jobIndex) => (jobIndex === index ? next : job));
  }

  private setSnapshot(patch: Partial<JobStoreSnapshot>): void {
    this.snapshot = { ...this.snapshot, ...patch };
    for (const listener of this.listeners) listener(this.snapshot);
  }

  private errorMessage(error: unknown): string {
    return error instanceof Error ? error.message : "unknown sidecar error";
  }
}

export const isActiveJob = (job: JobState): boolean => !TERMINAL_STATUSES.has(job.status);
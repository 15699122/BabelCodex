import { Command, Child } from "@tauri-apps/plugin-shell";
import { JobState, makeRequest, PROTOCOL_VERSION, SidecarResponse, SidecarTransport } from "./protocol";

const SIDECAR_PROGRAM = "binaries/babelcodex-service";

class TauriSidecarTransport implements SidecarTransport {
  private child: Child | null = null;
  private readonly pending = new Map<string, (value: unknown) => void>();
  private readonly failures = new Map<string, (reason: Error) => void>();
  private buffer = "";

  async start(configPath: string): Promise<void> {
    const command = Command.sidecar(SIDECAR_PROGRAM, ["--config", configPath]);
    command.stdout.on("data", (chunk) => this.consume(String(chunk)));
    command.on("error", (message) => this.rejectAll(new Error(message)));
    command.on("close", (payload) => {
      if (payload.code !== 0) {
        this.rejectAll(new Error(`sidecar exited with code ${payload.code ?? "signal"}`));
      }
    });
    this.child = await command.spawn();
  }

  async request<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
    if (!this.child) throw new Error("sidecar is not running");
    const request = makeRequest(method, params);
    const response = new Promise<T>((resolve, reject) => {
      this.pending.set(request.request_id, resolve as (value: unknown) => void);
      this.failures.set(request.request_id, reject);
    });
    await this.child.write(`${JSON.stringify(request)}\n`);
    return response;
  }

  async close(): Promise<void> {
    if (this.child) await this.child.kill();
    this.child = null;
    this.rejectAll(new Error("sidecar closed"));
  }

  private consume(chunk: string): void {
    this.buffer += chunk;
    const lines = this.buffer.split("\n");
    this.buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.trim()) continue;
      const response = JSON.parse(line) as SidecarResponse<unknown>;
      const resolve = this.pending.get(response.request_id);
      const reject = this.failures.get(response.request_id);
      this.pending.delete(response.request_id);
      this.failures.delete(response.request_id);
      if (!resolve || !reject) continue;
      if (response.ok) resolve(response.result);
      else reject(new Error(response.error?.safe_message ?? "sidecar request failed"));
    }
  }

  private rejectAll(error: Error): void {
    for (const reject of this.failures.values()) reject(error);
    this.pending.clear();
    this.failures.clear();
  }
}

export class MockSidecarTransport implements SidecarTransport {
  private readonly state: {
    sequence: number;
    jobs: JobState[];
    events: Array<import("./protocol").JobEvent>;
  };
  readonly requests: Array<{ method: string; params: Record<string, unknown> }> = [];

  constructor(state = { sequence: 0, jobs: [] as JobState[], events: [] as Array<import("./protocol").JobEvent> }) {
    this.state = state;
  }

  async start(_configPath: string): Promise<void> {
    this.requests.push({ method: "start", params: {} });
  }

  async request<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
    this.requests.push({ method, params });
    if (method === "list_jobs") return { jobs: this.state.jobs } as T;
    if (method === "poll_events") {
      const afterSequence = Number(params.after_sequence ?? 0);
      return {
        events: this.state.events.filter((event) => event.sequence > afterSequence),
        next_sequence: this.state.sequence,
      } as T;
    }
    if (method === "start_translation") {
      const job: JobState = {
        job_id: `mock-job-${this.state.jobs.length + 1}`,
        source_path: String(params.source_path ?? "sample.pdf"),
        status: "running",
        stage: "preparing_runtime",
        attempts: 1,
        safe_error_message: null,
        updated_at: new Date().toISOString(),
        completed_at: "",
      };
      this.state.jobs = [job, ...this.state.jobs];
      this.emit("job_created", job.job_id, { status: job.status, source_path: job.source_path });
      this.emit("status_changed", job.job_id, { status: job.status });
      return { job_id: job.job_id, status: job.status } as T;
    }
    if (method === "cancel_job") {
      const jobId = String(params.job_id ?? "");
      const job = this.state.jobs.find((candidate) => candidate.job_id === jobId);
      if (job && job.status === "running") {
        job.status = "cancelled";
        this.emit("status_changed", jobId, { status: "cancel_requested" });
        this.emit("status_changed", jobId, { status: "cancelled" });
      }
      return { job_id: jobId, cancelled: Boolean(job), status: job?.status ?? null } as T;
    }
    if (method === "get_job") {
      const jobId = String(params.job_id ?? "");
      const job = this.state.jobs.find((candidate) => candidate.job_id === jobId) ?? null;
      return {
        job: job
          ? {
              ...job,
              backend_name: "mock-babeldoc",
              translator_name: "mock",
              model: "mock-local",
              started_at: job.started_at || job.updated_at,
              artifacts: job.status === "cancelled" ? [] : [
                {
                  artifact_type: "mono_pdf",
                  path: `/workspace/translated/${job.job_id}.mono.pdf`,
                  size: 24832,
                  sha256: "mock-sha256",
                  created_at: job.updated_at,
                  validated: true,
                },
              ],
              qa_status: job.status === "completed" ? "passed" : "pending",
            }
          : null,
      } as T;
    }
    if (method === "list_glossary") {
      return {
        scope: String(params.scope ?? "global"),
        document_id: params.document_id ? String(params.document_id) : null,
        entries: [],
        version: null,
      } as T;
    }
    if (method === "save_glossary") {
      return {
        scope: String(params.scope ?? "global"),
        document_id: params.document_id ? String(params.document_id) : null,
        entries: (params.entries ?? []) as unknown[],
        version: "mock-glossary-version",
      } as T;
    }
    if (method === "get_context") {
      return {
        document_id: String(params.document_id ?? ""),
        text: "",
        title: "",
        abstract: "",
        version: null,
      } as T;
    }
    if (method === "save_context") {
      return {
        document_id: String(params.document_id ?? ""),
        text: String(params.text ?? ""),
        title: "",
        abstract: "",
        version: "mock-context-version",
      } as T;
    }
    if (method === "shutdown") return { closing: true } as T;
    return {} as T;
  }

  async close(): Promise<void> {
    this.requests.push({ method: "close", params: {} });
  }

  private emit(
    event_type: import("./protocol").JobEvent["event_type"],
    job_id: string,
    payload: Record<string, unknown>,
  ): void {
    this.state.sequence += 1;
    this.state.events.push({
      event_type,
      job_id,
      sequence: this.state.sequence,
      timestamp: new Date().toISOString(),
      payload,
    });
  }
}

export const createSidecarTransport = (): SidecarTransport => {
  const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
  return isTauri ? new TauriSidecarTransport() : new MockSidecarTransport();
};

export { PROTOCOL_VERSION };
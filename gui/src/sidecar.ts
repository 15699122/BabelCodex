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
  private sequence = 0;
  private jobs: JobState[] = [];
  readonly requests: Array<{ method: string; params: Record<string, unknown> }> = [];

  async request<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
    this.requests.push({ method, params });
    if (method === "list_jobs") return { jobs: this.jobs } as T;
    if (method === "poll_events") {
      return { events: [], next_sequence: this.sequence } as T;
    }
    if (method === "start_translation") {
      const job: JobState = {
        job_id: `mock-job-${this.jobs.length + 1}`,
        source_path: String(params.source_path ?? "sample.pdf"),
        status: "running",
        stage: "preparing_runtime",
        attempts: 1,
        safe_error_message: null,
        updated_at: new Date().toISOString(),
        completed_at: "",
      };
      this.jobs = [job, ...this.jobs];
      return { job_id: job.job_id, status: job.status } as T;
    }
    if (method === "shutdown") return { closing: true } as T;
    return {} as T;
  }

  async close(): Promise<void> {
    this.requests.push({ method: "close", params: {} });
  }
}

export const createSidecarTransport = (): SidecarTransport => {
  const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
  return isTauri ? new TauriSidecarTransport() : new MockSidecarTransport();
};

export { PROTOCOL_VERSION };
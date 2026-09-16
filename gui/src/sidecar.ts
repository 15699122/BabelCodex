import { Command, Child } from "@tauri-apps/plugin-shell";
import {
  JobState,
  makeRequest,
  PROTOCOL_VERSION,
  ServerInfo,
  SidecarResponse,
  SidecarTransport,
  assertCompatibleServerInfo,
} from "./protocol";

const SIDECAR_PROGRAM = "binaries/babelcodex-service";

export const E2E_MOCK_STATE_KEY = "babelcodex:e2e:mock-state";

type MockSidecarState = {
  sequence: number;
  jobs: JobState[];
  events: Array<import("./protocol").JobEvent>;
};

const createMockState = (): MockSidecarState => ({
  sequence: 0,
  jobs: [],
  events: [],
});

const loadE2EMockState = (): MockSidecarState => {
  if (typeof window === "undefined") return createMockState();
  try {
    const raw = window.localStorage.getItem(E2E_MOCK_STATE_KEY);
    if (!raw) return createMockState();
    const parsed = JSON.parse(raw) as Partial<MockSidecarState>;
    if (
      typeof parsed.sequence !== "number" ||
      !Array.isArray(parsed.jobs) ||
      !Array.isArray(parsed.events)
    ) {
      return createMockState();
    }
    return {
      sequence: parsed.sequence,
      jobs: parsed.jobs as JobState[],
      events: parsed.events as Array<import("./protocol").JobEvent>,
    };
  } catch {
    return createMockState();
  }
};

const isE2EInputPath = (candidate: string): boolean => {
  const normalized = candidate.replaceAll("\\", "/");
  return /(?:^|\/)build\/e2e\/incoming\/[^/]+\.pdf$/i.test(normalized);
};

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
    // Runtime handshake: reject a stale frozen sidecar with an explicit
    // rebuild hint before any job operation can silently misbehave.
    try {
      const info = await this.request<ServerInfo>("get_server_info");
      assertCompatibleServerInfo(info);
    } catch (error) {
      await this.close();
      throw error;
    }
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
  private readonly state: MockSidecarState;
  readonly requests: Array<{ method: string; params: Record<string, unknown> }> = [];

  constructor(state: MockSidecarState = createMockState(), private readonly persistState = false) {
    this.state = state;
  }

  async start(_configPath: string): Promise<void> {
    this.requests.push({ method: "start", params: {} });
    // Mirror the real transport's startup handshake in dev/test mode so stale
    // sidecars fail fast outside of packaged Tauri runs as well.
    const info = await this.request<ServerInfo>("get_server_info");
    assertCompatibleServerInfo(info);
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
      const sourcePath = String(params.source_path ?? "");
      if (this.persistState && !isE2EInputPath(sourcePath)) {
        throw new Error("source_path is outside the configured input directory");
      }
      const job: JobState = {
        job_id: `mock-job-${this.state.jobs.length + 1}`,
        source_path: sourcePath || "sample.pdf",
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
    if (method === "retry_job") {
      const jobId = String(params.job_id ?? "");
      const job = this.state.jobs.find((candidate) => candidate.job_id === jobId);
      if (!job) throw new Error("job was not found");
      job.status = "running";
      job.attempts += 1;
      job.safe_error_message = null;
      this.emit("status_changed", jobId, { status: job.status });
      return { job_id: jobId, status: job.status } as T;
    }
    if (method === "validate_output") {
      const jobId = String(params.job_id ?? "");
      return { job_id: jobId, validated: true, qa_status: "passed", artifacts: [] } as T;
    }
    if (method === "run_qa") {
      const jobId = String(params.job_id ?? "");
      return { job_id: jobId, qa_status: "passed", ok: true, reports: [] } as T;
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
                  path: `${job.job_id}.mono.pdf`,
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
    if (method === "get_runtime_layout") {
      return {
        portable_root: ".",
        paths: {
          root: ".",
          config: "config",
          cache: "cache",
          incoming: "cache/incoming",
          state: "cache/state",
          logs: "logs",
          output: "output",
          resource: "resource",
          babeldoc_cache: "cache/babeldoc",
        },
        output_exists: true,
        output_configured: "output",
      } as T;
    }
    if (method === "get_settings") {
      return {
        logging: { level: "info", max_files: 5 },
        output_dir: "output",
        input_dir: "cache/incoming",
        requires_restart: false,
      } as T;
    }
    if (method === "save_settings") {
      return {
        logging: (params.settings as { logging?: unknown } | undefined)?.logging ?? { level: "info", max_files: 5 },
        output_dir: "output",
        input_dir: "cache/incoming",
        requires_restart: true,
        saved_path: "config/config.yaml",
      } as T;
    }
    if (method === "prepare_output_directory") {
      const confirmed = Boolean(params.confirmed);
      return {
        configured_path: "output",
        exists: confirmed,
        created: confirmed,
        requires_confirmation: !confirmed,
        fallback_path: "Downloads",
      } as T;
    }
    if (method === "stage_input") {
      const sourcePath = String(params.source_path ?? "sample.pdf");
      return { source_path: sourcePath, display_name: sourcePath.split(/[\\/]/).pop() ?? "sample.pdf", size: 0 } as T;
    }
    if (method === "get_latest_log") return { path: null, text: "" } as T;
    if (method === "get_server_info") {
      return {
        protocol_version: PROTOCOL_VERSION,
        package_version: "mock-babelcodex",
        capabilities: [
          "start_translation",
          "get_job",
          "list_jobs",
          "cancel_job",
          "retry_job",
          "validate_output",
          "run_qa",
          "poll_events",
          "list_glossary",
          "save_glossary",
          "get_context",
          "save_context",
          "get_server_info",
          "get_runtime_layout",
          "prepare_output_directory",
          "get_settings",
          "save_settings",
          "stage_input",
          "get_latest_log",
          "shutdown",
        ],
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
    if (
      this.persistState &&
      typeof window !== "undefined" &&
      window.localStorage
    ) {
      window.localStorage.setItem(E2E_MOCK_STATE_KEY, JSON.stringify(this.state));
    }
  }
}

export const createSidecarTransport = (): SidecarTransport => {
  const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
  const isE2E = import.meta.env.VITE_E2E === "1";
  // @wdio/tauri-service injects an invoke spy into the WebView. In the
  // current 1.4.x embedded driver it does not transparently pass through
  // plugin-shell calls, so GUI E2E uses a persistent deterministic transport.
  // The frozen Windows sidecar remains covered by the separate protocol
  // handshake/start/shutdown check in the Windows validation procedure.
  if (isE2E) return new MockSidecarTransport(loadE2EMockState(), true);
  return isTauri ? new TauriSidecarTransport() : new MockSidecarTransport();
};

export { PROTOCOL_VERSION };
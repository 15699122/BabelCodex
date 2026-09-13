export const PROTOCOL_VERSION = 1;

export type JobStatus =
  | "discovered"
  | "running"
  | "retry_pending"
  | "completed"
  | "failed"
  | "cancelled";

export type JobStage =
  | "discovered"
  | "validating_input"
  | "preparing_runtime"
  | "translating"
  | "rendering"
  | "validating_output"
  | "completed";

export interface Artifact {
  artifact_type: string;
  path: string;
  size: number;
  sha256?: string;
  created_at?: string;
  validated?: boolean;
}

export interface QaResult {
  job_id: string;
  qa_status: string;
  ok: boolean;
  reports: Array<{
    artifact: string;
    ok: boolean;
    path: string;
    report?: string;
    summary: string;
  }>;
}

export interface JobState {
  job_id: string;
  source_path: string;
  status: JobStatus;
  stage: JobStage;
  attempts: number;
  safe_error_message: string | null;
  updated_at: string;
  completed_at: string;
  source_fingerprint?: string;
  config_fingerprint?: string;
  schema_version?: number;
  error_category?: string | null;
  error_code?: string | null;
  backend_name?: string;
  backend_version?: string;
  translator_name?: string;
  model?: string;
  codex_thread_id?: string | null;
  invocation_source?: string;
  started_at?: string;
  artifacts?: Artifact[];
  qa_status?: string;
}

export interface JobEvent {
  event_type:
    | "job_created"
    | "status_changed"
    | "progress"
    | "job_failed"
    | "job_completed"
    | "artifact_created";
  job_id: string;
  sequence: number;
  timestamp: string;
  payload: Record<string, unknown>;
}

export interface SidecarResponse<T> {
  type: "response";
  request_id: string;
  ok: boolean;
  result?: T;
  error?: {
    category: string;
    code: string;
    safe_message: string;
    retryable: boolean;
  };
}

export interface PollEventsResult {
  events: JobEvent[];
  next_sequence: number;
  oldest_sequence?: number;
}

export interface ServerInfo {
  protocol_version: number;
  package_version: string;
  capabilities: string[];
}

/**
 * Fail fast when the bundled sidecar was built from older sources.
 *
 * A stale frozen sidecar can silently speak an incompatible protocol or config
 * schema; turning that into an explicit startup error points the user at the
 * rebuild step instead of unexplained job failures.
 */
export const assertCompatibleServerInfo = (info: ServerInfo): void => {
  if (info.protocol_version !== PROTOCOL_VERSION) {
    throw new Error(
      `sidecar protocol mismatch: sidecar speaks v${info.protocol_version}, ` +
        `GUI expects v${PROTOCOL_VERSION}. Rebuild the bundled babelcodex-service ` +
        `sidecar (reported package version: ${info.package_version}).`,
    );
  }
};

export interface SidecarTransport {
  start(configPath: string): Promise<void>;
  request<T>(method: string, params?: Record<string, unknown>): Promise<T>;
  close(): Promise<void>;
}

export const makeRequest = (method: string, params: Record<string, unknown> = {}) => ({
  protocol_version: PROTOCOL_VERSION,
  request_id: crypto.randomUUID(),
  method,
  ...params,
});
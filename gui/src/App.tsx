import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, ArrowUpRight, BookOpen, FolderOpen, Gauge, Library, Settings2, ShieldCheck } from "lucide-react";
import { createFilePicker, isTauriRuntime } from "./filePicker";
import { isActiveJob, JobStore } from "./jobStore";
import type { Artifact, JobState } from "./protocol";

type View = "new" | "jobs" | "details" | "diagnostics" | "settings";

function App() {
  const [view, setView] = useState<View>("new");
  const [sourcePath, setSourcePath] = useState("");
  const store = useMemo(() => new JobStore(), []);
  const [snapshot, setSnapshot] = useState(() => store.getSnapshot());
  const [cancelling, setCancelling] = useState<string | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const filePicker = useMemo(() => createFilePicker(), []);

  useEffect(() => {
    const unsubscribe = store.subscribe(setSnapshot);
    void store.connect().catch(() => undefined);
    return () => {
      unsubscribe();
      void store.close();
    };
  }, [store]);

  const jobs = snapshot.jobs;

  const startTranslation = async () => {
    if (!sourcePath.trim()) {
      setSnapshot((current) => ({
        ...current,
        notice: "Choose a PDF inside the configured input folder first.",
      }));
      return;
    }
    try {
      const jobId = await store.startTranslation(sourcePath.trim());
      setView("jobs");
      setSnapshot((current) => ({ ...current, notice: `Started ${jobId}` }));
    } catch (error) {
      setSnapshot((current) => ({
        ...current,
        notice: error instanceof Error ? error.message : "Unable to start translation",
      }));
    }
  };

  const applyPickedPdf = (picked: { path: string; displayName: string } | null) => {
    if (!picked) return;
    setSourcePath(picked.path);
    setSnapshot((current) => ({ ...current, notice: `Selected ${picked.displayName}` }));
  };

  const pickPdf = async () => {
    try {
      if (!isTauriRuntime()) {
        fileInputRef.current?.click();
        return;
      }
      applyPickedPdf(await filePicker.pickPdf());
    } catch (error) {
      setSnapshot((current) => ({
        ...current,
        notice: error instanceof Error ? error.message : "Unable to open file picker",
      }));
    }
  };

  const handleBrowserFile = (file: File | undefined) => {
    if (!file) return;
    const picked = filePicker.fromBrowserFile(file);
    if (!picked) {
      setSnapshot((current) => ({ ...current, notice: "Choose a PDF file." }));
      return;
    }
    applyPickedPdf(picked);
  };

  const cancelJob = async (jobId: string) => {
    setCancelling(jobId);
    try {
      await store.cancel(jobId);
    } catch (error) {
      setSnapshot((current) => ({
        ...current,
        notice: error instanceof Error ? error.message : "Unable to cancel job",
      }));
    } finally {
      setCancelling(null);
    }
  };

  const openJobDetails = async (jobId: string) => {
    setSelectedJobId(jobId);
    setView("details");
    await store.getJob(jobId).catch((error) => {
      setSnapshot((current) => ({
        ...current,
        notice: error instanceof Error ? error.message : "Unable to load job details",
      }));
    });
  };

  return (
    <main className="app-shell">
      <aside className="rail">
        <div className="brand-mark" aria-label="BabelCodex home">BC<span>/</span></div>
        <nav className="nav-stack" aria-label="Primary navigation">
          <NavButton active={view === "new"} icon={<ArrowUpRight size={17} />} label="New translation" onClick={() => setView("new")} />
          <NavButton active={view === "jobs"} icon={<Activity size={17} />} label="Jobs" count={jobs.length} onClick={() => setView("jobs")} />
          <NavButton active={view === "diagnostics"} icon={<Gauge size={17} />} label="Diagnostics" onClick={() => setView("diagnostics")} />
          <NavButton active={view === "settings"} icon={<Settings2 size={17} />} label="Settings" onClick={() => setView("settings")} />
        </nav>
        <div className="rail-footer"><ShieldCheck size={15} /> local-only</div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div><span className="eyebrow">BABELCODEX / DESKTOP ALPHA</span><h1>{view === "new" ? "New translation" : view[0].toUpperCase() + view.slice(1)}</h1></div>
          <div className="connection"><span className="pulse" /> {snapshot.notice}</div>
        </header>

        {view === "new" && <NewTranslation sourcePath={sourcePath} setSourcePath={setSourcePath} onStart={startTranslation} onPickPdf={pickPdf} onBrowserFile={handleBrowserFile} fileInputRef={fileInputRef} />}
        {view === "jobs" && <Jobs jobs={jobs} onCancel={cancelJob} cancelling={cancelling} onOpen={openJobDetails} />}
        {view === "details" && selectedJobId && <JobDetails job={jobs.find((candidate) => candidate.job_id === selectedJobId) ?? null} onBack={() => setView("jobs")} onCancel={cancelJob} cancelling={cancelling} />}
        {view === "diagnostics" && <Diagnostics connection={snapshot.connection} onReconnect={() => void store.reconnect()} />}
        {view === "settings" && <Settings />}
      </section>
    </main>
  );
}

function NavButton({ active, icon, label, count, onClick }: { active: boolean; icon: React.ReactNode; label: string; count?: number; onClick: () => void }) {
  return <button className={`nav-item ${active ? "active" : ""}`} onClick={onClick}>{icon}<span>{label}</span>{count !== undefined && <b>{count}</b>}</button>;
}

function NewTranslation({ sourcePath, setSourcePath, onStart, onPickPdf, onBrowserFile, fileInputRef }: { sourcePath: string; setSourcePath: (value: string) => void; onStart: () => void; onPickPdf: () => void; onBrowserFile: (file: File | undefined) => void; fileInputRef: React.RefObject<HTMLInputElement | null> }) {
  return <div className="page-grid reveal">
    <div className="hero-panel">
      <div className="hero-kicker">01 / DOCUMENT INTAKE</div>
      <h2>Turn a paper into<br /><em>a readable room.</em></h2>
      <p>BabelDOC protects the page. Codex carries the meaning. Start with one PDF and keep every formula, link, and column in its place.</p>
      <div className="metric-row"><div><strong>01</strong><span>PDF at a time</span></div><div><strong>100%</strong><span>local orchestration</span></div><div><strong>JSONL</strong><span>sidecar protocol</span></div></div>
    </div>
    <div className="intake-card card">
      <div className="card-label"><FolderOpen size={16} /> SOURCE PDF</div>
      <label htmlFor="source-path">Input path</label>
      <div className="path-input-row"><input id="source-path" value={sourcePath} onChange={(event) => setSourcePath(event.target.value)} placeholder="/input/folder/research-paper.pdf" /><button className="browse-action" type="button" onClick={onPickPdf}>Browse</button></div>
      <input ref={fileInputRef} className="visually-hidden" type="file" accept="application/pdf,.pdf" onChange={(event) => onBrowserFile(event.target.files?.[0])} />
      <div className="drop-zone" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); onBrowserFile(event.dataTransfer.files[0]); }}><BookOpen size={25} /><span>Drop a PDF here</span><small>or browse / paste an allowlisted path above</small></div>
      <div className="field-pair"><div><label>From</label><div className="select-like">English <span>⌄</span></div></div><div><label>To</label><div className="select-like">简体中文 <span>⌄</span></div></div></div>
      <button className="primary-action" onClick={onStart}>Queue translation <ArrowUpRight size={17} /></button>
      <div className="safe-note"><ShieldCheck size={14} /> Files stay inside your configured workspace.</div>
    </div>
  </div>;
}

function Jobs({ jobs, onCancel, cancelling, onOpen }: { jobs: JobState[]; onCancel: (jobId: string) => void; cancelling: string | null; onOpen: (jobId: string) => void }) {
  return <div className="content-column reveal"><div className="section-heading"><div><span className="eyebrow">WORK QUEUE / 02</span><h2>Recent jobs</h2></div><span className="queue-badge">{jobs.filter(isActiveJob).length} active</span></div><div className="job-list">{jobs.length === 0 && <div className="empty-state">No translations yet. Queue a PDF from New translation.</div>}{jobs.map((job) => <article className="job-row" key={job.job_id}><button className="job-open" aria-label={`Open details for ${job.job_id}`} onClick={() => onOpen(job.job_id)}><div className={`status-dot ${job.status}`} /><div className="job-main"><strong>{job.source_path.split("/").pop()}</strong><span>{job.job_id} · {job.stage.replaceAll("_", " ")}</span>{job.safe_error_message && <small className="job-error">{job.safe_error_message}</small>}</div><div className="job-progress">{isActiveJob(job) ? <><div className="progress-track"><span style={{ width: job.status === "running" ? "68%" : "22%" }} /></div><small>{job.status.replaceAll("_", " ")}</small></> : <span className="done-label">{job.status}</span>}</div></button>{isActiveJob(job) ? <button className="cancel-action" disabled={cancelling === job.job_id} onClick={() => onCancel(job.job_id)}>{cancelling === job.job_id ? "stopping" : "cancel"}</button> : <ArrowUpRight size={17} className="muted-icon" />}</article>)}</div></div>;
}

function JobDetails({ job, onBack, onCancel, cancelling }: { job: JobState | null; onBack: () => void; onCancel: (jobId: string) => void; cancelling: string | null }) {
  if (!job) return <div className="content-column reveal"><button className="back-action" onClick={onBack}>← Back to jobs</button><div className="empty-state">This job is no longer available.</div></div>;
  const artifacts = job.artifacts ?? [];
  return <div className="content-column reveal"><div className="section-heading"><div><button className="back-action" onClick={onBack}>← Back to jobs</button><span className="eyebrow">JOB DETAIL / 02</span><h2>{job.source_path.split("/").pop()}</h2></div><div className={`detail-status ${job.status}`}>{job.status.replaceAll("_", " ")}</div></div><div className="detail-grid"><section className="detail-card card"><span className="card-label">RUN STATE</span><div className="detail-facts"><Fact label="Job ID" value={job.job_id} /><Fact label="Stage" value={job.stage.replaceAll("_", " ")} /><Fact label="Attempts" value={String(job.attempts)} /><Fact label="QA" value={job.qa_status ?? "pending"} /><Fact label="Backend" value={job.backend_name || "not reported"} /><Fact label="Translator" value={job.translator_name || "not reported"} /><Fact label="Started" value={formatDate(job.started_at)} /><Fact label="Updated" value={formatDate(job.updated_at)} /></div>{job.safe_error_message && <div className="detail-error">{job.safe_error_message}</div>}{isActiveJob(job) && <button className="cancel-action detail-cancel" disabled={cancelling === job.job_id} onClick={() => onCancel(job.job_id)}>{cancelling === job.job_id ? "stopping" : "cancel job"}</button>}</section><section className="detail-card card"><span className="card-label">OUTPUT ARTIFACTS</span>{artifacts.length === 0 ? <div className="empty-state">No output artifacts reported yet.</div> : <div className="artifact-list">{artifacts.map((artifact) => <ArtifactRow artifact={artifact} key={`${artifact.artifact_type}-${artifact.path}`} />)}</div>}</section></div></div>;
}

function Fact({ label, value }: { label: string; value: string }): React.ReactElement { return <div><span>{label}</span><strong>{value}</strong></div>; }
function ArtifactRow({ artifact }: { artifact: Artifact }): React.ReactElement { return <div className="artifact-row"><div><strong>{artifact.artifact_type.replaceAll("_", " ")}</strong><span>{artifact.path}</span></div><div><small>{formatBytes(artifact.size)}</small><small className={artifact.validated ? "validated" : "pending"}>{artifact.validated ? "validated" : "pending"}</small></div></div>; }
function formatDate(value?: string): string { if (!value) return "not recorded"; const date = new Date(value); return Number.isNaN(date.valueOf()) ? value : date.toLocaleString(); }
function formatBytes(value: number): string { if (value < 1024) return `${value} B`; if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`; return `${(value / (1024 * 1024)).toFixed(1)} MB`; }

function Diagnostics({ connection, onReconnect }: { connection: { status: string }; onReconnect: () => void }) { return <div className="content-column reveal"><div className="section-heading"><div><span className="eyebrow">SYSTEM CHECK / 03</span><h2>Quiet confidence</h2></div><button className="reconnect-action" onClick={onReconnect}>reconnect</button></div><div className="diagnostic-grid"><Diagnostic icon={<ShieldCheck />} title="Path allowlist" value="Enforced" detail="Input PDFs are scoped to the configured directory." /><Diagnostic icon={<Activity />} title="Sidecar protocol" value={connection.status === "ready" ? "v1 online" : connection.status} detail="JSONL request / response transport is available." /><Diagnostic icon={<Library />} title="Codex session" value="Not checked" detail="Live authentication is only used when a translation starts." /></div></div>; }
function Diagnostic({ icon, title, value, detail }: { icon: React.ReactNode; title: string; value: string; detail: string }) { return <div className="diag-card card">{icon}<span className="eyebrow">{title}</span><strong>{value}</strong><p>{detail}</p></div>; }
function Settings() { return <div className="content-column reveal"><div className="section-heading"><div><span className="eyebrow">RUNTIME / 04</span><h2>Settings</h2></div></div><div className="settings-card card"><div><span>Input directory</span><strong>configured in config.toml</strong></div><div><span>Translation mode</span><strong>Codex SDK · per-document thread</strong></div><div><span>Worker mode</span><strong>single-pass subprocess</strong></div></div></div>; }

export default App;
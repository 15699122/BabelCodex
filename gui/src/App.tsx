import { useEffect, useMemo, useState } from "react";
import { Activity, ArrowUpRight, BookOpen, FolderOpen, Gauge, Library, Settings2, ShieldCheck } from "lucide-react";
import { isActiveJob, JobStore } from "./jobStore";
import type { JobState } from "./protocol";

type View = "new" | "jobs" | "diagnostics" | "settings";

function App() {
  const [view, setView] = useState<View>("new");
  const [sourcePath, setSourcePath] = useState("");
  const store = useMemo(() => new JobStore(), []);
  const [snapshot, setSnapshot] = useState(() => store.getSnapshot());
  const [cancelling, setCancelling] = useState<string | null>(null);

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

        {view === "new" && <NewTranslation sourcePath={sourcePath} setSourcePath={setSourcePath} onStart={startTranslation} />}
        {view === "jobs" && <Jobs jobs={jobs} onCancel={cancelJob} cancelling={cancelling} />}
        {view === "diagnostics" && <Diagnostics connection={snapshot.connection} onReconnect={() => void store.reconnect()} />}
        {view === "settings" && <Settings />}
      </section>
    </main>
  );
}

function NavButton({ active, icon, label, count, onClick }: { active: boolean; icon: React.ReactNode; label: string; count?: number; onClick: () => void }) {
  return <button className={`nav-item ${active ? "active" : ""}`} onClick={onClick}>{icon}<span>{label}</span>{count !== undefined && <b>{count}</b>}</button>;
}

function NewTranslation({ sourcePath, setSourcePath, onStart }: { sourcePath: string; setSourcePath: (value: string) => void; onStart: () => void }) {
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
      <input id="source-path" value={sourcePath} onChange={(event) => setSourcePath(event.target.value)} placeholder="/input/folder/research-paper.pdf" />
      <div className="drop-zone"><BookOpen size={25} /><span>Drop a PDF here</span><small>or paste an allowlisted path above</small></div>
      <div className="field-pair"><div><label>From</label><div className="select-like">English <span>⌄</span></div></div><div><label>To</label><div className="select-like">简体中文 <span>⌄</span></div></div></div>
      <button className="primary-action" onClick={onStart}>Queue translation <ArrowUpRight size={17} /></button>
      <div className="safe-note"><ShieldCheck size={14} /> Files stay inside your configured workspace.</div>
    </div>
  </div>;
}

function Jobs({ jobs, onCancel, cancelling }: { jobs: JobState[]; onCancel: (jobId: string) => void; cancelling: string | null }) {
  return <div className="content-column reveal"><div className="section-heading"><div><span className="eyebrow">WORK QUEUE / 02</span><h2>Recent jobs</h2></div><span className="queue-badge">{jobs.filter(isActiveJob).length} active</span></div><div className="job-list">{jobs.length === 0 && <div className="empty-state">No translations yet. Queue a PDF from New translation.</div>}{jobs.map((job) => <article className="job-row" key={job.job_id}><div className={`status-dot ${job.status}`} /><div className="job-main"><strong>{job.source_path.split("/").pop()}</strong><span>{job.job_id} · {job.stage.replaceAll("_", " ")}</span>{job.safe_error_message && <small className="job-error">{job.safe_error_message}</small>}</div><div className="job-progress">{isActiveJob(job) ? <><div className="progress-track"><span style={{ width: job.status === "running" ? "68%" : "22%" }} /></div><small>{job.status.replaceAll("_", " ")}</small></> : <span className="done-label">{job.status}</span>}</div>{isActiveJob(job) ? <button className="cancel-action" disabled={cancelling === job.job_id} onClick={() => onCancel(job.job_id)}>{cancelling === job.job_id ? "stopping" : "cancel"}</button> : <ArrowUpRight size={17} className="muted-icon" />}</article>)}</div></div>;
}

function Diagnostics({ connection, onReconnect }: { connection: { status: string }; onReconnect: () => void }) { return <div className="content-column reveal"><div className="section-heading"><div><span className="eyebrow">SYSTEM CHECK / 03</span><h2>Quiet confidence</h2></div><button className="reconnect-action" onClick={onReconnect}>reconnect</button></div><div className="diagnostic-grid"><Diagnostic icon={<ShieldCheck />} title="Path allowlist" value="Enforced" detail="Input PDFs are scoped to the configured directory." /><Diagnostic icon={<Activity />} title="Sidecar protocol" value={connection.status === "ready" ? "v1 online" : connection.status} detail="JSONL request / response transport is available." /><Diagnostic icon={<Library />} title="Codex session" value="Not checked" detail="Live authentication is only used when a translation starts." /></div></div>; }
function Diagnostic({ icon, title, value, detail }: { icon: React.ReactNode; title: string; value: string; detail: string }) { return <div className="diag-card card">{icon}<span className="eyebrow">{title}</span><strong>{value}</strong><p>{detail}</p></div>; }
function Settings() { return <div className="content-column reveal"><div className="section-heading"><div><span className="eyebrow">RUNTIME / 04</span><h2>Settings</h2></div></div><div className="settings-card card"><div><span>Input directory</span><strong>configured in config.toml</strong></div><div><span>Translation mode</span><strong>Codex SDK · per-document thread</strong></div><div><span>Worker mode</span><strong>single-pass subprocess</strong></div></div></div>; }

export default App;
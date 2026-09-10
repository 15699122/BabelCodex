import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, ArrowUpRight, BookOpen, CheckCircle2, FolderOpen, Gauge, Library, RefreshCw, Settings2, ShieldCheck } from "lucide-react";
import { createFilePicker, isTauriRuntime } from "./filePicker";
import { isActiveJob, JobStore } from "./jobStore";
import type { ContextResult, GlossaryEntry, GlossaryResult } from "./jobStore";
import type { JobState } from "./protocol";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardHeader } from "./components/ui/card";
import { Progress } from "./components/ui/progress";

type View = "new" | "jobs" | "details" | "glossary" | "diagnostics" | "settings";

function App() {
  const [view, setView] = useState<View>("new");
  const [sourcePath, setSourcePath] = useState("");
  const store = useMemo(() => new JobStore(), []);
  const [snapshot, setSnapshot] = useState(() => store.getSnapshot());
  const [cancelling, setCancelling] = useState<string | null>(null);
  const [refreshingJob, setRefreshingJob] = useState<string | null>(null);
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
        notice: "请先选择配置输入目录中的 PDF 文件。",
      }));
      return;
    }
    try {
      const jobId = await store.startTranslation(sourcePath.trim());
      setView("jobs");
      setSnapshot((current) => ({ ...current, notice: `已加入翻译队列：${jobId}` }));
    } catch (error) {
      setSnapshot((current) => ({
        ...current,
        notice: error instanceof Error ? error.message : "无法开始翻译。",
      }));
    }
  };

  const applyPickedPdf = (picked: { path: string; displayName: string } | null) => {
    if (!picked) return;
    setSourcePath(picked.path);
    setSnapshot((current) => ({ ...current, notice: `已选择：${picked.displayName}` }));
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
        notice: error instanceof Error ? error.message : "无法打开文件选择器。",
      }));
    }
  };

  const handleBrowserFile = (file: File | undefined) => {
    if (!file) return;
    const picked = filePicker.fromBrowserFile(file);
    if (!picked) {
      setSnapshot((current) => ({ ...current, notice: "请选择 PDF 文件。" }));
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
        notice: error instanceof Error ? error.message : "无法取消任务。",
      }));
    } finally {
      setCancelling(null);
    }
  };

  const refreshJob = async (jobId: string) => {
    setRefreshingJob(jobId);
    try {
      await store.refreshJob(jobId);
    } catch (error) {
      setSnapshot((current) => ({
        ...current,
        notice: error instanceof Error ? error.message : "无法刷新任务。",
      }));
    } finally {
      setRefreshingJob(null);
    }
  };

  const openJob = (jobId: string) => {
    setSelectedJobId(jobId);
    setView("details");
  };

  const reconnect = () => {
    void store.connect().catch(() => undefined);
  };

  const connectionStatus = snapshot.connection.status;

  return (
    <div className="app-shell">
      <nav className="rail">
        <div className="brand-mark">
          <ShieldCheck size={18} />
          <span>BabelCodex <small>本地 PDF 翻译</small></span>
        </div>
        <div className="nav-stack">
          <Button variant={view === "new" ? "default" : "ghost"} onClick={() => setView("new")} aria-current={view === "new"}>
            <FolderOpen size={16} /> 新建翻译
          </Button>
          <Button variant={view === "jobs" ? "default" : "ghost"} onClick={() => setView("jobs")} aria-current={view === "jobs"}>
            <Activity size={16} /> 翻译任务
          </Button>
          <Button variant={view === "glossary" ? "default" : "ghost"} onClick={() => setView("glossary")} aria-current={view === "glossary"}>
            <BookOpen size={16} /> 术语与上下文
          </Button>
          <Button variant={view === "diagnostics" ? "default" : "ghost"} onClick={() => setView("diagnostics")} aria-current={view === "diagnostics"}>
            <Gauge size={16} /> 运行诊断
          </Button>
          <Button variant={view === "settings" ? "default" : "ghost"} onClick={() => setView("settings")} aria-current={view === "settings"}>
            <Settings2 size={16} /> 设置
          </Button>
        </div>
        <div className="rail-footer">
          <div className="safe-note">本地优先处理 PDF<br />文档保留在当前运行环境</div>
        </div>
      </nav>

      <main className="workspace">
        <div className="topbar">
          <div />
          <div className="connection" data-status={connectionStatus} aria-live="polite">
            <span className="pulse" aria-hidden="true" />
            <span>{connectionStatus === "ready" ? "本地服务已连接" : connectionStatus === "starting" ? "正在连接本地服务" : connectionStatus === "reconnecting" ? "正在重新连接" : "本地服务不可用"}</span>
          </div>
        </div>

        {snapshot.notice && (
          <div className="notice-banner" role="status" aria-live="polite">
            <span>{snapshot.notice}</span>
            <Button variant="ghost" size="sm" aria-label="关闭提示" onClick={() => setSnapshot((current) => ({ ...current, notice: "" }))}>×</Button>
          </div>
        )}
        {view === "new" && <NewTranslation sourcePath={sourcePath} onPickPdf={pickPdf} onBrowserFile={handleBrowserFile} onStart={() => void startTranslation()} fileInputRef={fileInputRef} />}
        {view === "jobs" && <Jobs jobs={jobs} cancelling={cancelling} refreshingJob={refreshingJob} onOpen={openJob} onCancel={(id) => void cancelJob(id)} onRefresh={(id) => void refreshJob(id)} />}
        {view === "details" && <JobDetails jobId={selectedJobId} onBack={() => setView("jobs")} />}
        {view === "glossary" && <GlossaryEditor store={store} />}
        {view === "diagnostics" && <Diagnostics connection={snapshot.connection} onReconnect={() => void reconnect()} />}
        {view === "settings" && <Settings />}
      </main>
    </div>
  );
}

function NewTranslation({ sourcePath, onPickPdf, onBrowserFile, onStart, fileInputRef }: { sourcePath: string; onPickPdf: () => void; onBrowserFile: (file: File | undefined) => void; onStart: () => void; fileInputRef: React.RefObject<HTMLInputElement | null> }) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) onBrowserFile(file);
  };

  return (
    <div className="content-column reveal">
      <div className="section-heading">
        <div>
          <p className="eyebrow">新建翻译</p>
          <h2>选择 PDF，开始本地翻译</h2>
          <p className="hero-panel-muted">从配置的输入目录选择 PDF。翻译通过本地 Codex sidecar 执行，文档保留在当前运行环境中。</p>
        </div>
      </div>

      <Card className="intake-card">
        <CardContent>
          <div className="form-grid">
            <div
              className="drop-zone"
              data-dragging={dragging}
              onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
            >
              <FolderOpen size={24} className="muted-icon" />
              <span>{sourcePath ? sourcePath : "将 PDF 拖放到这里"}</span>
              <Button variant="secondary" className="browse-action" onClick={onPickPdf}>选择 PDF</Button>
              <input ref={fileInputRef} type="file" accept="application/pdf" className="visually-hidden" onChange={(event) => onBrowserFile(event.target.files?.[0])} />
            </div>
            <p className="form-help">只能选择配置输入目录中的 PDF 文件。</p>

            <div className="form-row">
              <label id="lang-label">翻译方向</label>
              <span className="select-like" aria-labelledby="lang-label">英语 → 简体中文</span>
              <p className="form-help">当前版本的翻译方向由配置管理。</p>
            </div>

            <div className="form-row">
              <label id="output-label">输出方式</label>
              <span className="select-like" aria-labelledby="output-label">双语对照 PDF</span>
              <p className="form-help">生成包含原文与译文对照栏的翻译副本。</p>
            </div>

            <Button className="primary-action" onClick={onStart} disabled={!sourcePath.trim()}>加入翻译队列</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Jobs({ jobs, cancelling, refreshingJob, onOpen, onCancel, onRefresh }: { jobs: JobState[]; cancelling: string | null; refreshingJob: string | null; onOpen: (id: string) => void; onCancel: (id: string) => void; onRefresh: (id: string) => void }) {
  if (jobs.length === 0) {
    return (
      <div className="content-column reveal">
        <div className="section-heading">
          <div>
            <p className="eyebrow">翻译任务</p>
            <h2>还没有翻译任务</h2>
            <p className="hero-panel-muted">前往“新建翻译”选择 PDF 并加入队列。</p>
          </div>
        </div>
        <div className="empty-state">
          <FolderOpen size={24} className="muted-icon" />
          <span>加入文档后，任务会显示在这里。</span>
        </div>
      </div>
    );
  }

  return (
    <div className="content-column reveal">
      <div className="section-heading">
        <div>
          <p className="eyebrow">翻译任务</p>
          <h2>{jobs.length} 个翻译任务</h2>
        </div>
      </div>

      <Card>
        <CardContent>
          <div className="job-list" role="list">
            {jobs.map((job) => (
              <div
                key={job.job_id}
                className="job-row"
                data-active={isActiveJob(job)}
                role="listitem"
                tabIndex={0}
                onClick={() => onOpen(job.job_id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onOpen(job.job_id);
                  }
                }}
              >
                <div className="job-main">
                  <div className="job-id">{job.job_id}</div>
                  <div className="job-file">{job.source_path || "—"}</div>
                  {job.safe_error_message && <div className="job-error">{job.safe_error_message}</div>}
                </div>
                <StageBadge stage={job.stage} status={job.status} />
                {isActiveJob(job) && (
                  <div className="job-progress">
                  <Progress value={0} aria-label={`${job.job_id} 的翻译进度`} />
                  </div>
                )}
                <Button variant="ghost" size="sm" onClick={(event) => { event.stopPropagation(); onRefresh(job.job_id); }} disabled={refreshingJob === job.job_id} aria-label={`刷新任务 ${job.job_id}`}>
                  <RefreshCw size={14} className={refreshingJob === job.job_id ? "spin" : ""} />
                </Button>
                <Button variant="ghost" size="sm" className="cancel-action" onClick={(event) => { event.stopPropagation(); onCancel(job.job_id); }} disabled={cancelling === job.job_id || !isActiveJob(job)} aria-label={`取消任务 ${job.job_id}`}>
                  取消
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StageBadge({ stage, status }: { stage: JobState["stage"]; status: JobState["status"] }) {
  const labels: Record<JobState["stage"] | JobState["status"], string> = {
    discovered: "排队中",
    validating_input: "校验输入",
    preparing_runtime: "准备运行环境",
    translating: "正在翻译",
    rendering: "正在排版",
    validating_output: "正在校验",
    completed: "已完成",
    running: "运行中",
    retry_pending: "等待重试",
    failed: "失败",
    cancelled: "已取消",
  };
  const label = labels[status] ?? labels[stage];
  return (
    <span className="stage-badge" data-stage={status === "cancelled" ? "cancelled" : status === "failed" ? "failed" : status === "running" ? "running" : status === "discovered" || status === "retry_pending" ? "queued" : "completed"}>
      {status === "running" && <Activity size={12} />}
      {status === "completed" && <CheckCircle2 size={12} />}
      {label}
    </span>
  );
}

function JobDetails({ jobId, onBack }: { jobId: string | null; onBack: () => void }) {
  if (!jobId) {
    return (
      <div className="content-column reveal">
        <div className="empty-state"><span>尚未选择任务。</span></div>
      </div>
    );
  }

  return (
    <div className="content-column reveal">
      <div className="back-action">
        <Button variant="ghost" size="sm" onClick={onBack}><ArrowUpRight size={14} className="rotate-180" /> 返回任务列表</Button>
      </div>
      <div className="section-heading">
        <div>
          <p className="eyebrow">翻译任务</p>
          <h2>任务详情</h2>
          <p className="job-id">任务 ID：{jobId}</p>
        </div>
      </div>
      <Card className="detail-card">
        <CardContent>
          <p className="form-help">详细任务信息将通过本地服务协议提供。</p>
        </CardContent>
      </Card>
    </div>
  );
}

function GlossaryEditor({ store }: { store: JobStore }) {
  const [scope, setScope] = useState<"global" | "document">("global");
  const EMPTY_ENTRY: GlossaryEntry = { source: "", target: "", notes: "", enabled: true };
  const [entries, setEntries] = useState<GlossaryEntry[]>([EMPTY_ENTRY]);
  const [saving, setSaving] = useState(false);
  const [contextText, setContextText] = useState("");
  const [contextSaving, setContextSaving] = useState(false);
  const [context, setContext] = useState<ContextResult>({ document_id: "", title: "", abstract: "", text: "", version: null });
  const [glossary, setGlossary] = useState<GlossaryResult>({ scope: "global", document_id: null, entries: [], version: null });
  const [status, setStatus] = useState<string | undefined>(undefined);
  const [documentStem, setDocumentStem] = useState("");

  const saveGlossary = async () => {
    setSaving(true);
    setStatus(undefined);
    try {
      const documentId = scope === "document" ? documentStem.trim() : undefined;
      const result = await store.saveGlossary(scope, entries, documentId);
      setGlossary(result);
      setStatus("术语表已保存");
    } finally {
      setSaving(false);
    }
  };

  const saveContext = async () => {
    setContextSaving(true);
    setStatus(undefined);
    try {
      const documentId = documentStem.trim();
      if (!documentId) {
        setStatus("保存文档上下文前，请先填写文档标识。");
        return;
      }
      const result = await store.saveContext(documentId, contextText);
      setContext(result);
      setStatus("文档上下文已保存");
    } finally {
      setContextSaving(false);
    }
  };

  const loadDocumentGlossary = () => {
    const stem = documentStem.trim();
    if (!stem) {
      setStatus("加载文档术语表前，请先填写文档标识。");
      return;
    }
    setStatus("术语表和文档上下文已加载");
  };

  const updateEntry = (index: number, patch: Partial<GlossaryEntry>) => {
    setEntries((current) => current.map((entry, entryIndex) => entryIndex === index ? { ...entry, ...patch } : entry));
  };

  return (
    <div className="content-column reveal">
      <div className="section-heading">
        <div>
          <p className="eyebrow">术语与上下文</p>
          <h2>管理翻译术语和文档上下文</h2>
          <p className="hero-panel-muted">术语表用于统一译法；文档上下文会在发送给模型前进行长度限制和规范化。</p>
        </div>
      </div>

      <Card className="editor-card">
        <CardHeader className="card-label"><BookOpen size={16} /> 术语表</CardHeader>
        <CardContent>
          <div className="editor-toolbar">
            <div className="scope-tabs" role="tablist">
              <Button variant="secondary" data-active={scope === "global"} onClick={() => setScope("global")} aria-selected={scope === "global"}>全局术语</Button>
              <Button variant="secondary" data-active={scope === "document"} onClick={() => setScope("document")} aria-selected={scope === "document"}>文档术语</Button>
            </div>
          </div>
          <div className="glossary-list">
            {entries.map((entry, index) => (
              <div key={index} className="glossary-row">
                <input aria-label={`源术语 ${index + 1}`} className="form-input" value={entry.source} onChange={(event) => updateEntry(index, { source: event.target.value })} placeholder="源术语" />
                <input aria-label={`目标术语 ${index + 1}`} className="form-input" value={entry.target} onChange={(event) => updateEntry(index, { target: event.target.value })} placeholder="目标术语" />
                <input aria-label={`备注 ${index + 1}`} className="form-input" value={entry.notes} onChange={(event) => updateEntry(index, { notes: event.target.value })} placeholder="备注" />
                <label className="check-label"><input type="checkbox" checked={entry.enabled} onChange={(event) => updateEntry(index, { enabled: event.target.checked })} /> 启用</label>
                <Button variant="ghost" size="sm" aria-label={`删除术语 ${index + 1}`} onClick={() => setEntries((current) => current.filter((_, entryIndex) => entryIndex !== index))}>删除</Button>
              </div>
            ))}
          </div>
          <div className="editor-actions"><Button variant="secondary" onClick={() => setEntries((current) => [...current, { ...EMPTY_ENTRY }])}>新增术语</Button><Button onClick={() => void saveGlossary()} disabled={saving}>{saving ? "正在保存" : "保存术语表"}</Button></div>
        </CardContent>
      </Card>
      {scope === "document" && (
        <Card className="editor-card context-editor">
          <CardHeader className="card-label"><BookOpen size={16} /> 文档上下文</CardHeader>
          <CardContent>
            <div className="form-grid">
              <div className="form-row">
                <label htmlFor="document-stem">文档标识</label>
                <div className="path-input-row">
                  <input id="document-stem" className="form-input" placeholder="例如 paper-2024" aria-describedby="document-stem-help" value={documentStem} onChange={(event) => setDocumentStem(event.target.value)} />
                  <Button variant="secondary" onClick={() => loadDocumentGlossary()}>加载</Button>
                </div>
                <p id="document-stem-help" className="form-help">文档标识用于关联某一篇论文或 PDF。</p>
              </div>
            </div>
            <p className="editor-help">可填写标题、摘要、术语说明或背景信息。服务会在发送给 Codex 前对上下文进行规范化和长度限制。</p>
            {status && <p className="form-help" role="status" aria-live="polite">{status}</p>}
            <label htmlFor="document-context">上下文内容</label>
            <textarea id="document-context" value={contextText} onChange={(event) => setContextText(event.target.value)} placeholder={"论文标题\n摘要\n简短的文档背景或术语说明……"} />
            <div className="editor-footer"><small>{context.version ? `版本 ${context.version.slice(0, 8)}` : "尚未保存"}</small><Button onClick={() => void saveContext()} disabled={contextSaving}>{contextSaving ? "正在保存" : "保存上下文"}</Button></div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Diagnostics({ connection, onReconnect }: { connection: { status: string }; onReconnect: () => void }) {
  return (
    <div className="content-column reveal">
      <div className="section-heading">
        <div>
          <p className="eyebrow">运行诊断</p>
          <h2>检查本地运行状态</h2>
        </div>
        <Button variant="secondary" className="reconnect-action" onClick={onReconnect}>重新连接</Button>
      </div>
      <div className="diagnostic-grid">
        <Diagnostic icon={<ShieldCheck />} title="路径访问范围" value="已启用" detail="输入 PDF 仅限配置的目录。" />
        <Diagnostic icon={<Activity />} title="本地服务协议" value={connection.status === "ready" ? "协议 v1 · 已连接" : connection.status} detail="JSONL 请求/响应通道可用。" />
        <Diagnostic icon={<Library />} title="Codex 会话" value="尚未检查" detail="仅在开始翻译时使用实时认证。" />
      </div>
    </div>
  );
}

function Diagnostic({ icon, title, value, detail }: { icon: React.ReactNode; title: string; value: string; detail: string }) {
  return (
    <Card className="diag-card">
      {icon}
      <span className="eyebrow">{title}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
    </Card>
  );
}

function Settings() {
  return (
    <div className="content-column reveal">
      <div className="section-heading">
        <div>
          <p className="eyebrow">设置</p>
          <h2>运行配置</h2>
          <p className="hero-panel-muted">核心运行参数由 config.toml 管理；此处展示当前配置摘要。</p>
        </div>
      </div>
      <Card className="settings-card">
        <div><span>输入目录</span><strong>由 config.toml 配置</strong></div>
        <div><span>翻译模式</span><strong>Codex SDK · 按文档保持上下文</strong></div>
        <div><span>执行方式</span><strong>单次 BabelDOC 子进程</strong></div>
        <div className="settings-language-row">
          <div className="settings-language-copy">
            <span>界面语言</span>
            <small id="i18n-help">语言切换功能将在后续版本提供。</small>
          </div>
          <select aria-describedby="i18n-help" aria-label="界面语言" value="zh-CN" disabled>
            <option value="zh-CN">简体中文（当前）</option>
          </select>
        </div>
      </Card>
    </div>
  );
}

export default App;

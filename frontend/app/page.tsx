"use client";

import { useState, useEffect, useRef } from "react";

const API_BASE = "http://127.0.0.1:8000";

type Stage =
  | "idle"
  | "loading"
  | "awaiting_approval"
  | "already_fixed"
  | "fix_failed"
  | "success"
  | "cancelled"
  | "error";

interface SolveResult {
  status: string;
  thread_id?: string;
  message?: string;
  data?: {
    title?: string;
    root_cause?: string;
    files_fixed?: string[];
    tests_passed?: boolean;
    test_output?: string;
    diff?: Record<string, string>;
    reason?: string;
    pr_url?: string;
    branch_name?: string;
  };
}

const AGENT_STEPS = [
  { id: "fetch",    label: "Fetch Issue",       icon: "⬇",  keyword: "FetchIssue Agent running" },
  { id: "research", label: "Research Codebase", icon: "🔬", keyword: "Research Agent running" },
  { id: "validate", label: "Validate",          icon: "✔",  keyword: "Validator Agent running" },
  { id: "plan",     label: "Plan Fix",          icon: "📋", keyword: "Planner Agent running" },
  { id: "fix",      label: "Write Fix",         icon: "✏",  keyword: "Fix Agent running" },
  { id: "test",     label: "Run Tests",         icon: "🧪", keyword: "Test Runner Agent running" },
  { id: "pr",       label: "Create PR",         icon: "🚀", keyword: "PR Creator Agent running" },
];

function getLogColor(line: string): string {
  if (line.startsWith("✅") || line.startsWith("🏁")) return "text-[#00ff9d]";
  if (line.startsWith("❌")) return "text-[#ff4444]";
  if (line.startsWith("⚠️")) return "text-[#ffaa00]";
  if (line.startsWith("🔍") || line.startsWith("🔎") || line.startsWith("🔑")) return "text-[#4d94ff]";
  if (line.startsWith("📥") || line.startsWith("📝") || line.startsWith("📋") || line.startsWith("📄") || line.startsWith("📖")) return "text-[#cc99ff]";
  if (line.startsWith("🧠") || line.startsWith("🛡️") || line.startsWith("🔧") || line.startsWith("🧪") || line.startsWith("🚀")) return "text-[#ffcc44]";
  if (line.startsWith("🛑") || line.startsWith("🔄")) return "text-[#ff8844]";
  if (line.startsWith("✍️") || line.startsWith("🌿")) return "text-[#44ddff]";
  return "text-[#888]";
}

export default function Home() {
  const [issueUrl, setIssueUrl]         = useState("");
  const [stage, setStage]               = useState<Stage>("idle");
  const [result, setResult]             = useState<SolveResult | null>(null);
  const [activeStep, setActiveStep]     = useState(-1);
  const [expandedDiff, setExpandedDiff] = useState<string | null>(null);
  const [logs, setLogs]                 = useState<string[]>([]);
  const [threadId, setThreadId]         = useState<string | null>(null);
  const [errorDetail, setErrorDetail]   = useState<string>("");
  const logsEndRef                      = useRef<HTMLDivElement>(null);
  const eventSourceRef                  = useRef<EventSource | null>(null);
  const pollRef                         = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    if (logs.length === 0) return;
    const last = logs[logs.length - 1];
    AGENT_STEPS.forEach((step, i) => {
      if (last.includes(step.keyword)) setActiveStep(i);
    });
  }, [logs]);

  const stopAll = () => {
    eventSourceRef.current?.close();
    if (pollRef.current) clearInterval(pollRef.current);
  };

  const startLogStream = (tid: string) => {
    eventSourceRef.current?.close();
    const es = new EventSource(`${API_BASE}/logs/${tid}`);
    eventSourceRef.current = es;
    es.onmessage = (e) => {
      if (!e.data || e.data === "__DONE__") { es.close(); return; }
      setLogs((prev) => [...prev, e.data]);
    };
    es.onerror = () => es.close();
  };

  const pollStatus = (tid: string, onDone: (r: SolveResult) => void) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/status/${tid}`);
        const data = await res.json();
        if (data.status === "done" || data.status === "error") {
          clearInterval(pollRef.current!);
          onDone(data.result);
        }
      } catch (e) {
        clearInterval(pollRef.current!);
        setErrorDetail("Poll failed: " + String(e));
        setStage("error");
      }
    }, 1000);
  };

  const handleSolve = async () => {
    if (!issueUrl.trim()) return;
    setStage("loading");
    setResult(null);
    setLogs([]);
    setActiveStep(0);
    setErrorDetail("");

    try {
      const res = await fetch(`${API_BASE}/solve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ issue_url: issueUrl }),
      });

      const json = await res.json();
      const thread_id = json.thread_id;

      if (!thread_id) {
        setErrorDetail("/solve response missing thread_id: " + JSON.stringify(json));
        setStage("error");
        return;
      }

      setThreadId(thread_id);
      startLogStream(thread_id);

      pollStatus(thread_id, (finalResult) => {
        setResult(finalResult);
        if (finalResult.status === "awaiting_approval") {
          setActiveStep(5);
          setStage("awaiting_approval");
        } else if (finalResult.status === "already_fixed") {
          setStage("already_fixed");
        } else if (finalResult.status === "fix_failed") {
          setStage("fix_failed");
        } else {
          setErrorDetail("Unexpected status: " + finalResult.status);
          setStage("error");
        }
      });

    } catch (e) {
      setErrorDetail("Fetch failed: " + String(e));
      setStage("error");
    }
  };

  const handleApprove = async () => {
    if (!threadId) return;
    setStage("loading");
    setActiveStep(6);
    setLogs((prev) => [...prev, "▶️  Resuming → Creating PR..."]);

    try {
      await fetch(`${API_BASE}/approve-pr`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: threadId }),
      });

      startLogStream(threadId);
      pollStatus(threadId, (finalResult) => {
        setResult((prev) => ({ ...prev!, ...finalResult }));
        setStage(finalResult.status === "success" ? "success" : "error");
      });
    } catch (e) {
      setErrorDetail("Approve failed: " + String(e));
      setStage("error");
    }
  };

  const handleCancel = async () => {
    if (!threadId) return;
    stopAll();
    await fetch(`${API_BASE}/cancel-pr`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ thread_id: threadId }),
    });
    setStage("cancelled");
  };

  const handleReset = () => {
    stopAll();
    setStage("idle");
    setResult(null);
    setActiveStep(-1);
    setIssueUrl("");
    setExpandedDiff(null);
    setLogs([]);
    setThreadId(null);
    setErrorDetail("");
  };

  return (
    <main className="min-h-screen bg-[#0a0a0f] text-white font-mono relative overflow-hidden">
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateX(-8px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        .log-line {
          opacity: 0;
          animation: fadeSlideIn 0.15s ease forwards;
        }
      `}</style>

      <div className="absolute inset-0 opacity-[0.04]" style={{
        backgroundImage: "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)",
        backgroundSize: "40px 40px",
      }} />
      <div className="absolute top-[-200px] left-[50%] translate-x-[-50%] w-[600px] h-[400px] rounded-full bg-[#00ff9d] opacity-[0.04] blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-100px] right-[-100px] w-[400px] h-[400px] rounded-full bg-[#0066ff] opacity-[0.05] blur-[80px] pointer-events-none" />

      <div className="relative z-10 max-w-3xl mx-auto px-6 py-16">

        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-2 h-2 rounded-full bg-[#00ff9d] animate-pulse" />
            <span className="text-[#00ff9d] text-xs tracking-[0.3em] uppercase">Autonomous Agent</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-white leading-tight">AI GitHub Agent</h1>
          <p className="mt-2 text-[#666] text-sm leading-relaxed">
            Paste a GitHub issue URL. The agent researches, fixes, tests, and opens a PR — autonomously.
          </p>
        </div>

        {/* Input */}
        <div className="mb-8">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#333] text-sm select-none">$</span>
              <input
                type="text"
                value={issueUrl}
                onChange={(e) => setIssueUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && stage === "idle" && handleSolve()}
                placeholder="https://github.com/owner/repo/issues/42"
                disabled={stage !== "idle"}
                className="w-full bg-[#111118] border border-[#1e1e2e] rounded-lg pl-8 pr-4 py-3 text-sm text-white placeholder-[#333] focus:outline-none focus:border-[#00ff9d] focus:ring-1 focus:ring-[#00ff9d] disabled:opacity-40 transition-colors"
              />
            </div>
            {stage === "idle" ? (
              <button onClick={handleSolve} disabled={!issueUrl.trim()}
                className="px-5 py-3 bg-[#00ff9d] text-black text-sm font-bold rounded-lg hover:bg-[#00e68a] disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95">
                Solve →
              </button>
            ) : (
              <button onClick={handleReset}
                className="px-5 py-3 border border-[#1e1e2e] text-[#666] text-sm rounded-lg hover:border-[#333] hover:text-white transition-all">
                Reset
              </button>
            )}
          </div>
        </div>

        {/* Pipeline */}
        {stage !== "idle" && (
          <div className="mb-6 bg-[#0d0d14] border border-[#1a1a2e] rounded-xl p-5">
            <div className="text-[#444] text-xs tracking-widest uppercase mb-4">Pipeline</div>
            <div className="flex items-center gap-1 flex-wrap">
              {AGENT_STEPS.map((step, i) => {
                const isDone = i < activeStep || (stage === "success") || (stage === "awaiting_approval" && i < 6);
                const isActive = i === activeStep;
                return (
                  <div key={step.id} className="flex items-center gap-1">
                    <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-all duration-300 ${
                      isDone ? "bg-[#00ff9d]/10 text-[#00ff9d] border border-[#00ff9d]/20"
                      : isActive ? "bg-[#0066ff]/10 text-[#4d94ff] border border-[#0066ff]/30 animate-pulse"
                      : "text-[#333] border border-[#1a1a2e]"
                    }`}>
                      <span>{step.icon}</span>
                      <span>{step.label}</span>
                    </div>
                    {i < AGENT_STEPS.length - 1 && (
                      <span className={`text-xs ${i < activeStep ? "text-[#00ff9d]/40" : "text-[#1e1e2e]"}`}>→</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Live terminal */}
        {stage !== "idle" && (
          <div className="mb-6 bg-[#070710] border border-[#1a1a2e] rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-[#1a1a2e] bg-[#0d0d14]">
              <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
              <span className="ml-2 text-[#333] text-xs">agent logs</span>
              {stage === "loading" && (
                <div className="ml-auto flex gap-1">
                  {[0,1,2].map(i => (
                    <div key={i} className="w-1 h-1 rounded-full bg-[#0066ff] animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
              )}
            </div>
            <div className="p-4 h-80 overflow-y-auto">
              {logs.length === 0 ? (
                <span className="text-[#2a2a3a] text-xs animate-pulse">connecting to agent...</span>
              ) : (
                <div className="space-y-0.5">
                  {logs.map((line, i) => (
                    <div
                      key={i}
                      className={`log-line text-xs leading-relaxed ${getLogColor(line)}`}
                      style={{ animationDelay: `${i === logs.length - 1 ? 0 : 0}s` }}
                    >
                      <span className="text-[#2a2a3a] mr-2 select-none">{String(i + 1).padStart(3, "0")}</span>
                      {line}
                    </div>
                  ))}
                </div>
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        )}

        {/* Awaiting approval */}
        {stage === "awaiting_approval" && result?.data && (
          <div className="space-y-4">
            <div className="bg-[#0d0d14] border border-[#1a1a2e] rounded-xl p-5">
              <div className="text-[#444] text-xs tracking-widest uppercase mb-3">Issue</div>
              <div className="text-white text-sm font-bold mb-1">{result.data.title}</div>
              <div className="text-[#555] text-xs">{result.data.root_cause}</div>
            </div>

            {result.data.files_fixed && result.data.files_fixed.length > 0 && (
              <div className="bg-[#0d0d14] border border-[#1a1a2e] rounded-xl p-5">
                <div className="text-[#444] text-xs tracking-widest uppercase mb-3">Files Modified</div>
                <div className="space-y-1">
                  {result.data.files_fixed.map((f) => (
                    <div key={f} className="flex items-center gap-2 text-xs">
                      <span className="text-[#00ff9d]">M</span>
                      <span className="text-[#888]">{f}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.data.diff && Object.keys(result.data.diff).length > 0 && (
              <div className="bg-[#0d0d14] border border-[#1a1a2e] rounded-xl p-5">
                <div className="text-[#444] text-xs tracking-widest uppercase mb-3">Diff Preview</div>
                <div className="space-y-2">
                  {Object.entries(result.data.diff).map(([file, diff]) => (
                    <div key={file}>
                      <button onClick={() => setExpandedDiff(expandedDiff === file ? null : file)}
                        className="flex items-center gap-2 text-xs text-[#666] hover:text-white transition-colors w-full text-left">
                        <span>{expandedDiff === file ? "▼" : "▶"}</span>
                        <span>{file}</span>
                      </button>
                      {expandedDiff === file && (
                        <pre className="mt-2 text-[11px] bg-[#070710] border border-[#111] rounded-lg p-3 overflow-x-auto text-[#888] leading-relaxed whitespace-pre-wrap break-all">
                          {diff}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-[#0d0d14] border border-[#00ff9d]/20 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#00ff9d]" />
                <span className="text-[#00ff9d] text-xs tracking-widest uppercase">Tests Passed</span>
              </div>
              {result.data.test_output && (
                <pre className="text-[11px] text-[#555] leading-relaxed whitespace-pre-wrap break-all">
                  {result.data.test_output.slice(0, 300)}{result.data.test_output.length > 300 ? "..." : ""}
                </pre>
              )}
            </div>

            <div className="flex gap-3">
              <button onClick={handleApprove}
                className="flex-1 py-3 bg-[#00ff9d] text-black text-sm font-bold rounded-lg hover:bg-[#00e68a] transition-all active:scale-95">
                🚀 Create Pull Request
              </button>
              <button onClick={handleCancel}
                className="px-5 py-3 border border-[#1e1e2e] text-[#666] text-sm rounded-lg hover:border-[#ff4444]/50 hover:text-[#ff4444] transition-all">
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Success */}
        {stage === "success" && result?.data && (
          <div className="bg-[#0d0d14] border border-[#00ff9d]/30 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-full bg-[#00ff9d]/10 border border-[#00ff9d]/30 flex items-center justify-center text-[#00ff9d]">✓</div>
              <div>
                <div className="text-white font-bold text-sm">Pull Request Created</div>
                <div className="text-[#555] text-xs">Branch: {result.data.branch_name}</div>
              </div>
            </div>
            {result.data.pr_url && (
              <a href={result.data.pr_url} target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-[#00ff9d] text-sm hover:underline">
                View PR on GitHub →
              </a>
            )}
          </div>
        )}

        {/* Already fixed */}
        {stage === "already_fixed" && result?.data && (
          <div className="bg-[#0d0d14] border border-[#ffaa00]/30 rounded-xl p-6">
            <div className="text-[#ffaa00] text-xs tracking-widest uppercase mb-2">Already Resolved</div>
            <div className="text-white text-sm mb-1">{result.data.title}</div>
            <div className="text-[#555] text-xs">{result.data.reason}</div>
          </div>
        )}

        {/* Fix failed */}
        {stage === "fix_failed" && result?.data && (
          <div className="bg-[#0d0d14] border border-[#ff4444]/30 rounded-xl p-6">
            <div className="text-[#ff4444] text-xs tracking-widest uppercase mb-2">Fix Failed</div>
            <div className="text-white text-sm mb-2">{result.data.title}</div>
            {result.data.test_output && (
              <pre className="text-[11px] text-[#555] leading-relaxed whitespace-pre-wrap break-all">
                {result.data.test_output.slice(0, 400)}
              </pre>
            )}
          </div>
        )}

        {/* Cancelled */}
        {stage === "cancelled" && (
          <div className="bg-[#0d0d14] border border-[#1a1a2e] rounded-xl p-6 text-[#444] text-sm">
            PR creation cancelled.
          </div>
        )}

        {/* Error */}
        {stage === "error" && (
          <div className="bg-[#0d0d14] border border-[#ff4444]/30 rounded-xl p-6">
            <div className="text-[#ff4444] text-sm mb-2">Something went wrong.</div>
            {errorDetail && (
              <pre className="text-[11px] text-[#ff6666] leading-relaxed whitespace-pre-wrap break-all mt-2">
                {errorDetail}
              </pre>
            )}
            {!errorDetail && (
              <div className="text-[#555] text-xs">
                Make sure your backend is running at <code className="text-[#ff6666]">{API_BASE}</code>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
import React, { useState } from "react";
import { queryScene } from "../services/api";
import { MCPLogEntry } from "../types";
import { Terminal, Send, CheckCircle2, AlertCircle } from "lucide-react";

export const MCPCommandCenter: React.FC = () => {
  const [queryInput, setQueryInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [lastResult, setLastResult] = useState<{
    query: string;
    answer: string;
    tool_used: string;
    latency_ms: number;
  } | null>(null);

  const [logs, setLogs] = useState<MCPLogEntry[]>([
    {
      id: "log-init",
      tool: "get_current_scene",
      timestamp: new Date().toLocaleTimeString(),
      status: "success",
      latency_ms: 18,
      resultSummary: "Scene context synchronized with spatial engine",
    },
  ]);

  const suggestedQueries = [
    "How many people are visible?",
    "Where is the bus?",
    "What is in the center?",
    "Is anything moving?",
  ];

  const registeredTools = [
    "detect_objects",
    "get_current_scene",
    "count_objects",
    "find_object_location",
    "query_scene",
  ];

  const handleExecuteQuery = async (queryStr: string) => {
    const trimmed = queryStr.trim();
    if (!trimmed) return;

    try {
      setIsLoading(true);
      const res = await queryScene(trimmed);
      setLastResult({
        query: trimmed,
        answer: res.answer,
        tool_used: res.tool_used || "query_scene",
        latency_ms: res.latency_ms || 24,
      });

      const logEntry: MCPLogEntry = {
        id: `log-${Date.now()}`,
        tool: res.tool_used || "query_scene",
        query: trimmed,
        timestamp: new Date().toLocaleTimeString(),
        status: "success",
        latency_ms: res.latency_ms || 24,
        resultSummary: res.answer,
      };
      setLogs((prev) => [logEntry, ...prev.slice(0, 8)]);
    } catch (err: any) {
      const errEntry: MCPLogEntry = {
        id: `log-${Date.now()}`,
        tool: "query_scene",
        query: trimmed,
        timestamp: new Date().toLocaleTimeString(),
        status: "error",
        latency_ms: 12,
        resultSummary: err.message || "Execution exception",
      };
      setLogs((prev) => [errEntry, ...prev.slice(0, 8)]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="panel overflow-hidden bg-[#090d14] border border-zinc-800 rounded-none flex flex-col justify-between select-none">
      {/* Panel Header */}
      <div className="h-8 px-2.5 bg-[#080b11] border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-1.5 font-mono text-[11px] text-zinc-200">
          <Terminal className="w-3 h-3 text-sky-400" />
          <span className="font-semibold uppercase tracking-wider">MCP_AGENT_REASONER</span>
        </div>

        <div className="flex items-center gap-1 text-[9px] font-mono text-emerald-400">
          <span className="status-dot active" />
          <span>STDIO_FAST_MCP: READY</span>
        </div>
      </div>

      <div className="p-2 space-y-2">
        {/* Tool Registry Pill Ribbon */}
        <div className="flex items-center gap-1 overflow-x-auto pb-0.5">
          <span className="text-[9px] font-mono text-zinc-500 uppercase flex-shrink-0">
            TOOLS:
          </span>
          {registeredTools.map((t) => (
            <span
              key={t}
              className="text-[9px] font-mono px-1 py-0 bg-zinc-950 text-zinc-400 border border-zinc-800 rounded-none flex-shrink-0"
            >
              {t}()
            </span>
          ))}
        </div>

        {/* Query Input Box */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleExecuteQuery(queryInput);
          }}
          className="space-y-1.5"
        >
          <div className="relative flex items-center">
            <input
              type="text"
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              placeholder="Ask deterministic question (e.g. 'Where is the bus?')..."
              className="w-full bg-[#05070a] border border-zinc-800 focus:border-sky-500 rounded-none pl-2 pr-16 py-1 text-xs text-zinc-200 placeholder-zinc-600 font-mono"
            />
            <button
              type="submit"
              disabled={isLoading || !queryInput.trim()}
              className="absolute right-1 px-2 py-0.5 bg-zinc-900 hover:bg-sky-950/60 text-sky-400 border border-zinc-700 rounded-none text-[10px] font-mono flex items-center gap-1 transition-colors disabled:opacity-40"
            >
              {isLoading ? (
                <div className="w-2.5 h-2.5 border-2 border-sky-400 border-t-transparent animate-spin" />
              ) : (
                <>
                  <span>EXEC</span>
                  <Send className="w-2.5 h-2.5" />
                </>
              )}
            </button>
          </div>

          {/* Quick Query Badges */}
          <div className="flex flex-wrap items-center gap-1">
            <span className="text-[9px] text-zinc-500 font-mono">QUICK:</span>
            {suggestedQueries.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQueryInput(q);
                  handleExecuteQuery(q);
                }}
                className="text-[9px] px-1.5 py-0 bg-zinc-950 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 border border-zinc-800/80 rounded-none font-mono transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </form>

        {/* Execution Output Card */}
        {lastResult && (
          <div className="p-2 bg-[#05070a] border border-zinc-800 rounded-none space-y-1 font-mono">
            <div className="text-[9px] text-zinc-500 uppercase flex items-center justify-between">
              <span>MCP PIPELINE RESULT</span>
              <span className="text-sky-400">{lastResult.latency_ms}ms</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-1 text-[10px]">
              <div className="p-1 bg-zinc-950 border border-zinc-800/80">
                <span className="text-zinc-500 text-[8px] uppercase block">INVOKED TOOL:</span>
                <span className="text-sky-400 font-semibold">{lastResult.tool_used}()</span>
              </div>
              <div className="p-1 bg-zinc-950 border border-zinc-800/80">
                <span className="text-zinc-500 text-[8px] uppercase block">EVALUATED ANSWER:</span>
                <span className="text-zinc-200">{lastResult.answer}</span>
              </div>
            </div>
          </div>
        )}

        {/* Invocation Telemetry Log List */}
        <div>
          <div className="text-[9px] font-mono text-zinc-500 uppercase tracking-wider mb-1 flex items-center justify-between">
            <span>INVOCATION_LOG</span>
            <span>[{logs.length} ENTRIES]</span>
          </div>

          <div className="space-y-0.5 max-h-24 overflow-y-auto font-mono text-[9px] bg-[#05070a] border border-zinc-800/80 p-0.5">
            {logs.map((log) => (
              <div
                key={log.id}
                className="px-1.5 py-0.5 border-b border-zinc-900/60 flex items-center justify-between gap-1 text-zinc-400 hover:bg-zinc-900/60 transition-colors"
              >
                <div className="flex items-center gap-1 truncate">
                  {log.status === "success" ? (
                    <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="w-2.5 h-2.5 text-rose-400 flex-shrink-0" />
                  )}
                  <span className="text-sky-400 font-semibold">{log.tool}</span>
                  <span className="text-zinc-600 truncate">{log.resultSummary}</span>
                </div>
                <div className="flex items-center gap-1.5 text-[8px] text-zinc-500 flex-shrink-0">
                  <span>{log.latency_ms}ms</span>
                  <span>{log.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MCPCommandCenter;

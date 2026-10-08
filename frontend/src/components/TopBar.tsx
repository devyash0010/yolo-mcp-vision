import React from "react";
import { SystemStatus } from "../types";
import { NavTabId } from "./Sidebar";
import { Cpu, Terminal, RefreshCw, ExternalLink } from "lucide-react";

interface TopBarProps {
  activeTab: NavTabId;
  status: SystemStatus | null;
  wsConnected: boolean;
  fps: number;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  activeTab,
  status,
  wsConnected,
  fps,
  onRefresh,
  isRefreshing,
}) => {
  const getTabTitle = (tab: NavTabId) => {
    switch (tab) {
      case "overview":
        return "COMMAND_CENTER_OVERVIEW";
      case "live":
        return "LIVE_VISION_STREAM";
      case "scenes":
        return "SCENE_SNAPSHOT_BUFFER";
      case "detections":
        return "DETECTIONS_EXPLORER";
      case "mcp":
        return "MODEL_CONTEXT_PROTOCOL_TOOLS";
      case "system":
        return "SYSTEM_TELEMETRY_DIAGNOSTICS";
      case "settings":
        return "INFERENCE_PIPELINE_PARAMETERS";
    }
  };

  return (
    <header className="h-9 px-3 bg-[#080b11] border-b border-zinc-800 flex items-center justify-between gap-3 select-none rounded-none">
      {/* Breadcrumb Path */}
      <div className="flex items-center gap-2 text-xs font-mono">
        <span className="text-zinc-600">SYS</span>
        <span className="text-zinc-700">/</span>
        <span className="text-zinc-200 font-semibold uppercase tracking-tight">
          {getTabTitle(activeTab)}
        </span>
        <div className="hidden sm:flex items-center gap-1 ml-2 px-1.5 py-0.2 rounded-none bg-emerald-950/40 border border-emerald-800 text-[9px] text-emerald-400 font-mono">
          <span className="status-dot active" />
          <span>NOMINAL</span>
        </div>
      </div>

      {/* Telemetry Pills */}
      <div className="flex items-center gap-1.5">
        <div className="hidden md:flex items-center gap-1 px-2 py-0.5 rounded-none bg-zinc-950 border border-zinc-800 text-[10px] font-mono">
          <Cpu className="w-3 h-3 text-zinc-500" />
          <span className="text-zinc-500">DEV:</span>
          <span className="text-zinc-200 font-semibold uppercase">
            {status?.active_device || "CPU"}
          </span>
        </div>

        <div className="flex items-center gap-1 px-2 py-0.5 rounded-none bg-zinc-950 border border-zinc-800 text-[10px] font-mono">
          <span className="text-zinc-500">FPS:</span>
          <span
            className={`font-semibold ${
              fps > 15 ? "text-emerald-400" : fps > 5 ? "text-sky-400" : "text-amber-400"
            }`}
          >
            {fps.toFixed(1)}
          </span>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-none bg-zinc-950 border border-zinc-800 text-[10px] font-mono">
          <Terminal className="w-3 h-3 text-sky-400" />
          <span className={`status-dot ${wsConnected ? "active" : "warning"}`} />
          <span className="text-zinc-300 font-medium">
            STREAM:{wsConnected ? "ONLINE" : "OFFLINE"}
          </span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh Telemetry Buffer"
          className="p-1 rounded-none bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <RefreshCw className={`w-3 h-3 ${isRefreshing ? "animate-spin text-sky-400" : ""}`} />
        </button>

        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="hidden lg:flex items-center gap-1 px-2 py-0.5 rounded-none bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-200 text-[10px] font-mono transition-colors"
        >
          <span>OPENAPI</span>
          <ExternalLink className="w-2.5 h-2.5" />
        </a>
      </div>
    </header>
  );
};

export default TopBar;

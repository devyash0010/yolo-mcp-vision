import React from "react";
import { SystemStatus } from "../types";

interface HeaderProps {
  status: SystemStatus | null;
  wsConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({ status, wsConnected }) => {
  return (
    <header className="px-3 py-1.5 flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 bg-[#080b11] rounded-none font-mono text-xs select-none">
      <div className="flex items-center gap-2">
        <div className="h-6 w-6 rounded-none bg-sky-950/60 border border-sky-800 flex items-center justify-center font-bold text-sky-400 text-xs">
          Y
        </div>
        <div className="flex items-center gap-2">
          <span className="font-semibold tracking-wider text-zinc-100 uppercase">
            YOLO::MCP_COMMAND_CENTER
          </span>
          <span className="text-[9px] px-1 py-0.2 rounded-none bg-zinc-900 text-zinc-400 border border-zinc-800">
            v1.1.0
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 text-[10px]">
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-none bg-zinc-950 border border-zinc-800">
          <span className="text-zinc-500">MCP:</span>
          <span className="font-semibold text-emerald-400 flex items-center gap-1">
            <span className="status-dot active" />
            READY
          </span>
        </div>

        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-none bg-zinc-950 border border-zinc-800">
          <span className="text-zinc-500">STREAM:</span>
          <span className={`font-semibold flex items-center gap-1 ${wsConnected ? "text-emerald-400" : "text-amber-400"}`}>
            <span className={`status-dot ${wsConnected ? "active" : "warning"}`} />
            {wsConnected ? "ONLINE" : "CONNECTING"}
          </span>
        </div>

        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-none bg-zinc-950 border border-zinc-800">
          <span className="text-zinc-500">DEV:</span>
          <span className="font-semibold text-zinc-300 uppercase">
            {status?.active_device || "CPU"}
          </span>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-none bg-zinc-950 border border-zinc-800">
          <span className="text-zinc-500">MODEL:</span>
          <span className="text-zinc-400">
            {status?.model_path ? status.model_path.split("/").pop() : "yolo11n.pt"}
          </span>
        </div>
      </div>
    </header>
  );
};

export default Header;

import React from "react";
import { SystemStatus } from "../types";
import {
  LayoutDashboard,
  Video,
  Film,
  Layers,
  Crosshair,
  Terminal,
  Cpu,
  Settings,
} from "lucide-react";

export type NavTabId =
  | "overview"
  | "live"
  | "video"
  | "scenes"
  | "detections"
  | "mcp"
  | "system"
  | "settings";

interface SidebarProps {
  activeTab: NavTabId;
  setActiveTab: (tab: NavTabId) => void;
  status: SystemStatus | null;
  wsConnected: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  status,
  wsConnected,
}) => {
  const navItems: { id: NavTabId; label: string; icon: React.ComponentType<{ className?: string }>; badge?: string }[] = [
    { id: "overview", label: "OVERVIEW", icon: LayoutDashboard },
    { id: "live", label: "LIVE_VISION", icon: Video, badge: wsConnected ? "STREAM" : undefined },
    { id: "video", label: "VIDEO", icon: Film },
    { id: "scenes", label: "SCENE_GRAPH", icon: Layers },
    { id: "detections", label: "DETECTIONS", icon: Crosshair },
    { id: "mcp", label: "MCP_TOOLS", icon: Terminal, badge: "11" },
    { id: "system", label: "TELEMETRY", icon: Cpu },
    { id: "settings", label: "PARAMETERS", icon: Settings },
  ];

  return (
    <aside className="w-48 md:w-52 bg-[#090d14] border-r border-zinc-800 flex flex-col justify-between flex-shrink-0 select-none rounded-none h-screen">
      {/* Brand & Workspace ID */}
      <div>
        <div className="h-10 px-3 bg-[#080b11] border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 bg-sky-500/20 border border-sky-400 flex items-center justify-center font-mono font-bold text-[10px] text-sky-400">
              Y
            </div>
            <span className="font-mono font-bold text-xs tracking-wider text-zinc-100">
              YOLO::MCP
            </span>
          </div>
          <span className="text-[9px] font-mono text-zinc-500 border border-zinc-800 px-1 py-0.2">
            v1.1.0
          </span>
        </div>

        {/* Workspace Title Ribbon */}
        <div className="px-3 py-1 bg-zinc-950/60 border-b border-zinc-800/80 text-[9px] font-mono text-zinc-500 tracking-wider uppercase">
          TELEMETRY CONSOLE
        </div>

        {/* Navigation List Nodes with Tight Utility Margins */}
        <nav className="p-1 space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-2.5 py-1 text-[11px] font-mono border-l-2 rounded-none transition-colors ${
                  isActive
                    ? "bg-zinc-800/70 text-sky-400 border-sky-400 font-semibold"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 border-transparent"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? "text-sky-400" : "text-zinc-500"}`} />
                  <span className="tracking-tight">{item.label}</span>
                </div>

                {item.badge && (
                  <span
                    className={`text-[8px] font-mono px-1 py-0.2 rounded-none ${
                      item.badge === "STREAM"
                        ? "bg-emerald-950/50 text-emerald-400 border border-emerald-800"
                        : "bg-zinc-900 text-zinc-400 border border-zinc-800"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer System Node */}
      <div className="p-2 bg-[#080b11] border-t border-zinc-800 text-[10px] font-mono space-y-1 rounded-none">
        <div className="flex items-center justify-between text-zinc-400">
          <span className="text-zinc-500">RUNTIME:</span>
          <span className="font-semibold text-zinc-300 uppercase">
            {status?.active_device || "CPU"}
          </span>
        </div>

        <div className="flex items-center justify-between text-zinc-400">
          <span className="text-zinc-500">MODEL:</span>
          <span className="text-zinc-300 truncate max-w-[100px]">
            {status?.model_path ? status.model_path.split("/").pop() : "yolo11n.pt"}
          </span>
        </div>

        <div className="flex items-center justify-between pt-0.5 border-t border-zinc-900 text-[9px]">
          <span className="text-zinc-500">SOCKET:</span>
          <span className={`flex items-center gap-1 ${wsConnected ? "text-emerald-400" : "text-amber-400"}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? "bg-emerald-400" : "bg-amber-400"}`} />
            {wsConnected ? "MOUNTED" : "OFFLINE"}
          </span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;

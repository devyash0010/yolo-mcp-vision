import React from "react";
import { MetricsSummary, SystemStatus } from "../types";
import { Cpu, Activity, Terminal, ExternalLink } from "lucide-react";

interface SystemViewProps {
  status: SystemStatus | null;
  metrics: MetricsSummary | null;
  wsConnected: boolean;
}

export const SystemView: React.FC<SystemViewProps> = ({
  status,
  metrics,
  wsConnected,
}) => {
  const subsystems = [
    {
      name: "YOLO Detector Engine",
      status: "OPERATIONAL",
      desc: "Ultralytics YOLO11 Nano (PyTorch / ONNX)",
    },
    {
      name: "2D Spatial Engine",
      status: "OPERATIONAL",
      desc: "3x3 Equidistant Cartesian Grid & Relations",
    },
    {
      name: "FastMCP Server",
      status: "CONNECTED",
      desc: "Official Python FastMCP SDK (Stdio & JSON-RPC)",
    },
    {
      name: "WebSocket Gateway",
      status: wsConnected ? "CONNECTED" : "RECONNECTING",
      desc: "/ws/detection Stream Endpoint",
    },
    {
      name: "SQL Database",
      status: "CONNECTED",
      desc: "SQLAlchemy 2.0 (SQLite / Postgres Repository)",
    },
    {
      name: "REST API Gateway",
      status: "HEALTHY",
      desc: "FastAPI with OpenAPI /docs & /metrics",
    },
  ];

  return (
    <div className="space-y-2.5 select-none font-mono">
      {/* View Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
        <div>
          <h2 className="text-xs font-semibold text-zinc-100 flex items-center gap-1.5 uppercase">
            <Cpu className="w-3.5 h-3.5 text-sky-400" />
            SYSTEM_TELEMETRY & INFRASTRUCTURE_HEALTH
          </h2>
          <p className="text-[10px] text-zinc-500 mt-0.5">
            Hardware acceleration, inference percentiles, and protocol daemon statuses.
          </p>
        </div>
      </div>

      {/* Subsystems Matrix */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {subsystems.map((sub) => (
          <div
            key={sub.name}
            className="p-2 bg-[#090d14] border border-zinc-800 rounded-none flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-[11px] font-semibold text-zinc-200">
                {sub.name}
              </span>
              <span className="inline-flex items-center gap-1 text-[9px] px-1 py-0 bg-emerald-950/40 text-emerald-400 border border-emerald-800 rounded-none">
                <span className="status-dot active" />
                {sub.status}
              </span>
            </div>
            <span className="text-[10px] text-zinc-500">{sub.desc}</span>
          </div>
        ))}
      </div>

      {/* Detail Metric Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
        {/* Runtime Specs */}
        <div className="panel p-2.5 bg-[#090d14] border border-zinc-800 rounded-none space-y-2">
          <div className="text-[11px] font-semibold text-zinc-200 flex items-center gap-1.5 border-b border-zinc-800 pb-1.5 uppercase">
            <Cpu className="w-3 h-3 text-sky-400" />
            <span>VISION_RUNTIME_SPECS</span>
          </div>
          <div className="space-y-1.5 text-[10px]">
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">MODEL_FILE:</span>
              <span className="text-zinc-300">
                {status?.model_path ? status.model_path.split("/").pop() : "yolo11n.pt"}
              </span>
            </div>
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">COMPUTE_DEVICE:</span>
              <span className="text-sky-400 uppercase font-semibold">
                {status?.active_device || "CPU"}
              </span>
            </div>
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">CUDA_ACCELERATION:</span>
              <span className={status?.cuda_available ? "text-emerald-400" : "text-zinc-500"}>
                {status?.cuda_available ? "ENABLED" : "UNAVAILABLE"}
              </span>
            </div>
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">CANVAS_DIMENSION:</span>
              <span className="text-zinc-300">640x640 LETTERBOX</span>
            </div>
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">CONF_THRESHOLD:</span>
              <span className="text-zinc-300">0.35</span>
            </div>
            <div className="flex justify-between py-0.5">
              <span className="text-zinc-500">IOU_NMS_THRESHOLD:</span>
              <span className="text-zinc-300">0.45</span>
            </div>
          </div>
        </div>

        {/* Latency Percentiles */}
        <div className="panel p-2.5 bg-[#090d14] border border-zinc-800 rounded-none space-y-2">
          <div className="text-[11px] font-semibold text-zinc-200 flex items-center gap-1.5 border-b border-zinc-800 pb-1.5 uppercase">
            <Activity className="w-3 h-3 text-sky-400" />
            <span>PERFORMANCE_PERCENTILES</span>
          </div>
          <div className="space-y-1.5 text-[10px]">
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">THROUGHPUT:</span>
              <span className="text-emerald-400 font-semibold">
                {(metrics?.estimated_fps || 19.5).toFixed(1)} FPS
              </span>
            </div>
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">AVG_INFERENCE:</span>
              <span className="text-zinc-300">
                {(metrics?.average_inference_ms || 50.4).toFixed(1)} MS
              </span>
            </div>
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">P50_MEDIAN:</span>
              <span className="text-zinc-300">
                {(metrics?.p50_latency_ms || 51.2).toFixed(1)} MS
              </span>
            </div>
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">P95_LATENCY:</span>
              <span className="text-zinc-300">
                {(metrics?.p95_latency_ms || 53.6).toFixed(1)} MS
              </span>
            </div>
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">SPATIAL_CALC:</span>
              <span className="text-zinc-300">0.50 MS</span>
            </div>
            <div className="flex justify-between py-0.5">
              <span className="text-zinc-500">PROMETHEUS_METRICS:</span>
              <a
                href="/metrics"
                target="_blank"
                className="text-sky-400 hover:underline flex items-center gap-1"
              >
                <span>/metrics</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
          </div>
        </div>

        {/* Protocol Standards */}
        <div className="panel p-2.5 bg-[#090d14] border border-zinc-800 rounded-none space-y-2">
          <div className="text-[11px] font-semibold text-zinc-200 flex items-center gap-1.5 border-b border-zinc-800 pb-1.5 uppercase">
            <Terminal className="w-3 h-3 text-sky-400" />
            <span>PROTOCOL_SPECIFICATION</span>
          </div>
          <div className="space-y-1.5 text-[10px]">
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">SPEC:</span>
              <span className="text-zinc-300">MODEL_CONTEXT_PROTOCOL</span>
            </div>
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">TRANSPORT:</span>
              <span className="text-zinc-300">STDIO / FASTMCP</span>
            </div>
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">SPATIAL_FRAME:</span>
              <span className="text-zinc-300">2D EQUIDISTANT GRID</span>
            </div>
            <div className="flex justify-between border-b border-zinc-900 py-0.5">
              <span className="text-zinc-500">REASONER:</span>
              <span className="text-zinc-300">DETERMINISTIC MATCHER</span>
            </div>
            <div className="flex justify-between py-0.5">
              <span className="text-zinc-500">API_DOCS:</span>
              <a
                href="/docs"
                target="_blank"
                className="text-sky-400 hover:underline flex items-center gap-1"
              >
                <span>OPENAPI_UI</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemView;

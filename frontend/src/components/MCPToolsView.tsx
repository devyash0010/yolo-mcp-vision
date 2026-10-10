import React, { useState } from "react";
import { MCPToolInfo } from "../types";
import { queryScene } from "../services/api";
import { Terminal, Play, CheckCircle2, ChevronRight } from "lucide-react";

export const MCPToolsView: React.FC = () => {
  const tools: MCPToolInfo[] = [
    {
      name: "get_current_scene",
      description: "Returns complete structured SceneContext including entities, grid sectors, and relationships.",
    },
    {
      name: "count_objects",
      description: "Count detected objects of a specific class (or total if unspecified).",
      parameters: { object_class: "person" },
    },
    {
      name: "find_object_location",
      description: "Returns 2D grid position, pixel bounding box, and center coordinate of named object.",
      parameters: { object_class: "bus" },
    },
    {
      name: "get_objects_by_position",
      description: "Returns list of objects located within a specific 3x3 grid sector.",
      parameters: { grid_position: "center" },
    },
    {
      name: "get_spatial_relationships",
      description: "Returns deterministic 2D spatial relationships (left_of, right_of, above, below, near).",
      parameters: { subject: "bus" },
    },
    {
      name: "detect_objects",
      description: "Performs real-time YOLO object detection on the active frame or provided image.",
    },
    {
      name: "detect_image_from_path",
      description: "Runs detection and spatial analysis on an image at a specific local file path.",
      parameters: { image_path: "sample_data/bus.jpg" },
    },
    {
      name: "track_video_stream",
      description: "Runs multi-object ByteTrack tracking on a video media stream.",
      parameters: { frame_step: 5 },
    },
    {
      name: "get_system_status",
      description: "Returns hardware runtime status, active device (CPU vs CUDA), and model info.",
    },
    {
      name: "get_pipeline_metrics",
      description: "Exposes latency percentiles (P50, P95, P99), throughput (FPS), and inference counters.",
    },
    {
      name: "query_scene",
      description: "Evaluates natural language questions against the scene using deterministic intent matching.",
      parameters: { query: "How many people are there?" },
    },
    {
      name: "decide_scene",
      description: "Decision-model battery (Jev/Clef/Laya/local): answers with confidence, cutoff verification, and escalation flags.",
    },
  ];

  const [selectedTool, setSelectedTool] = useState<MCPToolInfo>(tools[0]);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  const handleRunTool = async (tool: MCPToolInfo) => {
    try {
      setIsRunning(true);
      const res = await queryScene(`Test tool: ${tool.name}`);
      setExecutionResult({
        tool: tool.name,
        timestamp: new Date().toISOString(),
        status: "200_OK",
        output: {
          result: res.answer,
          tool_invoked: res.tool_used,
          latency_ms: res.latency_ms,
        },
      });
    } catch (err: any) {
      setExecutionResult({
        tool: tool.name,
        timestamp: new Date().toISOString(),
        status: "500_ERROR",
        error: err.message,
      });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-2.5 select-none font-mono">
      {/* View Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
        <div>
          <h2 className="text-xs font-semibold text-zinc-100 flex items-center gap-1.5 uppercase">
            <Terminal className="w-3.5 h-3.5 text-sky-400" />
            MODEL_CONTEXT_PROTOCOL_TOOLS_REGISTRY
          </h2>
          <p className="text-[10px] text-zinc-500 mt-0.5">
            Official Python MCP SDK compliant tool interfaces exposed to LLM agents and clients.
          </p>
        </div>

        <div className="text-[10px] text-zinc-400 border border-zinc-800 px-2 py-0.5 bg-zinc-950">
          COUNT: <span className="text-sky-400 font-semibold">{tools.length}</span> REGISTERED TOOLS
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-start">
        {/* Tool List Panel */}
        <div className="lg:col-span-5 panel bg-[#090d14] border border-zinc-800 rounded-none overflow-hidden">
          <div className="h-7 px-2.5 bg-[#080b11] border-b border-zinc-800 flex items-center text-[10px] text-zinc-400 font-semibold uppercase">
            REGISTRY_INDEX
          </div>

          <div className="divide-y divide-zinc-900 max-h-[520px] overflow-y-auto">
            {tools.map((tool) => {
              const isSelected = selectedTool.name === tool.name;

              return (
                <div
                  key={tool.name}
                  onClick={() => setSelectedTool(tool)}
                  className={`p-2 cursor-pointer transition-colors ${
                    isSelected ? "bg-zinc-800/80 text-sky-300" : "hover:bg-zinc-900/60"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-zinc-200 text-[11px]">
                      {tool.name}()
                    </span>
                    <ChevronRight
                      className={`w-3 h-3 ${isSelected ? "text-sky-400" : "text-zinc-600"}`}
                    />
                  </div>
                  <p className="text-[9px] text-zinc-500 mt-0.5 line-clamp-2 font-mono">
                    {tool.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Tool Details and Test Invoker Panel */}
        <div className="lg:col-span-7 panel bg-[#090d14] border border-zinc-800 rounded-none p-2.5 space-y-2.5">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
            <div>
              <div className="text-xs font-semibold text-zinc-100 uppercase">
                TOOL: {selectedTool.name}()
              </div>
              <p className="text-[10px] text-zinc-400 mt-0.5">
                {selectedTool.description}
              </p>
            </div>

            <button
              onClick={() => handleRunTool(selectedTool)}
              disabled={isRunning}
              className="flex items-center gap-1 px-2.5 py-1 bg-sky-950/60 hover:bg-sky-900 text-sky-400 border border-sky-800 text-[10px] font-mono rounded-none transition-colors"
            >
              <Play className="w-2.5 h-2.5" />
              <span>{isRunning ? "INVOKING..." : "TEST_INVOCATION"}</span>
            </button>
          </div>

          {/* Parameters Spec */}
          <div className="space-y-1">
            <div className="text-[9px] text-zinc-500 uppercase tracking-wider">
              PARAMETER_SIGNATURE
            </div>
            <pre className="p-2 bg-[#05070a] border border-zinc-800 text-[10px] text-zinc-300 overflow-x-auto rounded-none">
              {JSON.stringify(selectedTool.parameters || { type: "void" }, null, 2)}
            </pre>
          </div>

          {/* Test Execution Output Console */}
          <div className="space-y-1">
            <div className="text-[9px] text-zinc-500 uppercase tracking-wider flex items-center justify-between">
              <span>OUTPUT_CONSOLE</span>
              {executionResult && (
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-2.5 h-2.5" />
                  <span>{executionResult.status}</span>
                </span>
              )}
            </div>
            <pre className="p-2.5 bg-[#05070a] border border-zinc-800 text-[10px] text-sky-300 font-mono overflow-x-auto min-h-[160px] max-h-[240px] rounded-none">
              {executionResult
                ? JSON.stringify(executionResult, null, 2)
                : "// AWAITING_TOOL_EXECUTION\n// Click [TEST_INVOCATION] to dispatch RPC request."}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MCPToolsView;

import React from "react";
import { MetricsSummary, SceneContext } from "../types";
import { MetricStrip } from "./MetricStrip";
import { VideoViewer } from "./VideoViewer";
import { SceneContextPanel } from "./SceneContextPanel";
import { DetectionTable } from "./DetectionTable";
import { MCPCommandCenter } from "./MCPCommandCenter";

interface OverviewViewProps {
  scene: SceneContext | null;
  metrics: MetricsSummary | null;
  annotatedBase64: string | null;
  onSceneUpdated: (newScene: SceneContext, base64: string) => void;
  wsConnected: boolean;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  scene,
  metrics,
  annotatedBase64,
  onSceneUpdated,
  wsConnected,
}) => {
  return (
    <div className="flex flex-col space-y-2.5">
      {/* 1. Header Metrics Overhaul: Unified Flat Ribbon Component */}
      <MetricStrip scene={scene} metrics={metrics} />

      {/* 2. Primary Analytics Viewport Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-start">
        <div className="lg:col-span-8">
          <VideoViewer
            scene={scene}
            annotatedImageBase64={annotatedBase64}
            onSceneUpdated={onSceneUpdated}
            isStreaming={wsConnected}
          />
        </div>

        <div className="lg:col-span-4">
          <SceneContextPanel scene={scene} />
        </div>
      </div>

      {/* 3. Secondary Telemetry Grid: Detections + MCP Agents */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5 items-start">
        <div className="lg:col-span-6">
          <DetectionTable objects={scene?.objects || []} />
        </div>

        <div className="lg:col-span-6">
          <MCPCommandCenter />
        </div>
      </div>
    </div>
  );
};

export default OverviewView;

import React from "react";
import { SceneContext } from "../types";
import { VideoViewer } from "./VideoViewer";
import { SceneContextPanel } from "./SceneContextPanel";
import { Crosshair } from "lucide-react";

interface LiveVisionViewProps {
  scene: SceneContext | null;
  annotatedBase64: string | null;
  onSceneUpdated: (newScene: SceneContext, base64: string) => void;
  wsConnected: boolean;
}

export const LiveVisionView: React.FC<LiveVisionViewProps> = ({
  scene,
  annotatedBase64,
  onSceneUpdated,
  wsConnected,
}) => {
  return (
    <div className="flex flex-col space-y-2.5">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5">
        <div className="lg:col-span-8 space-y-2.5">
          <VideoViewer
            scene={scene}
            annotatedImageBase64={annotatedBase64}
            onSceneUpdated={onSceneUpdated}
            isStreaming={wsConnected}
          />

          {/* Raw Bounding Box Telemetry Inspector */}
          <div className="panel p-2.5 bg-[#090d14] border border-zinc-800 rounded-none select-none">
            <div className="text-[11px] font-mono font-semibold text-zinc-200 mb-2 flex items-center justify-between border-b border-zinc-800 pb-1.5">
              <span className="flex items-center gap-1.5 uppercase">
                <Crosshair className="w-3.5 h-3.5 text-sky-400" />
                COORDINATE_INSPECTOR: NORMALIZED_2D_PLANE
              </span>
              <span className="text-[9px] font-mono text-zinc-500">
                UNITS: PIXEL_RECT_ABSOLUTE & RELATIVE_SECTORS
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-1.5">
              {scene?.objects && scene.objects.length > 0 ? (
                scene.objects.map((obj, i) => (
                  <div
                    key={obj.id || i}
                    className="p-1.5 rounded-none bg-[#05070a] border border-zinc-800 text-[10px] font-mono hover:border-zinc-700 transition-colors"
                  >
                    <div className="flex items-center justify-between text-zinc-200 font-semibold mb-1">
                      <span className="uppercase text-amber-400">{obj.class_name}</span>
                      <span className="text-sky-400">{Math.round(obj.confidence * 100)}%</span>
                    </div>
                    <div className="text-zinc-500 text-[9px] space-y-0.5">
                      <div>
                        BBOX: [{Math.round(obj.bbox.x1)}, {Math.round(obj.bbox.y1)},{" "}
                        {Math.round(obj.bbox.x2)}, {Math.round(obj.bbox.y2)}]
                      </div>
                      <div>
                        CENTER: ({Array.isArray(obj.center) ? Math.round(obj.center[0]) : Math.round(obj.center.x)},{" "}
                        {Array.isArray(obj.center) ? Math.round(obj.center[1]) : Math.round(obj.center.y)})
                      </div>
                      <div className="text-zinc-400 uppercase">
                        SECTOR: {obj.grid_position || "UNASSIGNED"}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="col-span-full py-4 text-center text-zinc-600 font-mono text-[10px]">
                  [NO_ACTIVE_DETECTIONS_TO_INSPECT]
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-4">
          <SceneContextPanel scene={scene} />
        </div>
      </div>
    </div>
  );
};

export default LiveVisionView;

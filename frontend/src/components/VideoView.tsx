import React from "react";
import { SceneContext } from "../types";
import { VideoViewer } from "./VideoViewer";
import { SceneContextPanel } from "./SceneContextPanel";
import { Film, Image, Video, Camera, Cpu } from "lucide-react";

interface VideoViewProps {
  scene: SceneContext | null;
  annotatedBase64: string | null;
  onSceneUpdated: (newScene: SceneContext, base64: string) => void;
  wsConnected: boolean;
}

const sourceMatrix: {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  endpoint: string;
  detail: string;
}[] = [
  {
    id: "sample",
    icon: Image,
    title: "SAMPLE_INPUT",
    endpoint: "POST /detection/image",
    detail: "Bundled sample media decoded into a single-frame SceneContext.",
  },
  {
    id: "video",
    icon: Film,
    title: "MOUNT_VIDEO",
    endpoint: "POST /detection/video",
    detail: "Uploaded .mp4/.avi/.mov sampled every 5 frames, max 60 frames, tracker IDs on.",
  },
  {
    id: "camera",
    icon: Camera,
    title: "ATTACH_CAMERA",
    endpoint: "POST /detection/frame",
    detail: "Browser getUserMedia feeds 640px JPEG frames to YOLO at ~2.5 FPS with live boxes.",
  },
];

export const VideoView: React.FC<VideoViewProps> = ({
  scene,
  annotatedBase64,
  onSceneUpdated,
  wsConnected,
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5">
      <div className="lg:col-span-8 space-y-2.5">
        <VideoViewer
          scene={scene}
          annotatedImageBase64={annotatedBase64}
          onSceneUpdated={onSceneUpdated}
          isStreaming={wsConnected}
        />

        {/* Source Processing Matrix */}
        <div className="panel p-2.5 bg-[#090d14] border border-zinc-800 rounded-none select-none">
          <div className="text-[11px] font-mono font-semibold text-zinc-200 mb-2 flex items-center justify-between border-b border-zinc-800 pb-1.5">
            <span className="flex items-center gap-1.5 uppercase">
              <Video className="w-3.5 h-3.5 text-sky-400" />
              SOURCE_PROCESSING_MATRIX
            </span>
            <span className="text-[9px] font-mono text-zinc-500">YOLO11N • SPATIAL_ENGINE_V2</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-1.5">
            {sourceMatrix.map((src) => {
              const Icon = src.icon;
              return (
                <div
                  key={src.id}
                  className="p-2 rounded-none bg-[#05070a] border border-zinc-800 hover:border-zinc-700 transition-colors"
                >
                  <div className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-200 font-semibold mb-1 uppercase">
                    <Icon className="w-3 h-3 text-sky-400" />
                    {src.title}
                  </div>
                  <div className="text-[9px] font-mono text-sky-500 mb-1">{src.endpoint}</div>
                  <div className="text-[9px] font-mono text-zinc-500 leading-relaxed">{src.detail}</div>
                </div>
              );
            })}
          </div>

          <div className="mt-2 pt-1.5 border-t border-zinc-800 flex items-center gap-1.5 text-[9px] font-mono text-zinc-600">
            <Cpu className="w-3 h-3" />
            ALL SOURCES CONVERGE ON DetectionService.process_frame() → SceneContext → MCP TOOLS
          </div>
        </div>
      </div>

      <div className="lg:col-span-4">
        <SceneContextPanel scene={scene} />
      </div>
    </div>
  );
};

export default VideoView;
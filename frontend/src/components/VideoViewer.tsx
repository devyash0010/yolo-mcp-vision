import React, { useEffect, useRef, useState } from "react";
import { SceneContext } from "../types";
import { detectImagePath, uploadImage, uploadVideo } from "../services/api";
import {
  Grid,
  Maximize2,
  Minimize2,
  Pause,
  Play,
  Download,
  Upload,
  Film,
  Camera,
} from "lucide-react";

interface VideoViewerProps {
  scene: SceneContext | null;
  annotatedImageBase64: string | null;
  onSceneUpdated: (newScene: SceneContext, base64: string) => void;
  isStreaming: boolean;
}

export const VideoViewer: React.FC<VideoViewerProps> = ({
  scene,
  annotatedImageBase64,
  onSceneUpdated,
  isStreaming,
}) => {
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [mediaSource, setMediaSource] = useState<"sample" | "upload" | "video" | "webcam">("sample");

  const containerRef = useRef<HTMLDivElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const webcamVideoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const fps =
    scene?.processing?.fps ??
    (scene?.processing?.inference_ms ? 1000 / scene.processing.inference_ms : 19.5);
  const inferenceMs = scene?.processing?.inference_ms ?? 50.4;

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setIsProcessing(true);
      setMediaSource("upload");
      const res = await uploadImage(file);
      if (res.success && res.scene) {
        onSceneUpdated(res.scene, res.annotated_image_base64 || "");
      }
    } catch (err: any) {
      alert(`Image processing failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVideoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setIsProcessing(true);
      setMediaSource("video");
      const res = await uploadVideo(file);
      if (res.success && res.latest_scene) {
        onSceneUpdated(res.latest_scene, "");
      }
    } catch (err: any) {
      alert(`Video processing failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLoadSample = async () => {
    try {
      setIsProcessing(true);
      stopWebcam();
      setMediaSource("sample");
      const res = await detectImagePath("sample_data/bus.jpg");
      if (res.success && res.scene) {
        onSceneUpdated(res.scene, res.annotated_image_base64 || "");
      }
    } catch (err) {
      console.error("Failed to load sample:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const startWebcam = async () => {
    try {
      setIsProcessing(true);
      setMediaSource("webcam");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      streamRef.current = stream;
      if (webcamVideoRef.current) {
        webcamVideoRef.current.srcObject = stream;
        webcamVideoRef.current.play();
      }
    } catch (err: any) {
      alert(`Camera access notice: ${err.message || "Could not access webcam"}`);
      setMediaSource("sample");
    } finally {
      setIsProcessing(false);
    }
  };

  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, []);

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (document.fullscreenElement) {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    } else {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    }
  };

  const handleDownloadSnapshot = () => {
    if (!annotatedImageBase64) return;
    const a = document.createElement("a");
    a.href = `data:image/jpeg;base64/${annotatedImageBase64}`;
    a.download = `telemetry_snapshot_${Date.now()}.jpg`;
    a.click();
  };

  const gridSectors = [
    "TOP_LEFT [0,0]", "TOP_CENTER [0,1]", "TOP_RIGHT [0,2]",
    "CENTER_LEFT [1,0]", "CENTER [1,1]", "CENTER_RIGHT [1,2]",
    "BOTTOM_LEFT [2,0]", "BOTTOM_CENTER [2,1]", "BOTTOM_RIGHT [2,2]",
  ];

  return (
    <div
      ref={containerRef}
      className="panel flex flex-col overflow-hidden select-none bg-[#090d14] border border-zinc-800 rounded-none"
    >
      {/* Telemetry Header */}
      <div className="h-8 px-3 bg-[#080b11] border-b border-zinc-800 flex items-center justify-between gap-3 text-xs rounded-none">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-mono">
            <span className={`status-dot ${isStreaming ? "active" : "idle"}`} />
            <span className="font-semibold text-zinc-200 uppercase text-[10px] tracking-wider">
              {isStreaming ? "STREAM: ACTIVE" : "STREAM: STANDBY"}
            </span>
          </div>

          <div className="h-3 w-px bg-zinc-800" />

          <div className="flex items-center gap-1 text-[10px] text-zinc-400 font-mono">
            <span className="text-zinc-500">SRC:</span>
            <span className="font-medium text-zinc-200 uppercase">[{mediaSource}]</span>
          </div>

          <div className="hidden sm:flex items-center gap-1 text-[10px] text-zinc-400 font-mono">
            <span className="text-zinc-500">FPS:</span>
            <span className="text-zinc-200 font-semibold">{fps.toFixed(1)}</span>
          </div>

          <div className="hidden sm:flex items-center gap-1 text-[10px] text-zinc-400 font-mono">
            <span className="text-zinc-500">INFER:</span>
            <span className="text-zinc-200">{inferenceMs.toFixed(1)}ms</span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowGrid(!showGrid)}
            title="Toggle 3x3 Spatial Grid"
            className={`flex items-center gap-1 px-2 py-0.5 rounded-none text-[10px] font-mono border transition-colors ${
              showGrid
                ? "bg-sky-950/40 text-sky-400 border-sky-800/80"
                : "bg-zinc-900 text-zinc-500 border-zinc-800 hover:text-zinc-300"
            }`}
          >
            <Grid className="w-2.5 h-2.5" />
            <span>GRID:{showGrid ? "ON" : "OFF"}</span>
          </button>

          <button
            onClick={() => setIsPaused(!isPaused)}
            title={isPaused ? "Resume feed" : "Pause feed"}
            className="p-1 rounded-none bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            {isPaused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
          </button>

          <button
            onClick={handleDownloadSnapshot}
            disabled={!annotatedImageBase64}
            title="Download snapshot"
            className="p-1 rounded-none bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors disabled:opacity-30"
          >
            <Download className="w-3 h-3" />
          </button>

          <button
            onClick={toggleFullscreen}
            title="Toggle fullscreen"
            className="p-1 rounded-none bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            {isFullscreen ? <Minimize2 className="w-3 h-3" /> : <Maximize2 className="w-3 h-3" />}
          </button>
        </div>
      </div>

      {/* Main Canvas Viewport Area */}
      <div className="relative aspect-video w-full bg-[#05070a] flex items-center justify-center overflow-hidden group">
        {mediaSource === "webcam" ? (
          <video
            ref={webcamVideoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-contain"
          />
        ) : annotatedImageBase64 ? (
          <img
            src={`data:image/jpeg;base64,${annotatedImageBase64}`}
            alt="YOLO Detection Telemetry"
            className="w-full h-full object-contain"
          />
        ) : (
          /* Engineering Schematic Canvas Placeholder */
          <div className="absolute inset-0 schematic-canvas-bg flex flex-col items-center justify-center text-center p-4">
            {/* 2D Coordinate Grid Ticks and Dead Center Thin Crosshairs */}
            <div className="relative w-44 h-44 flex items-center justify-center pointer-events-none">
              {/* Outer reticle circle */}
              <div className="absolute w-36 h-36 border border-zinc-800/80 rounded-none pointer-events-none" />
              <div className="absolute w-20 h-20 border border-dashed border-zinc-700/50 pointer-events-none" />

              {/* Dead center crosshairs (+) */}
              <div className="absolute w-full h-[1px] bg-zinc-700/60" />
              <div className="absolute h-full w-[1px] bg-zinc-700/60" />
              
              {/* Center crosshair + mark */}
              <div className="relative w-6 h-6 flex items-center justify-center">
                <div className="absolute w-4 h-[1.5px] bg-sky-400/80" />
                <div className="absolute h-4 w-[1.5px] bg-sky-400/80" />
                <div className="w-1.5 h-1.5 border border-sky-400/80 bg-zinc-950" />
              </div>

              {/* Axis labels */}
              <span className="absolute top-1 text-[8px] font-mono text-zinc-600 tracking-tighter">+Y [0.00]</span>
              <span className="absolute bottom-1 text-[8px] font-mono text-zinc-600 tracking-tighter">-Y [1.00]</span>
              <span className="absolute left-1 text-[8px] font-mono text-zinc-600 tracking-tighter">-X [0.00]</span>
              <span className="absolute right-1 text-[8px] font-mono text-zinc-600 tracking-tighter">+X [1.00]</span>
            </div>

            {/* Terminal Minimalist Labels */}
            <div className="mt-2 space-y-1">
              <div className="font-mono text-xs font-semibold text-zinc-300 tracking-wider">
                [AWAITING_MEDIA_STREAM_MOUNT]
              </div>
              <div className="font-mono text-[10px] text-zinc-500 uppercase tracking-tight">
                DEV: /DEV/VIDEO0 • ADAPTER: ONNX/CUDA • PROTOCOL: TCP/WS_STREAM
              </div>
              <div className="font-mono text-[9px] text-zinc-600 tracking-widest mt-0.5">
                MOUNT MEDIA VIA CONTROL RIBBON BELOW
              </div>
            </div>
          </div>
        )}

        {/* 3x3 Coordinate Projection Grid Overlay */}
        {showGrid && (
          <div className="absolute inset-0 grid grid-cols-3 grid-rows-3 pointer-events-none border border-sky-500/20">
            {gridSectors.map((sector) => (
              <div
                key={sector}
                className="border border-sky-500/10 p-1 flex items-start justify-between"
              >
                <span className="text-[8px] font-mono text-sky-400/70 bg-black/80 px-1 py-0.2 border border-sky-500/20">
                  {sector}
                </span>
                <span className="text-[7px] font-mono text-zinc-700 select-none">+</span>
              </div>
            ))}
          </div>
        )}

        {/* Top-Right Entity Count Badge */}
        <div className="absolute top-2 right-2 pointer-events-none flex items-center gap-1.5">
          <div className="px-2 py-0.5 rounded-none bg-black/90 border border-zinc-800 text-[9px] font-mono text-zinc-300 backdrop-blur-xs flex items-center gap-1">
            <span className="text-zinc-500">OBJECTS:</span>
            <span className="text-sky-400 font-semibold">
              {scene?.objects?.length ?? 0}
            </span>
          </div>
        </div>

        {/* Processing Spinner Overlay */}
        {isProcessing && (
          <div className="absolute inset-0 bg-black/70 flex items-center justify-center gap-2 text-xs text-sky-400 font-mono">
            <div className="w-3.5 h-3.5 border-2 border-sky-400 border-t-transparent rounded-none animate-spin" />
            <span>[INFERENCE_PIPELINE_EXECUTING]</span>
          </div>
        )}
      </div>

      {/* Bottom Control Ribbon */}
      <div className="p-1.5 bg-[#080b11] border-t border-zinc-800 flex flex-wrap items-center justify-between gap-1.5 rounded-none">
        <div className="flex items-center gap-1">
          <button
            onClick={handleLoadSample}
            className={`px-2 py-0.5 text-[11px] font-mono border rounded-none transition-colors ${
              mediaSource === "sample"
                ? "bg-zinc-800 text-sky-400 border-sky-500/40"
                : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border-zinc-800"
            }`}
          >
            SAMPLE_INPUT
          </button>

          <input
            type="file"
            ref={imageInputRef}
            onChange={handleImageUpload}
            accept="image/*"
            className="hidden"
          />
          <button
            onClick={() => imageInputRef.current?.click()}
            className={`px-2 py-0.5 text-[11px] font-mono border rounded-none flex items-center gap-1 transition-colors ${
              mediaSource === "upload"
                ? "bg-zinc-800 text-sky-400 border-sky-500/40"
                : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border-zinc-800"
            }`}
          >
            <Upload className="w-3 h-3 text-zinc-500" />
            <span>MOUNT_IMAGE</span>
          </button>

          <input
            type="file"
            ref={videoInputRef}
            onChange={handleVideoUpload}
            accept="video/*"
            className="hidden"
          />
          <button
            onClick={() => videoInputRef.current?.click()}
            className={`px-2 py-0.5 text-[11px] font-mono border rounded-none flex items-center gap-1 transition-colors ${
              mediaSource === "video"
                ? "bg-zinc-800 text-sky-400 border-sky-500/40"
                : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border-zinc-800"
            }`}
          >
            <Film className="w-3 h-3 text-zinc-500" />
            <span>MOUNT_VIDEO</span>
          </button>

          <button
            onClick={mediaSource === "webcam" ? stopWebcam : startWebcam}
            className={`px-2 py-0.5 text-[11px] font-mono border rounded-none flex items-center gap-1 transition-colors ${
              mediaSource === "webcam"
                ? "bg-emerald-950/40 text-emerald-400 border-emerald-700"
                : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border-zinc-800"
            }`}
          >
            <Camera className="w-3 h-3 text-zinc-500" />
            <span>{mediaSource === "webcam" ? "DETACH_CAMERA" : "ATTACH_CAMERA"}</span>
          </button>
        </div>

        <div className="text-[10px] font-mono text-zinc-500">
          PLANE: {scene?.frame_width || 810}x{scene?.frame_height || 1080} PX
        </div>
      </div>
    </div>
  );
};

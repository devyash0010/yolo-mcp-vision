import React, { useEffect, useRef, useState } from "react";
import { SceneContext } from "../types";
import { detectFrame, detectImagePath, uploadImage, uploadVideo } from "../services/api";
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
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [videoStats, setVideoStats] = useState<{ filename: string; frames: number; detections: number } | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const webcamVideoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement>(null);
  const detectTimerRef = useRef<number | null>(null);
  const inFlightRef = useRef<boolean>(false);
  const pausedRef = useRef<boolean>(false);
  const videoUrlRef = useRef<string | null>(null);

  const fps =
    scene?.processing?.fps ??
    (scene?.processing?.inference_ms ? 1000 / scene.processing.inference_ms : 19.5);
  const inferenceMs = scene?.processing?.inference_ms ?? 50.4;

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setIsProcessing(true);
      stopWebcam();
      clearOverlay();
      releaseVideoUrl();
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
      stopWebcam();
      clearOverlay();
      releaseVideoUrl();
      setMediaSource("video");
      const url = URL.createObjectURL(file);
      videoUrlRef.current = url;
      setVideoUrl(url);
      setVideoStats(null);

      const res = await uploadVideo(file);
      if (res.success && res.latest_scene) {
        onSceneUpdated(res.latest_scene, "");
        setVideoStats({
          filename: file.name,
          frames: res.frames_analyzed,
          detections: res.total_detections,
        });
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
      clearOverlay();
      releaseVideoUrl();
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

  const releaseVideoUrl = () => {
    if (videoUrlRef.current) {
      URL.revokeObjectURL(videoUrlRef.current);
      videoUrlRef.current = null;
    }
    setVideoUrl(null);
  };

  const clearOverlay = () => {
    const canvas = overlayCanvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (canvas && ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  const drawLiveOverlay = (sc: SceneContext | null) => {
    const canvas = overlayCanvasRef.current;
    const video = webcamVideoRef.current;
    if (!canvas || !video) return;
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    canvas.width = rect.width;
    canvas.height = rect.height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!sc || !video.videoWidth || !video.videoHeight) return;

    // object-contain fit of the video inside the viewport
    const scale = Math.min(canvas.width / video.videoWidth, canvas.height / video.videoHeight);
    const dw = video.videoWidth * scale;
    const dh = video.videoHeight * scale;
    const ox = (canvas.width - dw) / 2;
    const oy = (canvas.height - dh) / 2;
    const sx = dw / sc.frame_width;
    const sy = dh / sc.frame_height;

    // Same palette order as the backend annotate_frame()
    const colors = ["#2ecc71", "#3498db", "#e74c3c", "#9b59b6", "#f1c40f", "#e67e22", "#1abc9c"];

    ctx.lineWidth = 2;
    ctx.font = "11px monospace";
    for (const d of sc.objects) {
      const color = colors[d.class_id % colors.length];
      const x1 = ox + d.bbox.x1 * sx;
      const y1 = oy + d.bbox.y1 * sy;
      const x2 = ox + d.bbox.x2 * sx;
      const y2 = oy + d.bbox.y2 * sy;
      ctx.strokeStyle = color;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
      ctx.beginPath();
      ctx.arc((x1 + x2) / 2, (y1 + y2) / 2, 3, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      let label = `${d.class_name} ${Math.round(d.confidence * 100)}%`;
      if (d.track_id != null) label = `#${d.track_id} ${label}`;
      const tw = ctx.measureText(label).width;
      const ly = Math.max(0, y1 - 16);
      ctx.fillStyle = color;
      ctx.fillRect(x1, ly, tw + 8, 16);
      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, x1 + 4, ly + 11);
    }
  };

  const detectLoop = async () => {
    if (inFlightRef.current || pausedRef.current || !streamRef.current) return;
    const video = webcamVideoRef.current;
    const canvas = captureCanvasRef.current;
    if (!video || !canvas || !video.videoWidth) return;

    const capW = 640;
    const capH = Math.round((capW * video.videoHeight) / video.videoWidth);
    canvas.width = capW;
    canvas.height = capH;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, capW, capH);

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, "image/jpeg", 0.8)
    );
    if (!blob) return;

    inFlightRef.current = true;
    try {
      const res = await detectFrame(blob, true);
      if (res.success && res.scene && streamRef.current) {
        drawLiveOverlay(res.scene);
        onSceneUpdated(res.scene, "");
      }
    } catch (err) {
      console.error("Live frame detection failed:", err);
    } finally {
      inFlightRef.current = false;
    }
  };

  const stopDetectionLoop = () => {
    if (detectTimerRef.current !== null) {
      window.clearInterval(detectTimerRef.current);
      detectTimerRef.current = null;
    }
    inFlightRef.current = false;
  };

  const startDetectionLoop = () => {
    stopDetectionLoop();
    detectTimerRef.current = window.setInterval(detectLoop, 400);
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
      clearOverlay();
      startDetectionLoop();
    } catch (err: any) {
      alert(`Camera access notice: ${err.message || "Could not access webcam"}`);
      setMediaSource("sample");
    } finally {
      setIsProcessing(false);
    }
  };

  const stopWebcam = () => {
    stopDetectionLoop();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    clearOverlay();
  };

  useEffect(() => {
    return () => {
      stopWebcam();
      if (videoUrlRef.current) URL.revokeObjectURL(videoUrlRef.current);
    };
  }, []);

  useEffect(() => {
    pausedRef.current = isPaused;
  }, [isPaused]);

  // Re-attach the camera stream if the <video> element remounts after source switches
  useEffect(() => {
    if (mediaSource === "webcam" && streamRef.current && webcamVideoRef.current && !webcamVideoRef.current.srcObject) {
      webcamVideoRef.current.srcObject = streamRef.current;
      webcamVideoRef.current.play().catch(() => {});
    }
  }, [mediaSource]);

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (document.fullscreenElement) {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    } else {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    }
  };

  const handleDownloadSnapshot = () => {
    if (mediaSource === "webcam" && webcamVideoRef.current && webcamVideoRef.current.videoWidth) {
      const video = webcamVideoRef.current;
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(video, 0, 0);
      if (scene && scene.frame_width > 0) {
        const sx = canvas.width / scene.frame_width;
        const sy = canvas.height / scene.frame_height;
        const colors = ["#2ecc71", "#3498db", "#e74c3c", "#9b59b6", "#f1c40f", "#e67e22", "#1abc9c"];
        ctx.lineWidth = 2;
        ctx.font = "12px monospace";
        for (const d of scene.objects) {
          const color = colors[d.class_id % colors.length];
          const x1 = d.bbox.x1 * sx;
          const y1 = d.bbox.y1 * sy;
          const x2 = d.bbox.x2 * sx;
          const y2 = d.bbox.y2 * sy;
          ctx.strokeStyle = color;
          ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
          let label = `${d.class_name} ${Math.round(d.confidence * 100)}%`;
          if (d.track_id != null) label = `#${d.track_id} ${label}`;
          const tw = ctx.measureText(label).width;
          const ly = Math.max(0, y1 - 16);
          ctx.fillStyle = color;
          ctx.fillRect(x1, ly, tw + 8, 16);
          ctx.fillStyle = "#ffffff";
          ctx.fillText(label, x1 + 4, ly + 11);
        }
      }
      const a = document.createElement("a");
      a.href = canvas.toDataURL("image/jpeg");
      a.download = `live_snapshot_${Date.now()}.jpg`;
      a.click();
      return;
    }
    if (!annotatedImageBase64) return;
    const a = document.createElement("a");
    a.href = `data:image/jpeg;base64,${annotatedImageBase64}`;
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
          <>
            <video
              ref={webcamVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-contain"
            />
            <canvas
              ref={overlayCanvasRef}
              className="absolute inset-0 w-full h-full pointer-events-none"
            />
          </>
        ) : mediaSource === "video" && videoUrl ? (
          <video
            key={videoUrl}
            src={videoUrl}
            controls
            autoPlay
            loop
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

        {/* Hidden frame-capture surface for live webcam inference */}
        <canvas ref={captureCanvasRef} className="hidden" />

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

        <div className="flex items-center gap-3 text-[10px] font-mono">
          {mediaSource === "webcam" && (
            <span className="flex items-center gap-1 text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              LIVE_YOLO_INFERENCE
            </span>
          )}
          {mediaSource === "video" && videoStats && (
            <>
              <span className="text-zinc-500 truncate max-w-[140px]">{videoStats.filename}</span>
              <span className="text-zinc-500">FRAMES:</span>
              <span className="text-sky-400">{videoStats.frames}</span>
              <span className="text-zinc-500">DETS:</span>
              <span className="text-emerald-400">{videoStats.detections}</span>
            </>
          )}
          <span className="text-zinc-500">
            PLANE: {scene?.frame_width || 810}x{scene?.frame_height || 1080} PX
          </span>
        </div>
      </div>
    </div>
  );
};

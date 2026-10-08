import React, { useEffect, useState } from "react";
import { Sidebar, NavTabId } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { OverviewView } from "./components/OverviewView";
import { LiveVisionView } from "./components/LiveVisionView";
import { ScenesView } from "./components/ScenesView";
import { DetectionsView } from "./components/DetectionsView";
import { MCPToolsView } from "./components/MCPToolsView";
import { SystemView } from "./components/SystemView";
import { SettingsView } from "./components/SettingsView";
import { MetricsSummary, SceneContext, SystemStatus } from "./types";
import {
  detectImagePath,
  fetchCurrentScene,
  fetchMetrics,
  fetchSystemStatus,
} from "./services/api";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTabId>("overview");
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [scene, setScene] = useState<SceneContext | null>(null);
  const [annotatedBase64, setAnnotatedBase64] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isInitializing, setIsInitializing] = useState<boolean>(true);

  const refreshData = async () => {
    try {
      setIsRefreshing(true);
      const [sys, met, scn] = await Promise.all([
        fetchSystemStatus().catch(() => null),
        fetchMetrics().catch(() => null),
        fetchCurrentScene().catch(() => null),
      ]);
      if (sys) setStatus(sys);
      if (met) setMetrics(met);
      if (scn) {
        setScene(scn);
      } else {
        // Fallback to loading sample bus image if no current scene is in buffer
        const sampleRes = await detectImagePath("sample_data/bus.jpg").catch(() => null);
        if (sampleRes?.scene) {
          setScene(sampleRes.scene);
          if (sampleRes.annotated_image_base64) {
            setAnnotatedBase64(sampleRes.annotated_image_base64);
          }
        }
      }
    } catch (err) {
      console.error("Initialization error:", err);
    } finally {
      setIsRefreshing(false);
      setIsInitializing(false);
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(async () => {
      try {
        const [sys, met] = await Promise.all([
          fetchSystemStatus().catch(() => null),
          fetchMetrics().catch(() => null),
        ]);
        if (sys) setStatus(sys);
        if (met) setMetrics(met);
      } catch {}
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/detection`;

    let ws: WebSocket;
    let reconnectTimeout: any;

    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === "initial_scene" && msg.scene) {
              setScene(msg.scene);
            } else if (msg.timestamp && msg.objects) {
              setScene(msg);
            }
          } catch {}
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch {
        reconnectTimeout = setTimeout(connect, 4000);
      }
    };

    connect();

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  const handleSceneUpdated = (newScene: SceneContext, base64: string) => {
    setScene(newScene);
    if (base64) setAnnotatedBase64(base64);
  };

  const calculatedFps =
    scene?.processing?.fps ??
    metrics?.estimated_fps ??
    (metrics?.average_inference_ms ? 1000 / metrics.average_inference_ms : 19.5);

  const renderActiveView = () => {
    switch (activeTab) {
      case "overview":
        return (
          <OverviewView
            scene={scene}
            metrics={metrics}
            annotatedBase64={annotatedBase64}
            onSceneUpdated={handleSceneUpdated}
            wsConnected={wsConnected}
          />
        );
      case "live":
        return (
          <LiveVisionView
            scene={scene}
            annotatedBase64={annotatedBase64}
            onSceneUpdated={handleSceneUpdated}
            wsConnected={wsConnected}
          />
        );
      case "scenes":
        return <ScenesView />;
      case "detections":
        return <DetectionsView scene={scene} />;
      case "mcp":
        return <MCPToolsView />;
      case "system":
        return <SystemView status={status} metrics={metrics} wsConnected={wsConnected} />;
      case "settings":
        return <SettingsView />;
    }
  };

  return (
    <div className="min-h-screen flex bg-[#080b11] text-zinc-100 antialiased font-sans select-none">
      {/* 4. Side Navigation with tight utility margins */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        status={status}
        wsConnected={wsConnected}
      />

      {/* Main Viewport Column */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        {/* Top Control Bar */}
        <TopBar
          activeTab={activeTab}
          status={status}
          wsConnected={wsConnected}
          fps={calculatedFps}
          onRefresh={refreshData}
          isRefreshing={isRefreshing}
        />

        {/* Viewport Workspace */}
        <main className="flex-1 overflow-y-auto p-2 md:p-3">
          {isInitializing ? (
            <div className="h-full flex flex-col items-center justify-center text-zinc-500 gap-2 font-mono">
              <div className="w-4 h-4 border-2 border-sky-400 border-t-transparent animate-spin" />
              <span className="text-xs">[INITIALIZING_VISION_PIPELINE & MCP_DAEMON]</span>
            </div>
          ) : (
            renderActiveView()
          )}
        </main>

        {/* Production Telemetry Footer */}
        <footer className="h-6 px-3 bg-[#080b11] border-t border-zinc-800 flex items-center justify-between text-[9px] font-mono text-zinc-600 select-none">
          <div>
            <span>[TELEMETRY_ENGINE: ACTIVE]</span>
            <span className="mx-2">•</span>
            <span>ULTRALYTICS_YOLO11</span>
            <span className="mx-2">•</span>
            <span>MODEL_CONTEXT_PROTOCOL_SDK</span>
          </div>
          <div>
            <span>LATENCY_SYNC: OK</span>
            <span className="mx-2">•</span>
            <span>FRAME_BUFFER: MOUNTED</span>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default App;

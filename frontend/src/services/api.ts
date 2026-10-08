import { MetricsSummary, SceneContext, SystemStatus } from "../types";

const API_BASE = "/api/v1";

export function mapIntentToTool(intent: string): string {
  switch (intent) {
    case "count_objects":
      return "count_objects";
    case "find_location":
      return "find_object_location";
    case "get_by_position":
      return "get_objects_by_position";
    case "get_relationships":
      return "get_spatial_relationships";
    case "general_query":
    case "full_scene":
      return "get_current_scene";
    case "moving_objects":
      return "get_moving_objects";
    default:
      return "query_scene";
  }
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const res = await fetch("/system/status");
  if (!res.ok) {
    throw new Error(`System status failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchMetrics(): Promise<MetricsSummary> {
  const res = await fetch("/metrics");
  if (!res.ok) {
    throw new Error(`Metrics fetch failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchCurrentScene(): Promise<SceneContext> {
  const res = await fetch(`${API_BASE}/scene/current`);
  if (!res.ok) {
    throw new Error(`Failed to fetch current scene: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchSceneHistory(limit: number = 20): Promise<SceneContext[]> {
  const res = await fetch(`${API_BASE}/scene/history?limit=${limit}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch scene history: ${res.statusText}`);
  }
  return res.json();
}

export async function queryScene(query: string): Promise<{
  answer: string;
  matched_intent: string;
  tool_used: string;
  latency_ms: number;
  confidence?: number;
}> {
  const startTime = performance.now();
  const res = await fetch(`${API_BASE}/scene/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  const latency_ms = Math.round(performance.now() - startTime);

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData?.error?.message || errData?.detail || `Query failed with status ${res.status}`);
  }

  const data = await res.json();
  return {
    ...data,
    latency_ms,
    tool_used: mapIntentToTool(data.matched_intent),
  };
}

export async function uploadImage(
  file: File,
  includeAnnotated: boolean = true
): Promise<{ success: boolean; scene?: SceneContext; annotated_image_base64?: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("include_annotated", String(includeAnnotated));
  formData.append("track", "false");

  const res = await fetch(`${API_BASE}/detection/image`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData?.error?.message || errData?.detail || "Image detection failed");
  }

  return res.json();
}

export async function detectImagePath(
  imagePath: string = "sample_data/bus.jpg"
): Promise<{ success: boolean; scene?: SceneContext; annotated_image_base64?: string }> {
  const formData = new FormData();
  formData.append("image_path", imagePath);
  formData.append("include_annotated", "true");
  formData.append("track", "true");

  const res = await fetch(`${API_BASE}/detection/image`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData?.error?.message || errData?.detail || "Sample detection failed");
  }

  return res.json();
}

export async function uploadVideo(
  file: File,
  frameStep: number = 5,
  maxFrames: number = 60
): Promise<{
  success: boolean;
  filename: string;
  frames_analyzed: number;
  total_detections: number;
  latest_scene?: SceneContext;
}> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("frame_step", String(frameStep));
  formData.append("max_frames", String(maxFrames));

  const res = await fetch(`${API_BASE}/detection/video`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData?.error?.message || errData?.detail || "Video processing failed");
  }

  return res.json();
}

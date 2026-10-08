export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width?: number;
  height?: number;
  area?: number;
}

export interface Point {
  x: number;
  y: number;
}

export interface Detection {
  id: string;
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: BoundingBox;
  center: [number, number] | Point;
  width?: number;
  height?: number;
  area?: number;
  grid_position?: string;
  relative_size?: string;
  track_id?: number | null;
  movement?: string;
}

export interface SpatialRelation {
  subject: string;
  subject_id: string;
  relation: string;
  object: string;
  object_id: string;
  confidence: number;
  distance_2d?: number | null;
}

export interface ProcessingMetrics {
  preprocess_ms?: number;
  inference_ms?: number;
  postprocess_ms?: number;
  total_ms?: number;
  fps?: number;
}

export interface SceneContext {
  scene_id: string;
  timestamp: string;
  frame_width: number;
  frame_height: number;
  objects: Detection[];
  object_counts: Record<string, number>;
  spatial_distribution: Record<string, string[]>;
  relationships: SpatialRelation[];
  summary: string;
  processing: ProcessingMetrics;
}

export interface SystemStatus {
  status: string;
  active_device: string;
  cuda_available: boolean;
  device_name?: string;
  model_loaded?: boolean;
  model_path?: string;
  confidence_threshold?: number;
  iou_threshold?: number;
  total_detections_served?: number;
  uptime_seconds?: number;
}

export interface MetricsSummary {
  total_inferences?: number;
  average_inference_ms?: number;
  p50_latency_ms?: number;
  p95_latency_ms?: number;
  p99_latency_ms?: number;
  estimated_fps?: number;
  total_objects_detected?: number;
  active_streams?: number;
  total_frames_processed?: number;
}

export interface MCPToolInfo {
  name: string;
  description: string;
  parameters?: Record<string, any>;
}

export interface MCPLogEntry {
  id: string;
  tool: string;
  query?: string;
  timestamp: string;
  status: "success" | "error";
  latency_ms: number;
  resultSummary: string;
}

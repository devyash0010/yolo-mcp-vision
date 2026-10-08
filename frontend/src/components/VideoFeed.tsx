import React from "react";
import { SceneContext } from "../types";
import { VideoViewer } from "./VideoViewer";

interface VideoFeedProps {
  scene: SceneContext | null;
  annotatedImageBase64: string | null;
  onSceneUpdated: (newScene: SceneContext, base64: string) => void;
  isStreaming?: boolean;
}

export const VideoFeed: React.FC<VideoFeedProps> = ({
  scene,
  annotatedImageBase64,
  onSceneUpdated,
  isStreaming = false,
}) => {
  return (
    <VideoViewer
      scene={scene}
      annotatedImageBase64={annotatedImageBase64}
      onSceneUpdated={onSceneUpdated}
      isStreaming={isStreaming}
    />
  );
};

export default VideoFeed;

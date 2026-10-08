import React from "react";
import { MetricStrip } from "./MetricStrip";
import { MetricsSummary, SceneContext } from "../types";

interface StatsBarProps {
  scene: SceneContext | null;
  metrics: MetricsSummary | null;
}

export const StatsBar: React.FC<StatsBarProps> = ({ scene, metrics }) => {
  return <MetricStrip scene={scene} metrics={metrics} />;
};

export default StatsBar;


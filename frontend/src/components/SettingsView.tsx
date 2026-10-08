import React, { useState } from "react";
import { Settings, Save, Check } from "lucide-react";

export const SettingsView: React.FC = () => {
  const [confThreshold, setConfThreshold] = useState<number>(0.35);
  const [iouThreshold, setIouThreshold] = useState<number>(0.45);
  const [enableTracking, setEnableTracking] = useState<boolean>(true);
  const [defaultGridOverlay, setDefaultGridOverlay] = useState<boolean>(true);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return (
    <div className="space-y-2.5 max-w-2xl select-none font-mono">
      {/* View Header */}
      <div className="border-b border-zinc-800 pb-2">
        <h2 className="text-xs font-semibold text-zinc-100 flex items-center gap-1.5 uppercase">
          <Settings className="w-3.5 h-3.5 text-sky-400" />
          INFERENCE_PIPELINE_PARAMETERS
        </h2>
        <p className="text-[10px] text-zinc-500 mt-0.5">
          Tune algorithmic confidence cutoffs, suppression bounds, and persistent tracking.
        </p>
      </div>

      <div className="panel p-3 bg-[#090d14] border border-zinc-800 rounded-none space-y-3">
        {/* Confidence Threshold */}
        <div className="flex items-center justify-between py-1.5 border-b border-zinc-900">
          <div>
            <div className="text-[11px] font-semibold text-zinc-200 uppercase">
              CONFIDENCE_THRESHOLD
            </div>
            <div className="text-[9px] text-zinc-500">
              Minimum detection probability required to retain entity proposals.
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="range"
              min="0.1"
              max="0.9"
              step="0.05"
              value={confThreshold}
              onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
              className="w-28 accent-sky-400 cursor-pointer"
            />
            <span className="text-xs text-sky-400 font-semibold w-10 text-right">
              {Math.round(confThreshold * 100)}%
            </span>
          </div>
        </div>

        {/* IoU NMS Threshold */}
        <div className="flex items-center justify-between py-1.5 border-b border-zinc-900">
          <div>
            <div className="text-[11px] font-semibold text-zinc-200 uppercase">
              IOU_NMS_THRESHOLD
            </div>
            <div className="text-[9px] text-zinc-500">
              Intersection-over-Union cutoff for suppressing duplicate bounding boxes.
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="range"
              min="0.1"
              max="0.9"
              step="0.05"
              value={iouThreshold}
              onChange={(e) => setIouThreshold(parseFloat(e.target.value))}
              className="w-28 accent-sky-400 cursor-pointer"
            />
            <span className="text-xs text-sky-400 font-semibold w-10 text-right">
              {Math.round(iouThreshold * 100)}%
            </span>
          </div>
        </div>

        {/* Multi-Object Tracking Toggle */}
        <div className="flex items-center justify-between py-1.5 border-b border-zinc-900">
          <div>
            <div className="text-[11px] font-semibold text-zinc-200 uppercase">
              BYTETRACK_TRACKING_MODE
            </div>
            <div className="text-[9px] text-zinc-500">
              Maintain unique track IDs across contiguous frames.
            </div>
          </div>
          <button
            onClick={() => setEnableTracking(!enableTracking)}
            className={`px-2 py-0.5 text-[10px] font-mono border rounded-none ${
              enableTracking
                ? "bg-sky-950/50 text-sky-400 border-sky-800"
                : "bg-zinc-900 text-zinc-500 border-zinc-800"
            }`}
          >
            {enableTracking ? "ENABLED" : "DISABLED"}
          </button>
        </div>

        {/* Default Grid Overlay Toggle */}
        <div className="flex items-center justify-between py-1.5 border-b border-zinc-900">
          <div>
            <div className="text-[11px] font-semibold text-zinc-200 uppercase">
              DEFAULT_3X3_GRID_OVERLAY
            </div>
            <div className="text-[9px] text-zinc-500">
              Mount 3x3 Cartesian sectors on viewport initial start.
            </div>
          </div>
          <button
            onClick={() => setDefaultGridOverlay(!defaultGridOverlay)}
            className={`px-2 py-0.5 text-[10px] font-mono border rounded-none ${
              defaultGridOverlay
                ? "bg-sky-950/50 text-sky-400 border-sky-800"
                : "bg-zinc-900 text-zinc-500 border-zinc-800"
            }`}
          >
            {defaultGridOverlay ? "ENABLED" : "DISABLED"}
          </button>
        </div>

        {/* Save Button */}
        <div className="pt-2 flex items-center justify-between">
          <button
            onClick={handleSave}
            className="px-3 py-1 bg-sky-950/60 hover:bg-sky-900 text-sky-400 border border-sky-800 text-[10px] font-mono flex items-center gap-1.5 rounded-none transition-colors"
          >
            <Save className="w-3 h-3" />
            <span>APPLY_PARAMETERS</span>
          </button>

          {savedSuccess && (
            <span className="text-[10px] text-emerald-400 flex items-center gap-1">
              <Check className="w-3 h-3" />
              <span>CONFIG_SYNCED_SUCCESSFULLY</span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsView;

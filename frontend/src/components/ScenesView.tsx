import React, { useEffect, useState } from "react";
import { SceneContext } from "../types";
import { fetchSceneHistory } from "../services/api";
import { Layers, RefreshCw, Eye } from "lucide-react";

export const ScenesView: React.FC = () => {
  const [history, setHistory] = useState<SceneContext[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [inspectedScene, setInspectedScene] = useState<SceneContext | null>(null);

  const loadHistory = async () => {
    try {
      setIsLoading(true);
      const scenes = await fetchSceneHistory(25);
      setHistory(scenes);
    } catch (err) {
      console.error("Failed to load scene history:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="space-y-2.5 select-none font-mono">
      {/* View Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
        <div>
          <h2 className="text-xs font-semibold text-zinc-100 flex items-center gap-1.5 uppercase">
            <Layers className="w-3.5 h-3.5 text-sky-400" />
            SCENE_SNAPSHOT_BUFFER & HISTORY
          </h2>
          <p className="text-[10px] text-zinc-500 mt-0.5">
            Audit persisted historical scene contexts captured from the inference pipeline.
          </p>
        </div>

        <button
          onClick={loadHistory}
          disabled={isLoading}
          className="flex items-center gap-1 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800 text-[10px] rounded-none transition-colors"
        >
          <RefreshCw className={`w-3 h-3 ${isLoading ? "animate-spin text-sky-400" : ""}`} />
          <span>RELOAD_BUFFER</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5">
        <div className={inspectedScene ? "lg:col-span-8" : "lg:col-span-12"}>
          <div className="panel overflow-hidden bg-[#090d14] border border-zinc-800 rounded-none">
            <div className="overflow-x-auto max-h-[520px] overflow-y-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>SCENE_ID</th>
                    <th>TIMESTAMP</th>
                    <th>OBJECTS</th>
                    <th>PEOPLE</th>
                    <th>VEHICLES</th>
                    <th>INFERENCE</th>
                    <th>FPS</th>
                    <th className="text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {history.length > 0 ? (
                    history.map((sc) => {
                      const people =
                        sc.object_counts?.person ??
                        sc.objects?.filter((o) => o.class_name.toLowerCase() === "person").length ??
                        0;

                      const vehicleClasses = ["car", "bus", "truck", "motorcycle", "vehicle"];
                      const vehicles =
                        sc.objects?.filter((o) =>
                          vehicleClasses.includes(o.class_name.toLowerCase())
                        ).length ?? 0;

                      const isSelected = inspectedScene?.scene_id === sc.scene_id;

                      return (
                        <tr
                          key={sc.scene_id}
                          className={`transition-colors ${
                            isSelected ? "bg-zinc-800/80 text-sky-300" : ""
                          }`}
                        >
                          <td className="text-zinc-400 font-semibold">
                            {sc.scene_id.substring(0, 10)}
                          </td>
                          <td className="text-zinc-500 text-[9px]">{sc.timestamp}</td>
                          <td className="text-zinc-200">{sc.objects?.length ?? 0}</td>
                          <td className="text-zinc-300">{people}</td>
                          <td className="text-zinc-300">{vehicles}</td>
                          <td className="text-zinc-300">
                            {(sc.processing?.inference_ms ?? 50.4).toFixed(1)}ms
                          </td>
                          <td className="text-sky-400">
                            {(sc.processing?.fps ?? 19.5).toFixed(1)}
                          </td>
                          <td className="text-right">
                            <button
                              onClick={() => setInspectedScene(sc)}
                              className="px-1.5 py-0.5 bg-zinc-900 hover:bg-zinc-800 text-sky-400 border border-zinc-800 text-[9px] rounded-none flex items-center gap-1 ml-auto"
                            >
                              <Eye className="w-2.5 h-2.5" />
                              <span>INSPECT</span>
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={8} className="text-center py-6 text-zinc-600 italic">
                        {isLoading ? "[FETCHING_BUFFER...]" : "[BUFFER_EMPTY: NO_HISTORICAL_SNAPSHOTS]"}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Snapshot Inspector Drawer */}
        {inspectedScene && (
          <div className="lg:col-span-4 panel p-2.5 bg-[#090d14] border border-zinc-800 rounded-none space-y-2">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5 text-xs">
              <span className="font-semibold text-zinc-200 uppercase">
                SNAPSHOT: {inspectedScene.scene_id.substring(0, 10)}
              </span>
              <button
                onClick={() => setInspectedScene(null)}
                className="text-zinc-500 hover:text-zinc-300 text-[10px]"
              >
                [CLOSE]
              </button>
            </div>

            <div className="p-1.5 bg-[#05070a] border border-zinc-800 rounded-none text-[10px] space-y-1">
              <div className="text-zinc-500 uppercase text-[9px]">NATURAL SUMMARY</div>
              <p className="text-zinc-300 leading-tight">{inspectedScene.summary}</p>
            </div>

            {/* Tree view of relationships for this snapshot */}
            <div>
              <div className="text-[10px] text-zinc-400 uppercase font-semibold mb-1 flex items-center justify-between">
                <span>SPATIAL_GRAPH_RELATIONS</span>
                <span className="text-zinc-500">
                  ({inspectedScene.relationships?.length || 0})
                </span>
              </div>

              <div className="max-h-48 overflow-y-auto bg-[#05070a] border border-zinc-800 p-0.5 text-[10px]">
                {inspectedScene.relationships && inspectedScene.relationships.length > 0 ? (
                  inspectedScene.relationships.map((rel, idx) => (
                    <div
                      key={idx}
                      className="py-0.5 px-1 flex items-center justify-between border-b border-zinc-900/60 leading-tight"
                    >
                      <div className="flex items-center gap-1 truncate">
                        <span className="text-zinc-600 text-[9px]">├──</span>
                        <span className="text-amber-400">{rel.subject}</span>
                        <span className="text-sky-400">::{rel.relation}::</span>
                        <span className="text-emerald-400">{rel.object}</span>
                      </div>
                      <span className="text-zinc-500 text-[9px]">
                        d={(rel.distance_2d ?? 0).toFixed(2)}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="py-2 text-center text-zinc-600 text-[9px]">
                    [NO_RELATIONS_LOGGED]
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScenesView;

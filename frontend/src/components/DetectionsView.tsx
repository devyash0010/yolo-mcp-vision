import React, { useState } from "react";
import { Detection, SceneContext } from "../types";
import { Crosshair, Search, SlidersHorizontal } from "lucide-react";

interface DetectionsViewProps {
  scene: SceneContext | null;
}

export const DetectionsView: React.FC<DetectionsViewProps> = ({ scene }) => {
  const [selectedClass, setSelectedClass] = useState<string>("all");
  const [selectedSector, setSelectedSector] = useState<string>("all");
  const [minConfidence, setMinConfidence] = useState<number>(0.2);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedDetection, setSelectedDetection] = useState<Detection | null>(null);

  const objects = scene?.objects || [];
  const classNames = Array.from(new Set(objects.map((o) => o.class_name)));
  const sectors = Array.from(
    new Set(objects.map((o) => o.grid_position).filter(Boolean) as string[])
  );

  const filtered = objects.filter((o) => {
    const matchClass = selectedClass === "all" || o.class_name === selectedClass;
    const matchSector = selectedSector === "all" || o.grid_position === selectedSector;
    const matchConf = o.confidence >= minConfidence;
    const matchQuery =
      o.class_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      o.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchClass && matchSector && matchConf && matchQuery;
  });

  return (
    <div className="space-y-2.5 select-none font-mono">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
        <div>
          <h2 className="text-xs font-semibold text-zinc-100 flex items-center gap-1.5 uppercase">
            <Crosshair className="w-3.5 h-3.5 text-sky-400" />
            DETECTIONS_EXPLORER
          </h2>
          <p className="text-[10px] text-zinc-500 mt-0.5">
            Filter, inspect, and audit active geometric object instances in real-time.
          </p>
        </div>

        <div className="text-[10px] text-zinc-400 border border-zinc-800 px-2 py-0.5 bg-zinc-950">
          COUNT: <span className="text-sky-400 font-semibold">{filtered.length}</span> / {objects.length} ENTITIES
        </div>
      </div>

      {/* Filter Control Matrix */}
      <div className="panel p-2 bg-[#090d14] border border-zinc-800 rounded-none flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2 text-[10px]">
          <div className="relative flex items-center">
            <Search className="w-3 h-3 text-zinc-500 absolute left-1.5 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="SEARCH CLASS / ID..."
              className="pl-5 pr-2 py-0.5 bg-zinc-950 border border-zinc-800 text-zinc-200 w-36 rounded-none text-[10px]"
            />
          </div>

          <div className="flex items-center gap-1">
            <span className="text-zinc-500 uppercase">CLASS:</span>
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="py-0.5 px-1.5 bg-zinc-950 border border-zinc-800 text-zinc-200 rounded-none text-[10px]"
            >
              <option value="all">ALL CLASSES</option>
              {classNames.map((cls) => (
                <option key={cls} value={cls}>
                  {cls.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1">
            <span className="text-zinc-500 uppercase">SECTOR:</span>
            <select
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="py-0.5 px-1.5 bg-zinc-950 border border-zinc-800 text-zinc-200 rounded-none text-[10px]"
            >
              <option value="all">ALL SECTORS</option>
              {sectors.map((sec) => (
                <option key={sec} value={sec}>
                  {sec.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[10px]">
          <SlidersHorizontal className="w-3 h-3 text-zinc-500" />
          <span className="text-zinc-500 uppercase">MIN CONF:</span>
          <input
            type="range"
            min="0.1"
            max="0.9"
            step="0.05"
            value={minConfidence}
            onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
            className="w-20 accent-sky-400 cursor-pointer"
          />
          <span className="text-sky-400 font-semibold w-8 text-right">
            {Math.round(minConfidence * 100)}%
          </span>
        </div>
      </div>

      {/* Main Grid: Data Table + Detail Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2.5">
        <div className={selectedDetection ? "lg:col-span-8" : "lg:col-span-12"}>
          <div className="panel overflow-hidden bg-[#090d14] border border-zinc-800 rounded-none">
            <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>CLASS</th>
                    <th>CONF</th>
                    <th>SECTOR</th>
                    <th>SIZE</th>
                    <th>TRACK</th>
                    <th>MOTION</th>
                    <th>BBOX [X1, Y1, X2, Y2]</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length > 0 ? (
                    filtered.map((obj, idx) => {
                      const isSelected = selectedDetection?.id === obj.id;
                      const confPct = Math.round(obj.confidence * 100);
                      const isMoving = obj.movement === "moving";

                      return (
                        <tr
                          key={obj.id || idx}
                          onClick={() => setSelectedDetection(obj)}
                          className={`cursor-pointer transition-colors ${
                            isSelected ? "bg-zinc-800/90 text-sky-300" : ""
                          }`}
                        >
                          <td className="text-zinc-500">
                            #{obj.id ? obj.id.substring(0, 8) : idx + 1}
                          </td>
                          <td className="font-semibold text-zinc-200 uppercase">
                            {obj.class_name}
                          </td>
                          <td>
                            <div className="flex items-center gap-1.5">
                              <div className="w-8 h-1 bg-zinc-800 rounded-none overflow-hidden">
                                <div
                                  className="h-full bg-sky-400"
                                  style={{ width: `${confPct}%` }}
                                />
                              </div>
                              <span className="text-zinc-300">{confPct}%</span>
                            </div>
                          </td>
                          <td className="capitalize text-zinc-400">
                            {obj.grid_position ? obj.grid_position.replace("-", " ") : "—"}
                          </td>
                          <td className="uppercase text-[9px] text-zinc-400">
                            {obj.relative_size || "MED"}
                          </td>
                          <td className="text-zinc-400">
                            {obj.track_id != null ? `#${obj.track_id}` : "—"}
                          </td>
                          <td>
                            <span
                              className={`inline-flex items-center gap-1 px-1 py-0 text-[8px] border rounded-none ${
                                isMoving
                                  ? "bg-amber-950/40 text-amber-400 border-amber-800"
                                  : "bg-zinc-900 text-zinc-500 border-zinc-800"
                              }`}
                            >
                              {isMoving ? "MOVING" : "STATIC"}
                            </span>
                          </td>
                          <td className="text-[9px] text-zinc-500">
                            [{Math.round(obj.bbox.x1)}, {Math.round(obj.bbox.y1)},{" "}
                            {Math.round(obj.bbox.x2)}, {Math.round(obj.bbox.y2)}]
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={8} className="text-center py-6 text-zinc-600 italic">
                        [NO_ENTITIES_MATCH_FILTER_CRITERIA]
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Selected Entity Inspector Node */}
        {selectedDetection && (
          <div className="lg:col-span-4 panel p-2.5 bg-[#090d14] border border-zinc-800 rounded-none space-y-2">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5 text-xs">
              <span className="font-semibold text-zinc-200 uppercase">
                ENTITY_INSPECTOR: {selectedDetection.class_name}
              </span>
              <button
                onClick={() => setSelectedDetection(null)}
                className="text-zinc-500 hover:text-zinc-300 text-[10px]"
              >
                [CLOSE]
              </button>
            </div>

            <div className="space-y-1.5 text-[10px]">
              <div className="flex justify-between py-0.5 border-b border-zinc-900">
                <span className="text-zinc-500">ID:</span>
                <span className="text-zinc-300">{selectedDetection.id}</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-zinc-900">
                <span className="text-zinc-500">CLASS_ID:</span>
                <span className="text-zinc-300">{selectedDetection.class_id}</span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-zinc-900">
                <span className="text-zinc-500">CONFIDENCE:</span>
                <span className="text-sky-400 font-semibold">
                  {(selectedDetection.confidence * 100).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-zinc-900">
                <span className="text-zinc-500">GRID_SECTOR:</span>
                <span className="text-zinc-300 uppercase">
                  {selectedDetection.grid_position || "UNKNOWN"}
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-zinc-900">
                <span className="text-zinc-500">BOUNDING_BOX:</span>
                <span className="text-zinc-300">
                  [{Math.round(selectedDetection.bbox.x1)}, {Math.round(selectedDetection.bbox.y1)},{" "}
                  {Math.round(selectedDetection.bbox.x2)}, {Math.round(selectedDetection.bbox.y2)}]
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-zinc-900">
                <span className="text-zinc-500">CENTER_CARTESIAN:</span>
                <span className="text-zinc-300">
                  (
                  {Array.isArray(selectedDetection.center)
                    ? Math.round(selectedDetection.center[0])
                    : Math.round(selectedDetection.center.x)}
                  ,{" "}
                  {Array.isArray(selectedDetection.center)
                    ? Math.round(selectedDetection.center[1])
                    : Math.round(selectedDetection.center.y)}
                  )
                </span>
              </div>
              <div className="flex justify-between py-0.5 border-b border-zinc-900">
                <span className="text-zinc-500">RELATIVE_AREA:</span>
                <span className="text-zinc-300">
                  {selectedDetection.area ||
                    Math.round(
                      (selectedDetection.bbox.x2 - selectedDetection.bbox.x1) *
                        (selectedDetection.bbox.y2 - selectedDetection.bbox.y1)
                    )}{" "}
                  PX²
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DetectionsView;

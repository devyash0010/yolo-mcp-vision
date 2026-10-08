import React, { useState } from "react";
import { Detection } from "../types";
import { Crosshair, Search } from "lucide-react";

interface DetectionTableProps {
  objects: Detection[];
}

export const DetectionTable: React.FC<DetectionTableProps> = ({ objects }) => {
  const [filterText, setFilterText] = useState("");
  const [selectedSector, setSelectedSector] = useState("all");

  const sectors = Array.from(
    new Set(objects.map((o) => o.grid_position).filter(Boolean) as string[])
  );

  const filtered = objects.filter((obj) => {
    const matchesText =
      obj.class_name.toLowerCase().includes(filterText.toLowerCase()) ||
      obj.id.toLowerCase().includes(filterText.toLowerCase());
    const matchesSector =
      selectedSector === "all" || obj.grid_position === selectedSector;
    return matchesText && matchesSector;
  });

  return (
    <div className="panel overflow-hidden bg-[#090d14] border border-zinc-800 rounded-none select-none">
      {/* Panel Header */}
      <div className="h-8 px-2.5 bg-[#080b11] border-b border-zinc-800 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <Crosshair className="w-3 h-3 text-sky-400" />
          <span className="text-[11px] font-mono font-semibold text-zinc-200 uppercase tracking-tight">
            DETECTED_ENTITIES
          </span>
          <span className="text-[10px] font-mono text-zinc-500">
            [{filtered.length}/{objects.length}]
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <div className="relative flex items-center">
            <Search className="w-2.5 h-2.5 text-zinc-500 absolute left-1.5 pointer-events-none" />
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder="SEARCH..."
              className="pl-5 pr-1.5 py-0 text-[10px] bg-zinc-950 border border-zinc-800 text-zinc-300 w-28 rounded-none h-5"
            />
          </div>

          {sectors.length > 0 && (
            <select
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="text-[10px] py-0 px-1 bg-zinc-950 border border-zinc-800 text-zinc-300 rounded-none h-5"
            >
              <option value="all">ALL_SECTORS</option>
              {sectors.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* High Density Table Body */}
      <div className="overflow-x-auto max-h-60 overflow-y-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th className="w-16">ID</th>
              <th>CLASS</th>
              <th className="w-20">CONF</th>
              <th>SECTOR</th>
              <th>SIZE</th>
              <th>TRACK</th>
              <th>MOTION</th>
              <th>BBOX</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length > 0 ? (
              filtered.map((obj, idx) => {
                const confPercent = Math.round(obj.confidence * 100);
                const isMoving = obj.movement === "moving";

                return (
                  <tr key={obj.id || idx}>
                    <td className="text-zinc-500 font-mono">
                      #{obj.id ? obj.id.substring(0, 6) : idx + 1}
                    </td>
                    <td>
                      <span className="font-semibold text-zinc-200 uppercase">
                        {obj.class_name}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center gap-1.5">
                        <div className="w-8 h-1 bg-zinc-800 rounded-none overflow-hidden">
                          <div
                            className="h-full bg-sky-400 rounded-none"
                            style={{ width: `${confPercent}%` }}
                          />
                        </div>
                        <span className="text-zinc-300 font-mono text-[9px]">
                          {confPercent}%
                        </span>
                      </div>
                    </td>
                    <td className="text-zinc-400 capitalize">
                      {obj.grid_position ? obj.grid_position.replace("-", " ") : "—"}
                    </td>
                    <td className="text-zinc-400 uppercase text-[9px]">
                      {obj.relative_size || "MED"}
                    </td>
                    <td className="text-zinc-400">
                      {obj.track_id != null ? `#${obj.track_id}` : "—"}
                    </td>
                    <td>
                      <span
                        className={`inline-flex items-center gap-1 px-1 py-0 text-[8px] font-mono border rounded-none ${
                          isMoving
                            ? "bg-amber-950/40 text-amber-400 border-amber-800"
                            : "bg-zinc-900 text-zinc-500 border-zinc-800"
                        }`}
                      >
                        <span
                          className={`w-1 h-1 rounded-full ${
                            isMoving ? "bg-amber-400" : "bg-zinc-600"
                          }`}
                        />
                        {isMoving ? "MOVING" : "STATIC"}
                      </span>
                    </td>
                    <td className="text-[9px] text-zinc-500 font-mono">
                      [{Math.round(obj.bbox.x1)},{Math.round(obj.bbox.y1)},
                      {Math.round(obj.bbox.x2)},{Math.round(obj.bbox.y2)}]
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={8} className="text-center py-4 text-zinc-600 italic font-mono">
                  {objects.length === 0
                    ? "[NO_ACTIVE_DETECTIONS_IN_VIEWPORT]"
                    : "[NO_ENTITIES_MATCH_FILTER_QUERY]"}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DetectionTable;

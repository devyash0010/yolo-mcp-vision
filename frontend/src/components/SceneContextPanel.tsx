import React, { useState } from "react";
import { SceneContext } from "../types";
import { Layers, Activity } from "lucide-react";

interface SceneContextPanelProps {
  scene: SceneContext | null;
}

export const SceneContextPanel: React.FC<SceneContextPanelProps> = ({ scene }) => {
  const [filterRelation, setFilterRelation] = useState<string>("all");

  const objects = scene?.objects || [];
  const relationships = scene?.relationships || [];
  const relationTypes = Array.from(new Set(relationships.map((r) => r.relation)));

  const filteredRelations =
    filterRelation === "all"
      ? relationships
      : relationships.filter((r) => r.relation === filterRelation);

  const entityCounts = Object.entries(scene?.object_counts || {});

  return (
    <div className="panel h-full flex flex-col justify-between overflow-hidden bg-[#090d14] border border-zinc-800 rounded-none select-none">
      {/* Panel Header */}
      <div className="h-8 px-2.5 bg-[#080b11] border-b border-zinc-800 flex items-center justify-between text-xs rounded-none">
        <div className="flex items-center gap-1.5 font-mono text-[11px] text-zinc-300">
          <Layers className="w-3 h-3 text-sky-400" />
          <span className="font-semibold uppercase tracking-wider">SCENE_GRAPH</span>
          <span className="text-zinc-600">::</span>
          <span className="text-[10px] text-zinc-400">
            {objects.length} ENTITIES
          </span>
        </div>

        <div className="text-[9px] font-mono text-zinc-500">
          ID: {scene?.scene_id ? scene.scene_id.substring(0, 8) : "NIL"}
        </div>
      </div>

      <div className="p-2 space-y-2 overflow-y-auto flex-1 max-h-[560px]">
        {/* Entity Composition Bar */}
        <div>
          <div className="text-[10px] font-mono font-medium text-zinc-500 mb-1 flex items-center justify-between uppercase tracking-wider">
            <span>Entity Registry</span>
            <span className="text-[9px] text-zinc-600">{objects.length} TOTAL</span>
          </div>

          {entityCounts.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {entityCounts.map(([cls, count]) => (
                <div
                  key={cls}
                  className="px-1.5 py-0.5 rounded-none bg-zinc-950 border border-zinc-800 text-[10px] font-mono flex items-center gap-1.5"
                >
                  <span className="text-zinc-300 uppercase">{cls}</span>
                  <span className="text-sky-400 font-semibold">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-[10px] font-mono text-zinc-600 italic py-0.5">
              [NO_ACTIVE_ENTITIES_DETECTED]
            </div>
          )}
        </div>

        {/* Deterministic Natural Language Summary */}
        <div className="p-2 rounded-none bg-[#05070a] border border-zinc-800">
          <div className="text-[9px] font-mono text-zinc-500 uppercase tracking-wider mb-1 flex items-center gap-1">
            <Activity className="w-2.5 h-2.5 text-zinc-500" />
            <span>Deterministic Spatial Summary</span>
          </div>
          <p className="text-[11px] text-zinc-300 leading-snug font-mono">
            {scene?.summary || "[BUFFER_EMPTY: Ingest media feed to generate scene graph]"}
          </p>
        </div>

        {/* 2D Spatial Relationships - IDE Debugger Panel Tree View */}
        <div>
          <div className="h-6 px-1.5 bg-zinc-950 border border-zinc-800 flex items-center justify-between text-[10px] font-mono text-zinc-400 mb-1">
            <div className="flex items-center gap-1">
              <span className="text-sky-400">▼</span>
              <span className="font-semibold text-zinc-300 uppercase tracking-tight">
                2D_SPATIAL_TREE
              </span>
              <span className="text-zinc-600">({filteredRelations.length})</span>
            </div>

            {relationTypes.length > 0 && (
              <select
                value={filterRelation}
                onChange={(e) => setFilterRelation(e.target.value)}
                className="text-[9px] py-0 px-1 bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-none h-4"
              >
                <option value="all">ALL_PREDICATES ({relationships.length})</option>
                {relationTypes.map((rel) => (
                  <option key={rel} value={rel}>
                    {rel}
                  </option>
                ))}
              </select>
            )}
          </div>

          {filteredRelations.length > 0 ? (
            <div className="border border-zinc-800/80 bg-[#05070a] max-h-56 overflow-y-auto font-mono text-[10px]">
              {filteredRelations.slice(0, 30).map((rel, idx) => {
                const isLast = idx === filteredRelations.length - 1;
                const distStr =
                  rel.distance_2d !== null && rel.distance_2d !== undefined
                    ? rel.distance_2d.toFixed(2)
                    : "0.00";

                return (
                  <div
                    key={`${rel.subject_id}-${rel.relation}-${rel.object_id}-${idx}`}
                    className="py-0.5 px-1.5 flex items-center justify-between border-b border-zinc-900/60 hover:bg-zinc-900/60 transition-colors leading-tight"
                  >
                    <div className="flex items-center gap-1 truncate">
                      <span className="text-zinc-600 select-none text-[9px]">
                        {isLast ? "└──" : "├──"}
                      </span>
                      <span className="text-[9px] text-zinc-600 select-none">
                        [{String(idx).padStart(2, "0")}]
                      </span>
                      <span className="text-amber-400 font-semibold">{rel.subject}</span>
                      <span className="text-sky-400 select-none">::{rel.relation}::</span>
                      <span className="text-emerald-400 font-semibold">{rel.object}</span>
                    </div>

                    <div className="text-[9px] text-zinc-500 font-mono ml-2 flex-shrink-0">
                      d={distStr}
                    </div>
                  </div>
                );
              })}
              {filteredRelations.length > 30 && (
                <div className="text-center text-[9px] text-zinc-600 py-1 font-mono">
                  + {filteredRelations.length - 30} additional tree nodes collapsed
                </div>
              )}
            </div>
          ) : (
            <div className="text-[10px] font-mono text-zinc-600 italic py-2 text-center border border-dashed border-zinc-800">
              [NO_SPATIAL_RELATIONS_COMPUTED]
            </div>
          )}
        </div>
      </div>

      {/* Footer Basis */}
      <div className="p-1.5 bg-[#080b11] border-t border-zinc-800 flex items-center justify-between text-[9px] font-mono text-zinc-500 rounded-none">
        <span>BASIS: 2D_CARTESIAN_PLANE</span>
        <span>GRID: 3x3_EQUIDISTANT</span>
      </div>
    </div>
  );
};

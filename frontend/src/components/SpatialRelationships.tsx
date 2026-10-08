import React from "react";
import { SpatialRelation } from "../types";

interface SpatialRelationshipsProps {
  relationships: SpatialRelation[];
}

export const SpatialRelationships: React.FC<SpatialRelationshipsProps> = ({ relationships }) => {
  return (
    <div className="panel bg-[#090d14] border border-zinc-800 rounded-none overflow-hidden select-none">
      <div className="h-7 px-2.5 bg-[#080b11] border-b border-zinc-800 flex items-center justify-between text-[11px] font-mono text-zinc-300">
        <div className="flex items-center gap-1.5">
          <span className="text-sky-400">▼</span>
          <span className="font-semibold uppercase tracking-wider">DEBUGGER: 2D_SPATIAL_GRAPH</span>
        </div>
        <span className="text-[10px] text-zinc-500 font-mono">({relationships.length} relations)</span>
      </div>

      <div className="p-1 max-h-48 overflow-y-auto font-mono text-[10px] bg-[#05070a]">
        {relationships.length > 0 ? (
          relationships.map((rel, idx) => {
            const isLast = idx === relationships.length - 1;
            const dist =
              rel.distance_2d !== null && rel.distance_2d !== undefined
                ? rel.distance_2d.toFixed(2)
                : "0.00";

            return (
              <div
                key={`${rel.subject_id}-${rel.relation}-${rel.object_id}-${idx}`}
                className="py-0.5 px-1.5 flex items-center justify-between border-b border-zinc-900/60 hover:bg-zinc-900/60 transition-colors leading-tight"
              >
                <div className="flex items-center gap-1 truncate">
                  <span className="text-zinc-600 select-none text-[9px]">{isLast ? "└──" : "├──"}</span>
                  <span className="text-[9px] text-zinc-600 select-none">[{String(idx).padStart(2, "0")}]</span>
                  <span className="text-amber-400 font-semibold">{rel.subject}</span>
                  <span className="text-sky-400 select-none">::{rel.relation}::</span>
                  <span className="text-emerald-400 font-semibold">{rel.object}</span>
                </div>
                <span className="text-[9px] text-zinc-500 font-mono ml-2">d={dist}</span>
              </div>
            );
          })
        ) : (
          <div className="py-2 text-center text-zinc-600 font-mono text-[10px]">
            [NO_SPATIAL_RELATIONSHIPS_FOUND]
          </div>
        )}
      </div>
    </div>
  );
};

export default SpatialRelationships;


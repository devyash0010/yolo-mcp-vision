import React from "react";
import { Detection } from "../types";
import { DetectionTable } from "./DetectionTable";

interface ObjectTableProps {
  objects: Detection[];
}

export const ObjectTable: React.FC<ObjectTableProps> = ({ objects }) => {
  return <DetectionTable objects={objects} />;
};

export default ObjectTable;


import React, { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Handle,
  Position,
  type NodeProps,
  type Node
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { GraphNode, GraphEdge } from '../types';
import { Layers, FileCode, Sparkles } from 'lucide-react';

interface DependencyGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (nodeId: string, nodeData: GraphNode) => void;
  selectedNodeId?: string;
  cycles?: string[][];
}

// Custom Node Component
const CustomGraphNode: React.FC<NodeProps> = ({ data, selected }) => {
  const isSymbol = data.type === 'symbol';
  const label = data.label as string;
  const path = data.path as string;
  const metrics = (data.metrics || {}) as any;
  const inDegree = metrics.in_degree || 0;
  const outDegree = metrics.out_degree || 0;

  return (
    <div
      className={`px-3 py-2 rounded-lg shadow-lg border transition-all min-w-[150px] max-w-[220px] ${
        selected
          ? 'bg-cyan-950 border-cyan-400 ring-2 ring-cyan-500/50 shadow-cyan-500/20'
          : isSymbol
          ? 'bg-slate-900 border-violet-800/60 hover:border-violet-500'
          : 'bg-slate-900 border-slate-700 hover:border-cyan-500'
      }`}
    >
      <Handle type="target" position={Position.Top} className="w-2 h-2 !bg-cyan-400" />
      <div className="flex items-center space-x-2">
        {isSymbol ? (
          <Sparkles className="w-3.5 h-3.5 text-violet-400 shrink-0" />
        ) : (
          <FileCode className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
        )}
        <div className="text-xs font-semibold text-slate-100 truncate">{label}</div>
      </div>

      {path && (
        <div className="text-[10px] text-slate-400 truncate mt-0.5 font-mono">
          {path}
        </div>
      )}

      {/* Metrics Footer */}
      <div className="flex items-center justify-between text-[10px] text-slate-400 mt-2 pt-1 border-t border-slate-800">
        <span>In: <strong className="text-cyan-400">{inDegree}</strong></span>
        <span>Out: <strong className="text-violet-400">{outDegree}</strong></span>
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2 !bg-violet-400" />
    </div>
  );
};

const nodeTypes = {
  custom: CustomGraphNode
};

export const DependencyGraph: React.FC<DependencyGraphProps> = ({
  nodes: rawNodes,
  edges: rawEdges,
  onNodeClick,
  selectedNodeId,
  cycles = []
}) => {
  // Layout nodes in a structured grid or circular distribution
  const initialNodes = useMemo(() => {
    const cols = Math.max(3, Math.ceil(Math.sqrt(rawNodes.length)));
    return rawNodes.map((n, i) => {
      const row = Math.floor(i / cols);
      const col = i % cols;
      return {
        id: n.id,
        type: 'custom',
        position: { x: col * 260 + 50, y: row * 140 + 50 },
        data: n,
        selected: n.id === selectedNodeId
      };
    });
  }, [rawNodes, selectedNodeId]);

  const initialEdges = useMemo(() => {
    return rawEdges.map((e) => {
      const isCycleEdge = cycles.some(cycle => 
        cycle.includes(e.source) && cycle.includes(e.target)
      );

      return {
        id: e.id,
        source: e.source,
        target: e.target,
        animated: isCycleEdge,
        label: e.label !== 'import' ? e.label : undefined,
        style: {
          stroke: isCycleEdge ? '#ef4444' : '#0891b2',
          strokeWidth: isCycleEdge ? 2 : 1.5
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isCycleEdge ? '#ef4444' : '#0891b2'
        }
      };
    });
  }, [rawEdges, cycles]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes as any);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges as any);

  const handleNodeClick = useCallback(
    (_: any, node: any) => {
      if (onNodeClick) {
        onNodeClick(node.id, node.data);
      }
    },
    [onNodeClick]
  );

  return (
    <div className="w-full h-full bg-slate-950 rounded-lg overflow-hidden border border-slate-800 relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
      >
        <Background color="#1e293b" gap={20} size={1} />
        <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300" />
        <MiniMap
          nodeColor={(n: any) => (n.data?.type === 'symbol' ? '#8b5cf6' : '#06b6d4')}
          maskColor="rgba(11, 15, 25, 0.7)"
          className="!bg-slate-900 !border-slate-800"
        />
      </ReactFlow>

      {/* Cycle alert floating banner */}
      {cycles.length > 0 && (
        <div className="absolute top-3 right-3 bg-rose-950/90 border border-rose-800 text-rose-300 text-xs px-3 py-1.5 rounded-md shadow-lg flex items-center space-x-2 backdrop-blur-sm z-10">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
          <span><strong>{cycles.length} Cycle(s) Detected</strong> in Dependency Graph</span>
        </div>
      )}
    </div>
  );
};

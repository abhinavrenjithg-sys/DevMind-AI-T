import React, { useEffect, useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import type { DependencyGraphResponse, GraphNode } from '../types';
import { DependencyGraph } from '../components/DependencyGraph';
import { 
  GitFork, 
  Filter, 
  ExternalLink, 
  Flame, 
  FileCode, 
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const DependencyGraphPage: React.FC = () => {
  const { currentRepo } = useWorkspace();
  const navigate = useNavigate();
  const [graphData, setGraphData] = useState<DependencyGraphResponse | null>(null);
  const [nodeType, setNodeType] = useState<string>('file');
  const [relationship, setRelationship] = useState<string>('all');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadGraph = async () => {
    if (!currentRepo?.active_revision_id) return;
    setIsLoading(true);
    try {
      const data = await api.getDependencyGraph(currentRepo.active_revision_id, nodeType, relationship);
      setGraphData(data);
    } catch (err) {
      console.error('Failed to load dependency graph:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, [currentRepo, nodeType, relationship]);

  const handleNodeClick = (nodeId: string, nodeData: GraphNode) => {
    setSelectedNode(nodeData);
  };

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col p-4 space-y-3">
      {/* Top Filter and Stats Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs shrink-0">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 font-semibold text-slate-200">
            <GitFork className="w-4 h-4 text-cyan-400" />
            <span>Dependency Analysis Graph</span>
          </div>

          {graphData && (
            <div className="flex items-center space-x-2 text-slate-400 text-[11px]">
              <span><strong>{graphData.stats.total_nodes}</strong> Nodes</span>
              <span>•</span>
              <span><strong>{graphData.stats.total_edges}</strong> Edges</span>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 bg-slate-950 px-2 py-1 rounded-md border border-slate-800">
            <span className="text-slate-400 text-[11px]">Node Type:</span>
            <select
              value={nodeType}
              onChange={(e) => setNodeType(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="file" className="bg-slate-900">Files Only</option>
              <option value="symbol" className="bg-slate-900">Symbols Only</option>
              <option value="all" className="bg-slate-900">All (Files & Symbols)</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5 bg-slate-950 px-2 py-1 rounded-md border border-slate-800">
            <span className="text-slate-400 text-[11px]">Relationship:</span>
            <select
              value={relationship}
              onChange={(e) => setRelationship(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900">All Relations</option>
              <option value="import" className="bg-slate-900">Imports</option>
              <option value="calls" className="bg-slate-900">Function Calls</option>
              <option value="inherits" className="bg-slate-900">Inheritance</option>
            </select>
          </div>

          <button
            onClick={loadGraph}
            disabled={isLoading}
            className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Reload graph"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main Canvas and Inspector Split */}
      <div className="flex-1 flex gap-3 overflow-hidden">
        <div className="flex-1 h-full relative">
          {isLoading ? (
            <div className="w-full h-full bg-slate-950 rounded-lg flex items-center justify-center text-xs text-slate-400 border border-slate-800">
              Generating dependency graph...
            </div>
          ) : graphData ? (
            <DependencyGraph
              nodes={graphData.nodes}
              edges={graphData.edges}
              onNodeClick={handleNodeClick}
              selectedNodeId={selectedNode?.id}
              cycles={graphData.cycles}
            />
          ) : (
            <div className="w-full h-full bg-slate-950 rounded-lg flex items-center justify-center text-xs text-slate-400 border border-slate-800">
              Run repository analysis to generate dependency graph
            </div>
          )}
        </div>

        {/* Selected Node Inspector Drawer */}
        {selectedNode && (
          <div className="w-72 bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between overflow-y-auto shrink-0 shadow-xl">
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                  Node Inspector
                </span>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-slate-400 hover:text-slate-200 text-xs"
                >
                  ✕
                </button>
              </div>

              <div>
                <div className="flex items-center space-x-1.5">
                  {selectedNode.type === 'symbol' ? (
                    <Sparkles className="w-4 h-4 text-violet-400" />
                  ) : (
                    <FileCode className="w-4 h-4 text-cyan-400" />
                  )}
                  <h3 className="font-bold text-sm text-slate-100 truncate">
                    {selectedNode.label}
                  </h3>
                </div>
                {selectedNode.path && (
                  <p className="text-[11px] font-mono text-slate-400 mt-1 truncate">
                    {selectedNode.path}
                  </p>
                )}
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <div className="text-[10px] text-slate-400">In-Degree (Callers)</div>
                  <div className="text-base font-bold text-cyan-400">
                    {selectedNode.metrics?.in_degree || 0}
                  </div>
                </div>

                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <div className="text-[10px] text-slate-400">Out-Degree</div>
                  <div className="text-base font-bold text-violet-400">
                    {selectedNode.metrics?.out_degree || 0}
                  </div>
                </div>

                <div className="p-2 rounded bg-slate-950 border border-slate-800 col-span-2">
                  <div className="text-[10px] text-slate-400">Degree Centrality</div>
                  <div className="text-sm font-bold text-slate-200 font-mono">
                    {selectedNode.metrics?.centrality || 0}
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-2 pt-4 border-t border-slate-800 text-xs">
              <button
                onClick={() => {
                  if (selectedNode.path) {
                    navigate(`/search?file=${encodeURIComponent(selectedNode.path)}`);
                  }
                }}
                className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium transition"
              >
                <FileCode className="w-3.5 h-3.5" />
                <span>View Source Code</span>
              </button>

              <button
                onClick={() => {
                  navigate(`/impact?id=${encodeURIComponent(selectedNode.id)}&name=${encodeURIComponent(selectedNode.label)}`);
                }}
                className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 font-medium transition border border-amber-900/40"
              >
                <Flame className="w-3.5 h-3.5" />
                <span>Analyze Change Impact</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

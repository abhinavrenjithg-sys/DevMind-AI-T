import React, { useEffect, useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import type { SourceFile } from '../types';
import { 
  Layers, 
  FileCode, 
  AlertTriangle, 
  CheckCircle2, 
  ExternalLink,
  ShieldAlert
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const ArchitecturePage: React.FC = () => {
  const { currentRepo } = useWorkspace();
  const navigate = useNavigate();
  const [files, setFiles] = useState<SourceFile[]>([]);
  const [activeLayer, setActiveLayer] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!currentRepo?.active_revision_id) return;
    setIsLoading(true);
    api.getFiles(currentRepo.active_revision_id)
      .then(setFiles)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [currentRepo]);

  const stats = currentRepo?.summary_stats;
  const layers = ['Presentation', 'API / Controller', 'Business / Service', 'Data / Model', 'Core / Infrastructure', 'Test'];

  const filteredFiles = files.filter(f => activeLayer === 'all' || f.layer === activeLayer);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">Architecture Explorer</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Transparent multi-layer decomposition, entry points, and structural clustering
          </p>
        </div>

        {stats?.cycle_count ? (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-300 text-xs">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span><strong>{stats.cycle_count} Dependency Cycle(s)</strong> detected</span>
          </div>
        ) : (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Clean acyclic architecture</span>
          </div>
        )}
      </div>

      {/* Layer Filter Pills */}
      <div className="flex flex-wrap gap-2 text-xs">
        <button
          onClick={() => setActiveLayer('all')}
          className={`px-3 py-1.5 rounded-lg font-medium transition ${
            activeLayer === 'all'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
              : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
          }`}
        >
          All Layers ({files.length})
        </button>

        {layers.map((layer) => {
          const count = files.filter(f => f.layer === layer).length;
          return (
            <button
              key={layer}
              onClick={() => setActiveLayer(layer)}
              className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center space-x-1.5 ${
                activeLayer === layer
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              <span>{layer}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-400">
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Files in Selected Layer */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="p-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-200">
            {activeLayer === 'all' ? 'All Architectural Modules' : `${activeLayer} Components`}
          </span>
          <span className="text-slate-400">{filteredFiles.length} files</span>
        </div>

        {isLoading ? (
          <div className="text-center py-12 text-xs text-slate-400">Loading components...</div>
        ) : filteredFiles.length === 0 ? (
          <div className="text-center py-12 text-xs text-slate-400 italic">No files in this layer</div>
        ) : (
          <div className="divide-y divide-slate-800 max-h-[600px] overflow-y-auto">
            {filteredFiles.map((file) => (
              <div
                key={file.id}
                onClick={() => navigate(`/search?file=${encodeURIComponent(file.path)}`)}
                className="p-3 hover:bg-slate-800/60 cursor-pointer flex items-center justify-between group transition text-xs"
              >
                <div className="flex items-center space-x-3 truncate">
                  <FileCode className="w-4 h-4 text-cyan-400 shrink-0" />
                  <div className="truncate">
                    <span className="font-mono text-slate-200 group-hover:text-cyan-300 font-medium">
                      {file.path}
                    </span>
                    <div className="text-[11px] text-slate-400 flex items-center space-x-3 mt-0.5">
                      <span className="uppercase text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                        {file.layer}
                      </span>
                      <span>{file.lines_of_code} LOC</span>
                      <span>{file.symbols_count} symbols</span>
                      <span>{file.imports_count} imports</span>
                    </div>
                  </div>
                </div>

                <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-cyan-400 shrink-0 ml-2" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

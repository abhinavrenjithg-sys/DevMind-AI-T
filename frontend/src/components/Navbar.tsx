import React from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { 
  GitBranch, 
  Search, 
  Plus, 
  Layers, 
  Terminal,
  Activity
} from 'lucide-react';

interface NavbarProps {
  onOpenSearch: () => void;
  onOpenImport: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenSearch, onOpenImport }) => {
  const { 
    workspaces, 
    currentWorkspace, 
    setCurrentWorkspace, 
    repositories, 
    currentRepo, 
    setCurrentRepo 
  } = useWorkspace();

  return (
    <header className="h-14 bg-slate-900 border-b border-slate-800 px-4 flex items-center justify-between z-30 sticky top-0">
      {/* Brand & Tagline */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Layers className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-base text-slate-100 tracking-tight">DevMind AI</span>
            <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
              v1.0
            </span>
          </div>
          <span className="text-[11px] text-slate-400 hidden md:inline">
            Understand any codebase. Trace every dependency.
          </span>
        </div>
      </div>

      {/* Workspace & Repository Selectors */}
      <div className="flex items-center space-x-3">
        {/* Workspace select */}
        <div className="hidden sm:flex items-center space-x-1.5 bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800 text-xs">
          <span className="text-slate-400">Workspace:</span>
          <select
            className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer"
            value={currentWorkspace?.id || ''}
            onChange={(e) => {
              const ws = workspaces.find(w => w.id === e.target.value);
              if (ws) setCurrentWorkspace(ws);
            }}
          >
            {workspaces.map(ws => (
              <option key={ws.id} value={ws.id} className="bg-slate-900 text-slate-200">
                {ws.name}
              </option>
            ))}
          </select>
        </div>

        {/* Repository select */}
        <div className="flex items-center space-x-2 bg-slate-950 px-3 py-1 rounded-md border border-slate-800 text-xs">
          <GitBranch className="w-3.5 h-3.5 text-cyan-400" />
          <select
            className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer max-w-[140px] sm:max-w-[200px] truncate"
            value={currentRepo?.id || ''}
            onChange={(e) => {
              const r = repositories.find(item => item.id === e.target.value);
              if (r) setCurrentRepo(r);
            }}
          >
            {repositories.length === 0 ? (
              <option value="" disabled className="bg-slate-900 text-slate-400">No Repositories</option>
            ) : (
              repositories.map(r => (
                <option key={r.id} value={r.id} className="bg-slate-900 text-slate-200">
                  {r.name}
                </option>
              ))
            )}
          </select>
          {currentRepo && (
            <span className={`w-2 h-2 rounded-full ${currentRepo.is_analyzed ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]' : 'bg-amber-400'}`} title={currentRepo.is_analyzed ? "Analyzed" : "Pending Analysis"} />
          )}
        </div>

        {/* Global Quick Search */}
        <button
          onClick={onOpenSearch}
          className="flex items-center space-x-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 px-3 py-1.5 rounded-md text-xs transition"
          title="Quick Code Search (Ctrl+K)"
        >
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <span className="hidden md:inline">Quick Search...</span>
          <kbd className="hidden md:inline bg-slate-800 text-slate-400 px-1 py-0.5 rounded text-[10px]">Ctrl+K</kbd>
        </button>

        {/* Import Repo Button */}
        <button
          onClick={onOpenImport}
          className="flex items-center space-x-1.5 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white font-medium text-xs px-3 py-1.5 rounded-md transition shadow-md shadow-cyan-600/20"
        >
          <Plus className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Import Repository</span>
        </button>
      </div>
    </header>
  );
};

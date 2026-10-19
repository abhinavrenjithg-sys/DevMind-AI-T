import React, { useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import type { Repository } from '../types';
import { 
  GitBranch, 
  Trash2, 
  Play, 
  CheckCircle2, 
  Clock, 
  FolderGit2, 
  ExternalLink,
  Plus
} from 'lucide-react';

interface RepositoriesPageProps {
  onOpenImport: () => void;
}

export const RepositoriesPage: React.FC<RepositoriesPageProps> = ({ onOpenImport }) => {
  const { repositories, currentRepo, setCurrentRepo, refreshRepositories } = useWorkspace();
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);

  const handleRunAnalysis = async (repo: Repository) => {
    setAnalyzingId(repo.id);
    try {
      await api.startAnalysis(repo.id);
      await refreshRepositories();
    } catch (err) {
      console.error('Failed to trigger analysis:', err);
    } finally {
      setAnalyzingId(null);
    }
  };

  const handleDelete = async (repo: Repository) => {
    if (confirm(`Are you sure you want to delete repository "${repo.name}"?`)) {
      try {
        await api.deleteRepository(repo.id);
        await refreshRepositories();
      } catch (err) {
        console.error('Failed to delete repository:', err);
      }
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">Repository Management</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Ingest and manage codebases for reverse-engineering and dependency indexing
          </p>
        </div>

        <button
          onClick={onOpenImport}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white text-xs font-medium transition shadow-md shadow-cyan-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>Import Repository</span>
        </button>
      </div>

      {repositories.length === 0 ? (
        <div className="text-center py-16 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
          <FolderGit2 className="w-12 h-12 text-slate-400 mx-auto" />
          <h3 className="font-semibold text-slate-200 text-sm">No Repositories Ingested Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Import a public Git repository or upload a ZIP archive to parse its source code, build dependency graphs, and ask questions.
          </p>
          <button
            onClick={onOpenImport}
            className="px-4 py-2 rounded-md bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition inline-flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Import First Repository</span>
          </button>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold text-[10px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Repository</th>
                <th className="py-3 px-4">Source Type</th>
                <th className="py-3 px-4">Branch / Commit</th>
                <th className="py-3 px-4">Code Metrics</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {repositories.map((repo) => {
                const isSelected = currentRepo?.id === repo.id;
                const stats = repo.summary_stats;

                return (
                  <tr
                    key={repo.id}
                    className={`hover:bg-slate-800/50 transition ${
                      isSelected ? 'bg-cyan-950/20' : ''
                    }`}
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        <FolderGit2 className="w-4 h-4 text-cyan-400 shrink-0" />
                        <div>
                          <div className="font-semibold text-slate-100 flex items-center space-x-2">
                            <span>{repo.name}</span>
                            {isSelected && (
                              <span className="text-[10px] uppercase font-bold text-cyan-400 bg-cyan-950 px-1.5 py-0.2 rounded border border-cyan-800">
                                Active
                              </span>
                            )}
                          </div>
                          {repo.remote_url && (
                            <a
                              href={repo.remote_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[11px] text-slate-400 hover:text-cyan-300 flex items-center space-x-1 mt-0.5 truncate max-w-xs"
                            >
                              <span className="truncate">{repo.remote_url}</span>
                              <ExternalLink className="w-3 h-3 shrink-0" />
                            </a>
                          )}
                        </div>
                      </div>
                    </td>

                    <td className="py-3 px-4 uppercase text-[10px] font-semibold text-slate-400">
                      {repo.source_type === 'git_url' ? 'Git Clone' : 'ZIP Upload'}
                    </td>

                    <td className="py-3 px-4 font-mono text-[11px]">
                      <div className="flex items-center space-x-1.5">
                        <GitBranch className="w-3.5 h-3.5 text-slate-400" />
                        <span>{repo.default_branch}</span>
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      {stats ? (
                        <div className="space-y-0.5 text-[11px]">
                          <div><strong className="text-slate-100">{stats.total_files}</strong> files • <strong className="text-slate-100">{stats.total_loc?.toLocaleString()}</strong> LOC</div>
                          <div className="text-slate-400">{stats.total_symbols} symbols • {stats.total_edges} edges</div>
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">Not analyzed yet</span>
                      )}
                    </td>

                    <td className="py-3 px-4">
                      {repo.is_analyzed ? (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Indexed</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-950 text-amber-300 border border-amber-800">
                          <Clock className="w-3 h-3" />
                          <span>Pending</span>
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => setCurrentRepo(repo)}
                        disabled={isSelected}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition disabled:opacity-40"
                      >
                        {isSelected ? 'Selected' : 'Select'}
                      </button>

                      <button
                        onClick={() => handleRunAnalysis(repo)}
                        disabled={analyzingId === repo.id}
                        className="p-1.5 rounded bg-cyan-600/20 hover:bg-cyan-600/40 text-cyan-300 transition"
                        title="Re-run static analysis job"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                      </button>

                      <button
                        onClick={() => handleDelete(repo)}
                        className="p-1.5 rounded bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 transition"
                        title="Delete repository"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

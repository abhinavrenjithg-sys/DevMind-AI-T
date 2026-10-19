import React, { useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import { 
  GitCompare, 
  FileCode, 
  Sparkles, 
  TestTube, 
  AlertCircle,
  PlusCircle,
  MinusCircle,
  RefreshCw
} from 'lucide-react';

export const RevisionComparePage: React.FC = () => {
  const { currentRepo } = useWorkspace();
  const [baseRev, setBaseRev] = useState<string>(currentRepo?.active_revision_id || '');
  const [targetRev, setTargetRev] = useState<string>(currentRepo?.active_revision_id || '');
  const [diffData, setDiffData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!baseRev || !targetRev) {
      setError('Please select both base and target revisions.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.compareRevisions(baseRev, targetRev);
      setDiffData(data);
    } catch (err: any) {
      setError(err.message || 'Comparison failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">Repository Revision Comparison</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Static analysis differential engine across commits, branches, and code releases
          </p>
        </div>
      </div>

      {/* Revision Selectors */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Base Revision (Commit / Snapshot)</label>
            <input
              type="text"
              value={baseRev}
              onChange={(e) => setBaseRev(e.target.value)}
              placeholder="Revision ID or Commit Hash..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-mono text-xs focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Target Revision (Commit / Snapshot)</label>
            <input
              type="text"
              value={targetRev}
              onChange={(e) => setTargetRev(e.target.value)}
              placeholder="Revision ID or Commit Hash..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-mono text-xs focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2 border-t border-slate-800">
          <button
            onClick={handleCompare}
            disabled={isLoading || !baseRev || !targetRev}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white font-medium text-xs transition shadow-md shadow-cyan-600/20 disabled:opacity-40 flex items-center space-x-1.5"
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span>{isLoading ? 'Computing Diff...' : 'Compare Revisions'}</span>
          </button>
        </div>

        {error && (
          <div className="p-2.5 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Diff Results */}
      {diffData && (
        <div className="space-y-6 text-xs">
          {/* Changed Files */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
            <h3 className="font-bold text-slate-200 flex items-center space-x-2">
              <FileCode className="w-4 h-4 text-cyan-400" />
              <span>Changed Source Files ({diffData.changed_files.length})</span>
            </h3>

            {diffData.changed_files.length === 0 ? (
              <div className="text-slate-400 italic">No file differences detected between selected revisions.</div>
            ) : (
              <div className="divide-y divide-slate-800 font-mono">
                {diffData.changed_files.map((cf: any, idx: number) => (
                  <div key={idx} className="py-2 flex items-center justify-between">
                    <span className="text-slate-200 truncate">{cf.path}</span>
                    <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
                      cf.change_type === 'added' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' :
                      cf.change_type === 'deleted' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                      'bg-amber-950 text-amber-300 border border-amber-800'
                    }`}>
                      {cf.change_type}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Added & Removed Symbols */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 font-bold">
                <PlusCircle className="w-4 h-4" />
                <span>Added Symbols ({diffData.added_symbols.length})</span>
              </div>
              <div className="space-y-1 font-mono max-h-60 overflow-y-auto">
                {diffData.added_symbols.length === 0 ? (
                  <div className="text-slate-400 italic">None</div>
                ) : (
                  diffData.added_symbols.map((s: any, i: number) => (
                    <div key={i} className="p-1.5 rounded bg-slate-950 border border-slate-800 text-slate-300 truncate">
                      {s.qualified_name} ({s.kind})
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
              <div className="flex items-center space-x-2 text-rose-400 font-bold">
                <MinusCircle className="w-4 h-4" />
                <span>Removed Symbols ({diffData.removed_symbols.length})</span>
              </div>
              <div className="space-y-1 font-mono max-h-60 overflow-y-auto">
                {diffData.removed_symbols.length === 0 ? (
                  <div className="text-slate-400 italic">None</div>
                ) : (
                  diffData.removed_symbols.map((s: any, i: number) => (
                    <div key={i} className="p-1.5 rounded bg-slate-950 border border-slate-800 text-slate-300 truncate">
                      {s.qualified_name} ({s.kind})
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

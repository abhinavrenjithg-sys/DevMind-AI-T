import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import type { ChangeImpactResponse, SymbolItem, SourceFile } from '../types';
import { 
  Flame, 
  Layers, 
  TestTube, 
  AlertCircle, 
  ArrowRight,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';

export const ChangeImpactPage: React.FC = () => {
  const { currentRepo } = useWorkspace();
  const [searchParams] = useSearchParams();

  const [symbols, setSymbols] = useState<SymbolItem[]>([]);
  const [files, setFiles] = useState<SourceFile[]>([]);
  const [selectedSymbolId, setSelectedSymbolId] = useState<string>(searchParams.get('id') || '');
  const [selectedFilePath, setSelectedFilePath] = useState<string>('');
  const [depth, setDepth] = useState<number>(3);

  const [impactData, setImpactData] = useState<ChangeImpactResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load symbols and files on mount
  useEffect(() => {
    if (!currentRepo?.active_revision_id) return;
    api.getSymbols(currentRepo.active_revision_id).then(setSymbols).catch(console.error);
    api.getFiles(currentRepo.active_revision_id).then(setFiles).catch(console.error);
  }, [currentRepo]);

  // Auto trigger if param passed
  useEffect(() => {
    const id = searchParams.get('id');
    const name = searchParams.get('name');
    if ((id || name) && currentRepo?.active_revision_id) {
      handleAnalyze(id || undefined, name || undefined);
    }
  }, [searchParams, currentRepo]);

  const handleAnalyze = async (symId = selectedSymbolId, symName?: string) => {
    if (!currentRepo?.active_revision_id) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.analyzeImpact(
        currentRepo.active_revision_id,
        symId || undefined,
        symName || undefined,
        selectedFilePath || undefined,
        depth
      );
      setImpactData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to calculate change impact blast radius');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">Change Impact Analyzer</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Static blast-radius estimation, transitive dependency analysis, and affected test suite detection
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs text-amber-400 bg-amber-950/60 border border-amber-800/80 px-2.5 py-1 rounded-full">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Blast Radius Simulator Active</span>
        </div>
      </div>

      {/* Target Selector Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Target Symbol (Function / Class)</label>
            <select
              value={selectedSymbolId}
              onChange={(e) => {
                setSelectedSymbolId(e.target.value);
                setSelectedFilePath('');
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono text-xs cursor-pointer"
            >
              <option value="">-- Choose Symbol --</option>
              {symbols.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.qualified_name} ({s.kind})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Or Target File</label>
            <select
              value={selectedFilePath}
              onChange={(e) => {
                setSelectedFilePath(e.target.value);
                setSelectedSymbolId('');
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono text-xs cursor-pointer"
            >
              <option value="">-- Choose File --</option>
              {files.map((f) => (
                <option key={f.id} value={f.path}>
                  {f.path}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Blast Radius Depth</label>
            <div className="flex items-center space-x-2">
              <input
                type="range"
                min="1"
                max="5"
                value={depth}
                onChange={(e) => setDepth(Number(e.target.value))}
                className="flex-1 accent-cyan-400 cursor-pointer"
              />
              <span className="font-mono font-bold text-cyan-400 w-8 text-center">{depth} Hops</span>
              <button
                onClick={() => handleAnalyze()}
                disabled={isLoading || (!selectedSymbolId && !selectedFilePath)}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white font-medium transition shadow-md shadow-amber-600/20 disabled:opacity-40"
              >
                {isLoading ? 'Calculating...' : 'Analyze Impact'}
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-2.5 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Impact Results */}
      {impactData && (
        <div className="space-y-6">
          {/* Summary Box */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
            <div className="flex items-center space-x-2 text-amber-400">
              <Flame className="w-4 h-4" />
              <span className="font-bold text-xs uppercase tracking-wider">Impact Assessment Summary</span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-medium">
              {impactData.summary}
            </p>
          </div>

          {/* Three Column Breakdown: Direct | Transitive | Affected Tests */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Direct Dependents */}
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="font-bold text-xs text-cyan-300">
                  Direct Dependents ({impactData.direct_dependents.length})
                </span>
                <span className="text-[10px] uppercase font-semibold text-cyan-400 bg-cyan-950 px-1.5 py-0.2 rounded border border-cyan-800">
                  Depth 1
                </span>
              </div>

              {impactData.direct_dependents.length === 0 ? (
                <div className="text-slate-400 text-xs italic py-4 text-center">No direct dependents found</div>
              ) : (
                <div className="space-y-1.5 max-h-80 overflow-y-auto">
                  {impactData.direct_dependents.map((d, idx) => (
                    <div key={idx} className="p-2 rounded bg-slate-950 border border-slate-800 text-xs font-mono">
                      <div className="font-semibold text-slate-200 truncate">{d.name}</div>
                      <div className="text-[10px] text-slate-400 truncate mt-0.5">{d.file_path}</div>
                      <div className="text-[10px] text-cyan-400 mt-1">{d.reason}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Transitive Dependents */}
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="font-bold text-xs text-violet-300">
                  Transitive Dependents ({impactData.transitive_dependents.length})
                </span>
                <span className="text-[10px] uppercase font-semibold text-violet-400 bg-violet-950 px-1.5 py-0.2 rounded border border-violet-800">
                  Depth 2–{depth}
                </span>
              </div>

              {impactData.transitive_dependents.length === 0 ? (
                <div className="text-slate-400 text-xs italic py-4 text-center">No transitive dependents found</div>
              ) : (
                <div className="space-y-1.5 max-h-80 overflow-y-auto">
                  {impactData.transitive_dependents.map((t, idx) => (
                    <div key={idx} className="p-2 rounded bg-slate-950 border border-slate-800 text-xs font-mono">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200 truncate">{t.name}</span>
                        <span className="text-[9px] px-1 py-0.2 rounded bg-slate-800 text-slate-400">Hop {t.depth}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 truncate mt-0.5">{t.file_path}</div>
                      <div className="text-[10px] text-violet-400 mt-1">{t.reason}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Affected Test Suites */}
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="font-bold text-xs text-emerald-300 flex items-center space-x-1.5">
                  <TestTube className="w-3.5 h-3.5" />
                  <span>Affected Tests ({impactData.affected_tests.length})</span>
                </span>
                <span className="text-[10px] uppercase font-semibold text-emerald-400 bg-emerald-950 px-1.5 py-0.2 rounded border border-emerald-800">
                  Verification
                </span>
              </div>

              {impactData.affected_tests.length === 0 ? (
                <div className="text-slate-400 text-xs italic py-4 text-center">
                  No automated test files directly or transitively reference this component
                </div>
              ) : (
                <div className="space-y-1.5 max-h-80 overflow-y-auto">
                  {impactData.affected_tests.map((test, idx) => (
                    <div key={idx} className="p-2 rounded bg-slate-950 border border-emerald-900/40 text-xs font-mono">
                      <div className="font-semibold text-emerald-300 truncate">{test.test_file}</div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        Target Dependent: <strong className="text-slate-200">{test.target_dependent}</strong>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

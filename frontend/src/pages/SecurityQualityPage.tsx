import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import type { FindingItem } from '../types';
import { 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  Info, 
  Check, 
  X,
  FileCode,
  Filter
} from 'lucide-react';

export const SecurityQualityPage: React.FC = () => {
  const { currentRepo } = useWorkspace();
  const [findings, setFindings] = useState<FindingItem[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [toolFilter, setToolFilter] = useState<string>('all');
  const [includeDismissed, setIncludeDismissed] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState(false);

  // Dismiss dialog state
  const [dismissingId, setDismissingId] = useState<string | null>(null);
  const [dismissReason, setDismissReason] = useState<string>('False positive / reviewed');

  const loadFindings = async () => {
    if (!currentRepo?.active_revision_id) return;
    setIsLoading(true);
    try {
      const data = await api.getFindings(
        currentRepo.active_revision_id,
        severityFilter !== 'all' ? severityFilter : undefined,
        toolFilter !== 'all' ? toolFilter : undefined,
        includeDismissed
      );
      setFindings(data);
    } catch (err) {
      console.error('Failed to load findings:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadFindings();
  }, [currentRepo, severityFilter, toolFilter, includeDismissed]);

  const handleDismiss = async (finding: FindingItem, dismissState: boolean) => {
    try {
      await api.dismissFinding(finding.id, dismissState, dismissReason);
      setDismissingId(null);
      await loadFindings();
    } catch (err) {
      console.error('Failed to update finding status:', err);
    }
  };

  const getSeverityBadge = (severity: string) => {
    const sev = severity.toLowerCase();
    if (sev === 'critical') return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800 uppercase">Critical</span>;
    if (sev === 'high') return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-900/60 text-rose-300 border border-rose-700 uppercase">High</span>;
    if (sev === 'medium') return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-800 uppercase">Medium</span>;
    if (sev === 'low') return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950 text-cyan-300 border border-cyan-800 uppercase">Low</span>;
    return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700 uppercase">Info</span>;
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">Security & Code Quality Analysis</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Static AST rule evaluation, Ruff linter findings, Bandit security checks, and false-positive management
          </p>
        </div>

        <div className="text-[11px] text-slate-400 max-w-xs text-right hidden sm:block">
          All checks execute statically without executing codebase repository code.
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800">
            <span className="text-slate-400">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900">All Severities</option>
              <option value="critical" className="bg-slate-900">Critical</option>
              <option value="high" className="bg-slate-900">High</option>
              <option value="medium" className="bg-slate-900">Medium</option>
              <option value="low" className="bg-slate-900">Low</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5 bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800">
            <span className="text-slate-400">Tool:</span>
            <select
              value={toolFilter}
              onChange={(e) => setToolFilter(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900">All Tools</option>
              <option value="ruff" className="bg-slate-900">Ruff (Linter)</option>
              <option value="bandit" className="bg-slate-900">Bandit (Security AST)</option>
              <option value="devmind_sec" className="bg-slate-900">DevMind AST Rules</option>
            </select>
          </div>

          <label className="flex items-center space-x-1.5 text-slate-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={includeDismissed}
              onChange={(e) => setIncludeDismissed(e.target.checked)}
              className="accent-cyan-500 rounded cursor-pointer"
            />
            <span>Show Dismissed</span>
          </label>
        </div>

        <div className="text-slate-400 text-xs">
          <strong>{findings.length}</strong> findings listed
        </div>
      </div>

      {/* Findings Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        {isLoading ? (
          <div className="text-center py-16 text-slate-400 text-xs">Loading static analysis findings...</div>
        ) : findings.length === 0 ? (
          <div className="text-center py-16 text-slate-400 text-xs italic">
            No static analysis or security findings matching selected filters.
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {findings.map((item) => (
              <div
                key={item.id}
                className={`p-4 space-y-2 hover:bg-slate-800/40 transition text-xs ${
                  item.is_dismissed ? 'opacity-50 bg-slate-950/40' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getSeverityBadge(item.severity)}
                    <span className="font-mono text-xs font-bold text-slate-200">
                      {item.rule_id}
                    </span>
                    <span className="text-[10px] uppercase font-semibold text-slate-400 bg-slate-800 px-1.5 py-0.2 rounded">
                      {item.tool}
                    </span>
                    {item.is_dismissed && (
                      <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-800 px-1.5 py-0.2 rounded border border-slate-700">
                        Dismissed: {item.dismissed_reason || 'Reviewed'}
                      </span>
                    )}
                  </div>

                  {/* Actions */}
                  <div>
                    {item.is_dismissed ? (
                      <button
                        onClick={() => handleDismiss(item, false)}
                        className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition"
                      >
                        Restore Finding
                      </button>
                    ) : (
                      <button
                        onClick={() => setDismissingId(item.id)}
                        className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition"
                      >
                        Dismiss as False Positive
                      </button>
                    )}
                  </div>
                </div>

                <div className="text-slate-200 font-medium">
                  {item.message}
                </div>

                <div className="flex items-center space-x-2 text-[11px] text-slate-400 font-mono">
                  <FileCode className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{item.file_path}:{item.line_number}</span>
                </div>

                {item.code_snippet && (
                  <pre className="p-2 rounded bg-slate-950 border border-slate-800 text-slate-300 font-mono text-[11px] overflow-x-auto">
                    {item.code_snippet}
                  </pre>
                )}

                {/* Inline dismissal modal if active */}
                {dismissingId === item.id && (
                  <div className="p-3 rounded-lg bg-slate-950 border border-cyan-800/60 mt-2 space-y-2">
                    <span className="font-semibold text-slate-200 block text-xs">
                      False-Positive Dismissal Reason:
                    </span>
                    <input
                      type="text"
                      value={dismissReason}
                      onChange={(e) => setDismissReason(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                    />
                    <div className="flex justify-end space-x-2 pt-1">
                      <button
                        onClick={() => setDismissingId(null)}
                        className="px-2.5 py-1 rounded border border-slate-800 text-slate-400 hover:text-slate-200 text-xs"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleDismiss(item, true)}
                        className="px-3 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs transition"
                      >
                        Confirm Dismissal
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

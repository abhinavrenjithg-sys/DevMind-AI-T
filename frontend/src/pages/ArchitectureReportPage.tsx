import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import type { ArchitectureReportResponse } from '../types';
import { 
  FileText, 
  Download, 
  Copy, 
  Check, 
  RefreshCw,
  Layers,
  AlertTriangle,
  ShieldCheck
} from 'lucide-react';

export const ArchitectureReportPage: React.FC = () => {
  const { currentRepo } = useWorkspace();
  const [report, setReport] = useState<ArchitectureReportResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const loadReport = async () => {
    if (!currentRepo?.active_revision_id) return;
    setIsLoading(true);
    try {
      const data = await api.getArchitectureReport(currentRepo.active_revision_id);
      setReport(data);
    } catch (err) {
      console.error('Failed to load architecture report:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [currentRepo]);

  const handleCopy = () => {
    if (report?.markdown_report) {
      navigator.clipboard.writeText(report.markdown_report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!report?.markdown_report) return;
    const blob = new Blob([report.markdown_report], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${currentRepo?.name || 'architecture'}-report.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">Technical Architecture Report</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Executive architectural synthesis, layer topology, circular dependencies, and exportable documentation
          </p>
        </div>

        {report && (
          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied Markdown' : 'Copy Markdown'}</span>
            </button>

            <button
              onClick={handleDownload}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition shadow-md shadow-cyan-600/20"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export .md</span>
            </button>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="text-center py-20 text-xs text-slate-400 italic">
          Compiling technical architecture report...
        </div>
      ) : !report ? (
        <div className="text-center py-20 text-xs text-slate-400 italic">
          Run repository analysis to generate an architecture report.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Markdown Preview Document Container */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl font-sans text-xs text-slate-200 space-y-4">
            <pre className="font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap select-text bg-slate-950 p-6 rounded-lg border border-slate-800 overflow-x-auto">
              {report.markdown_report}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

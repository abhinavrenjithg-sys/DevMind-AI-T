import React, { useEffect, useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { api } from '../lib/api';
import type { AnalysisJob } from '../types';
import { MetricCard } from '../components/MetricCard';
import { 
  FileCode, 
  Layers, 
  GitFork, 
  ShieldAlert, 
  AlertTriangle, 
  Play, 
  ArrowRight,
  Bot,
  Search,
  Flame,
  CheckCircle2,
  Clock
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

export const DashboardPage: React.FC = () => {
  const { currentRepo, refreshRepositories } = useWorkspace();
  const navigate = useNavigate();
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);

  const fetchJobStatus = async () => {
    if (!currentRepo) return;
    try {
      const latest = await api.getLatestJob(currentRepo.id);
      setJob(latest);
      if (latest.status === 'completed' && !currentRepo.is_analyzed) {
        await refreshRepositories();
      }
    } catch {
      setJob(null);
    }
  };

  useEffect(() => {
    fetchJobStatus();
    // Poll job status if running or pending
    const interval = setInterval(() => {
      if (job?.status === 'running' || job?.status === 'pending') {
        fetchJobStatus();
      }
    }, 2500);
    return () => clearInterval(interval);
  }, [currentRepo, job?.status]);

  const handleStartAnalysis = async () => {
    if (!currentRepo) return;
    setIsTriggering(true);
    try {
      const newJob = await api.startAnalysis(currentRepo.id);
      setJob(newJob);
    } catch (err) {
      console.error('Failed to trigger analysis:', err);
    } finally {
      setIsTriggering(false);
    }
  };

  const stats = currentRepo?.summary_stats;

  // Prepare chart data for architectural layers
  const layerData = stats?.layers
    ? Object.entries(stats.layers).map(([name, count]) => ({ name, value: count }))
    : [];

  const COLORS = ['#06b6d4', '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ec4899'];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">Codebase Intelligence Overview</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time program analysis, architectural mapping, and static intelligence
          </p>
        </div>

        {currentRepo && (
          <div className="flex items-center space-x-3">
            <button
              onClick={handleStartAnalysis}
              disabled={isTriggering || job?.status === 'running'}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition shadow-md shadow-cyan-600/20 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{job?.status === 'running' ? 'Analyzing...' : 'Run Full Analysis'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Analysis Job Progress Banner */}
      {job && (job.status === 'running' || job.status === 'pending') && (
        <div className="p-4 rounded-xl bg-slate-900 border border-cyan-800/60 shadow-lg space-y-2.5">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
              <span className="font-semibold text-slate-200">
                Analysis in Progress: Stage '{job.current_stage}'
              </span>
            </div>
            <span className="font-mono text-cyan-400 font-bold">{job.progress_percentage}%</span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-cyan-500 to-violet-500 h-full transition-all duration-300"
              style={{ width: `${job.progress_percentage}%` }}
            />
          </div>

          {job.stage_logs && job.stage_logs.length > 0 && (
            <div className="text-[11px] text-slate-400 font-mono flex items-center space-x-1 truncate">
              <Clock className="w-3 h-3 text-cyan-400 shrink-0" />
              <span>{job.stage_logs[job.stage_logs.length - 1].message}</span>
            </div>
          )}
        </div>
      )}

      {/* Primary Repository Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          title="Files"
          value={stats?.total_files?.toLocaleString() || '0'}
          subtitle="Parsed source files"
          icon={FileCode}
          color="cyan"
        />
        <MetricCard
          title="Lines of Code"
          value={stats?.total_loc?.toLocaleString() || '0'}
          subtitle="Verified LOC"
          icon={Layers}
          color="violet"
        />
        <MetricCard
          title="Symbols"
          value={stats?.total_symbols?.toLocaleString() || '0'}
          subtitle="Funcs, classes, types"
          icon={Layers}
          color="emerald"
        />
        <MetricCard
          title="Dependencies"
          value={stats?.total_edges?.toLocaleString() || '0'}
          subtitle="Static relations"
          icon={GitFork}
          color="cyan"
        />
        <MetricCard
          title="Cycles"
          value={stats?.cycle_count || '0'}
          subtitle={stats?.cycle_count ? "Circular loops" : "No cycles"}
          icon={AlertTriangle}
          color={stats?.cycle_count ? "rose" : "emerald"}
        />
        <MetricCard
          title="Findings"
          value={stats?.total_findings || '0'}
          subtitle="Security & lint"
          icon={ShieldAlert}
          color={stats?.total_findings ? "amber" : "emerald"}
        />
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div
          onClick={() => navigate('/ai')}
          className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-violet-500/50 cursor-pointer group transition space-y-2"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-violet-500/20 text-violet-400">
              <Bot className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-violet-400 transition" />
          </div>
          <h3 className="font-semibold text-sm text-slate-200 group-hover:text-violet-300">AI Codebase Assistant</h3>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Ask questions grounded in source code evidence with exact line citations.
          </p>
        </div>

        <div
          onClick={() => navigate('/graph')}
          className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 cursor-pointer group transition space-y-2"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400">
              <GitFork className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-cyan-400 transition" />
          </div>
          <h3 className="font-semibold text-sm text-slate-200 group-hover:text-cyan-300">Dependency Graph</h3>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Explore interactive call and import graphs with cycle detection.
          </p>
        </div>

        <div
          onClick={() => navigate('/search')}
          className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-blue-500/50 cursor-pointer group transition space-y-2"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
              <Search className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-400 transition" />
          </div>
          <h3 className="font-semibold text-sm text-slate-200 group-hover:text-blue-300">Code Search</h3>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Lexical and full-text search across symbols, functions, and lines.
          </p>
        </div>

        <div
          onClick={() => navigate('/impact')}
          className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-amber-500/50 cursor-pointer group transition space-y-2"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
              <Flame className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-400 transition" />
          </div>
          <h3 className="font-semibold text-sm text-slate-200 group-hover:text-amber-300">Change Impact</h3>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Estimate blast radius and discover affected tests before refactoring.
          </p>
        </div>
      </div>

      {/* Two-Column Detail Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Architectural Layers Breakdown */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="font-semibold text-sm text-slate-200 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Architectural Layers Distribution</span>
          </h3>

          {layerData.length > 0 ? (
            <div className="h-60 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={layerData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, value }) => `${name} (${value})`}
                  >
                    {layerData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-center py-12 text-xs text-slate-400 italic">
              Run analysis to view architectural layer distribution
            </div>
          )}
        </div>

        {/* Frameworks, Languages & Entry Points */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="font-semibold text-sm text-slate-200">Discovered Technologies & Entry Points</h3>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-400 block mb-1.5 font-medium">Frameworks & Tools</span>
              <div className="flex flex-wrap gap-1.5">
                {stats?.frameworks && stats.frameworks.length > 0 ? (
                  stats.frameworks.map((fw) => (
                    <span key={fw} className="px-2.5 py-1 rounded bg-slate-800 text-cyan-300 font-medium border border-slate-700">
                      {fw}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-400 italic">No specific frameworks identified</span>
                )}
              </div>
            </div>

            <div>
              <span className="text-slate-400 block mb-1.5 font-medium">Languages</span>
              <div className="flex flex-wrap gap-1.5">
                {stats?.languages && Object.keys(stats.languages).length > 0 ? (
                  Object.entries(stats.languages).map(([lang, count]) => (
                    <span key={lang} className="px-2.5 py-1 rounded bg-slate-800 text-slate-200 border border-slate-700">
                      {lang}: <strong className="text-cyan-400">{count}</strong> files
                    </span>
                  ))
                ) : (
                  <span className="text-slate-400 italic">No files parsed yet</span>
                )}
              </div>
            </div>

            <div>
              <span className="text-slate-400 block mb-1.5 font-medium">Detected Entry Points</span>
              <div className="space-y-1 font-mono text-[11px]">
                {stats?.entry_points && stats.entry_points.length > 0 ? (
                  stats.entry_points.map((ep) => (
                    <div key={ep} className="p-1.5 rounded bg-slate-950 border border-slate-800 text-slate-300 flex items-center justify-between">
                      <span className="truncate">{ep}</span>
                      <span className="text-[10px] uppercase text-cyan-400 font-sans font-semibold">Entry</span>
                    </div>
                  ))
                ) : (
                  <div className="text-slate-400 italic font-sans text-xs">None identified</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

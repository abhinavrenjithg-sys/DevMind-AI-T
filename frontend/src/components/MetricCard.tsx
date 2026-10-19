import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  badge?: string;
  color?: 'cyan' | 'violet' | 'emerald' | 'amber' | 'rose';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  badge,
  color = 'cyan'
}) => {
  const colorMap = {
    cyan: 'from-cyan-500/10 to-transparent border-cyan-500/20 text-cyan-400',
    violet: 'from-violet-500/10 to-transparent border-violet-500/20 text-violet-400',
    emerald: 'from-emerald-500/10 to-transparent border-emerald-500/20 text-emerald-400',
    amber: 'from-amber-500/10 to-transparent border-amber-500/20 text-amber-400',
    rose: 'from-rose-500/10 to-transparent border-rose-500/20 text-rose-400',
  };

  return (
    <div className={`p-4 rounded-lg bg-slate-900 border ${colorMap[color].split(' ')[2]} bg-gradient-to-b ${colorMap[color].split(' ')[0]} ${colorMap[color].split(' ')[1]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400">{title}</span>
        <div className={`p-1.5 rounded-md bg-slate-800 ${colorMap[color].split(' ')[3]}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="mt-2 flex items-baseline justify-between">
        <div className="text-2xl font-bold text-slate-100 tracking-tight">{value}</div>
        {badge && (
          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            {badge}
          </span>
        )}
      </div>
      {subtitle && <p className="text-[11px] text-slate-400 mt-1">{subtitle}</p>}
    </div>
  );
};

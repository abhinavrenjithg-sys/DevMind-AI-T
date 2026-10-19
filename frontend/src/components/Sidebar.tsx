import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FolderGit2, 
  Network, 
  Search, 
  Bot, 
  GitFork, 
  GitCompare, 
  ShieldAlert, 
  FileText, 
  Settings,
  Flame
} from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';

export const Sidebar: React.FC = () => {
  const { currentRepo } = useWorkspace();

  const navItems = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/repositories', label: 'Repositories', icon: FolderGit2 },
    { to: '/architecture', label: 'Architecture Explorer', icon: Network },
    { to: '/search', label: 'Code Search', icon: Search },
    { to: '/ai', label: 'AI Assistant', icon: Bot, badge: 'AI' },
    { to: '/graph', label: 'Dependency Graph', icon: GitFork },
    { to: '/impact', label: 'Change Impact', icon: Flame },
    { to: '/security', label: 'Security & Quality', icon: ShieldAlert },
    { to: '/compare', label: 'Revision Compare', icon: GitCompare },
    { to: '/report', label: 'Architecture Report', icon: FileText },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-56 bg-slate-900 border-r border-slate-800 flex flex-col justify-between select-none shrink-0">
      <div className="py-3 px-2 space-y-1">
        <div className="px-3 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Workspace Navigation
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition ${
                  isActive
                    ? 'bg-slate-800 text-cyan-400 border-l-2 border-cyan-400'
                    : 'text-slate-300 hover:bg-slate-800/60 hover:text-slate-100'
                }`
              }
            >
              <div className="flex items-center space-x-2.5">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] px-1.5 py-0.2 rounded font-semibold bg-violet-950 text-violet-300 border border-violet-800">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Active Repo Footer Status */}
      <div className="p-3 border-t border-slate-800 text-xs">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
          Active Repository
        </div>
        {currentRepo ? (
          <div className="bg-slate-950 p-2 rounded border border-slate-800">
            <div className="font-medium text-slate-200 truncate">{currentRepo.name}</div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
              <span>{currentRepo.default_branch}</span>
              <span className={`px-1.5 py-0.2 rounded text-[10px] ${currentRepo.is_analyzed ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'}`}>
                {currentRepo.is_analyzed ? 'Analyzed' : 'Pending'}
              </span>
            </div>
          </div>
        ) : (
          <div className="text-slate-400 italic text-[11px]">No repository selected</div>
        )}
      </div>
    </aside>
  );
};

import React from 'react';
import {
  LayoutDashboard,
  Activity,
  Cpu,
  Wrench,
  ShieldCheck,
  Settings,
  Zap,
  Radio
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  isSimulating: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, setCurrentTab, isSimulating }) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'monitoring', label: 'Live Monitoring', icon: Activity },
    { id: 'ai', label: 'AI Health Intelligence', icon: Cpu },
    { id: 'service', label: 'Vehicle & Service History', icon: Wrench },
    { id: 'ota', label: 'OTA Validation Center', icon: ShieldCheck },
    { id: 'settings', label: 'Settings & Config', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                MotoMind
              </h1>
              <span className="text-[10px] font-semibold tracking-wider text-cyan-400 uppercase bg-cyan-950/60 border border-cyan-800/60 px-1.5 py-0.5 rounded">
                EV Intelligence
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status Badge */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <span className="flex items-center gap-1.5 font-medium">
            <Radio className={`w-3.5 h-3.5 ${isSimulating ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
            Simulator Engine
          </span>
          <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded ${
            isSimulating ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60' : 'bg-slate-800 text-slate-400'
          }`}>
            {isSimulating ? 'RUNNING' : 'PAUSED'}
          </span>
        </div>
        <div className="text-[11px] text-slate-500 leading-tight">
          Synthetic 2-Wheeler Physics v1.0 • Isolated Local Staging
        </div>
      </div>
    </aside>
  );
};

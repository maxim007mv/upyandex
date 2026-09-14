import React from 'react';
import {
  LayoutDashboard,
  Send,
  Users,
  FileText,
  ExternalLink,
  Mail,
  ShieldCheck,
} from 'lucide-react';
import clsx from 'clsx';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Панель управления', icon: LayoutDashboard },
    { id: 'mailings', label: 'Кампании и рассылки', icon: Send },
    { id: 'subscribers', label: 'База подписчиков', icon: Users },
    { id: 'templates', label: 'Шаблоны писем', icon: FileText },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 min-h-screen">
      {/* Brand header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800 space-x-3">
        <div className="bg-brand-600 p-2 rounded-lg text-white">
          <Mail className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-white tracking-wide leading-tight">
            Mailing System
          </h1>
          <p className="text-[10px] text-slate-400 font-mono">v1.0.0 Architecture</p>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 py-6 px-4 space-y-1">
        <div className="px-3 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Основное меню
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={clsx(
                'w-full flex items-center px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-brand-600 text-white shadow-sm shadow-brand-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              )}
            >
              <Icon className={clsx('w-4 h-4 mr-3', isActive ? 'text-white' : 'text-slate-400')} />
              {item.label}
            </button>
          );
        })}

        <div className="pt-8 px-3 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Инфраструктура и API
        </div>
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
        >
          <div className="flex items-center">
            <ShieldCheck className="w-4 h-4 mr-3 text-emerald-400" />
            <span>OpenAPI (Swagger)</span>
          </div>
          <ExternalLink className="w-3.5 h-3.5 opacity-60" />
        </a>

        <a
          href="http://localhost:8025"
          target="_blank"
          rel="noreferrer"
          className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
        >
          <div className="flex items-center">
            <Mail className="w-4 h-4 mr-3 text-amber-400" />
            <span>Mailpit Web UI</span>
          </div>
          <ExternalLink className="w-3.5 h-3.5 opacity-60" />
        </a>
      </div>

      {/* System info badge */}
      <div className="p-4 border-t border-slate-800 text-xs text-slate-400">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-mono text-[11px] text-slate-300">Workers: Active</span>
        </div>
        <p className="mt-1 text-[11px] text-slate-400">Celery + Redis + FastAPI</p>
      </div>
    </aside>
  );
};

import React from 'react';
import { LogOut, User as UserIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  title: string;
}

export const Navbar: React.FC<NavbarProps> = ({ title }) => {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0">
      <div className="flex items-center space-x-3">
        <h2 className="text-lg font-bold text-slate-800">{title}</h2>
      </div>

      <div className="flex items-center space-x-4">
        {user && (
          <div className="flex items-center space-x-3 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl">
            <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-xs">
              {user.full_name ? user.full_name.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
            </div>
            <div className="text-left text-xs">
              <p className="font-semibold text-slate-900 leading-tight">
                {user.full_name || user.email}
              </p>
              <div className="flex items-center space-x-1.5">
                <span className="text-[10px] uppercase font-bold text-brand-600 tracking-wider">
                  {user.role}
                </span>
                <span className="text-slate-300">•</span>
                <span className="text-[11px] text-slate-500 font-mono">{user.email}</span>
              </div>
            </div>
          </div>
        )}

        <button
          onClick={logout}
          title="Выйти из системы"
          className="flex items-center text-xs font-medium text-slate-600 hover:text-rose-600 p-2 rounded-lg hover:bg-rose-50 border border-transparent hover:border-rose-100 transition-colors"
        >
          <LogOut className="w-4 h-4 mr-1.5" />
          <span>Выйти</span>
        </button>
      </div>
    </header>
  );
};

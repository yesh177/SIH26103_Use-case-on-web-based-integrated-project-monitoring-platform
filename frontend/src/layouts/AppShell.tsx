import React, { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Trophy,
  FileSpreadsheet,
  Network,
  ClipboardCheck,
  Menu,
  X,
  ShieldCheck,
  User,
  LogOut,
} from 'lucide-react';
import { cn } from '../lib/utils';

export const AppShell: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  // Extract canonicalProjectKey from current URL or default to sample Rank #1 key
  const matchKey = location.pathname.match(/\/projects\/([^/]+)/);
  const currentKey = matchKey ? matchKey[1] : 'PROJ-PAIMANA-400119';

  const navItems = [
    {
      name: 'Portfolio Overview',
      path: '/dashboard',
      icon: <LayoutDashboard className="w-4 h-4" />,
      description: 'Macro portfolio KPIs & distributions',
    },
    {
      name: 'Risk Ranking',
      path: '/risk-ranking',
      icon: <Trophy className="w-4 h-4" />,
      description: 'Min-rank multi-hazard leaderboard',
    },
    {
      name: 'Project Detail',
      path: `/projects/${currentKey}`,
      icon: <FileSpreadsheet className="w-4 h-4" />,
      description: 'Multi-hazard project profile',
      exact: true,
    },
    {
      name: 'Risk Drivers',
      path: `/projects/${currentKey}/drivers`,
      icon: <Network className="w-4 h-4" />,
      description: 'Top 3 explainability drivers',
    },
    {
      name: 'Interventions',
      path: `/projects/${currentKey}/interventions`,
      icon: <ClipboardCheck className="w-4 h-4" />,
      description: '7-action supervisory protocols',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Government Official Strip */}
      <div className="bg-slate-900 text-slate-300 text-[11px] px-4 py-1.5 flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-medium text-slate-200">
            Government of India · Ministry of Statistics and Programme Implementation (MoSPI)
          </span>
          <span className="hidden md:inline text-slate-500">|</span>
          <span className="hidden md:inline text-slate-400">
            Problem Statement SIH26103 · Central Infrastructure Monitoring
          </span>
        </div>
        <div className="flex items-center gap-4 text-slate-400">
          <span className="hidden sm:inline bg-slate-800 px-2 py-0.5 rounded text-[10px] text-blue-300 font-mono">
            COHORT: JULY 2025 — JULY 2026 (N=437)
          </span>
          <NavLink to="/login" className="hover:text-white flex items-center gap-1">
            <LogOut className="w-3 h-3" />
            <span className="hidden sm:inline">Sign Out</span>
          </NavLink>
        </div>
      </div>

      {/* Main Header / Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Mobile menu toggle button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 text-slate-600 hover:text-slate-900 rounded-md hover:bg-slate-100"
              aria-label="Toggle Navigation"
            >
              {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>

            {/* PAIMANA Brand */}
            <NavLink to="/dashboard" className="flex items-center gap-2.5">
              <div className="w-9 h-9 bg-blue-700 text-white rounded-lg flex items-center justify-center font-bold tracking-wider shadow-sm">
                P
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-extrabold text-base tracking-tight text-slate-900">
                    PAIMANA
                  </span>
                  <span className="text-[10px] font-bold bg-blue-100 text-blue-800 px-1.5 py-0.2 rounded uppercase tracking-wide">
                    Risk Intel
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 font-medium tracking-tight -mt-0.5">
                  Predictive Infrastructure Surveillance Platform
                </p>
              </div>
            </NavLink>
          </div>

          {/* Desktop Primary Nav */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = item.exact
                ? location.pathname === item.path
                : location.pathname.startsWith(item.path);

              return (
                <NavLink
                  key={item.name}
                  to={item.path}
                  className={cn(
                    'px-3 py-2 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-colors',
                    isActive
                      ? 'bg-blue-50 text-blue-700 border border-blue-200/80 shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  )}
                >
                  {item.icon}
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* User / Persona Indicator */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-semibold text-slate-800">Surveillance Officer</span>
              <span className="text-[10px] text-slate-500">Central Oversight Division</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-slate-200 border border-slate-300 flex items-center justify-center text-slate-600 font-semibold text-xs">
              <User className="w-4 h-4 text-slate-600" />
            </div>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {isMobileMenuOpen && (
          <div className="lg:hidden bg-white border-b border-slate-200 px-4 pt-2 pb-4 space-y-1 shadow-md">
            {navItems.map((item) => (
              <NavLink
                key={item.name}
                to={item.path}
                onClick={() => setIsMobileMenuOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'px-3 py-2.5 rounded-md text-sm font-medium flex items-center gap-2.5 transition-colors',
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-semibold'
                      : 'text-slate-700 hover:bg-slate-100'
                  )
                }
              >
                {item.icon}
                <div>
                  <div>{item.name}</div>
                  <div className="text-[11px] text-slate-400 font-normal">{item.description}</div>
                </div>
              </NavLink>
            ))}
          </div>
        )}
      </header>

      {/* Main Page Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>

      {/* Enterprise / MoSPI Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-slate-500 text-xs mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-700 shrink-0" />
            <span className="font-medium text-slate-700">
              PAIMANA Predictive Risk Intelligence Platform
            </span>
            <span className="hidden md:inline">·</span>
            <span className="hidden md:inline text-[11px]">
              Point-in-Time Holdout Benchmark (July 2025 Cutoff)
            </span>
          </div>
          <div className="text-[11px] text-slate-400 flex items-center gap-3">
            <span>Built for SIH 2026 · Problem Statement SIH26103</span>
            <span className="inline-block w-1 h-1 rounded-full bg-slate-300" />
            <span className="text-slate-500 font-medium">Non-Punitive Supervisory Support</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

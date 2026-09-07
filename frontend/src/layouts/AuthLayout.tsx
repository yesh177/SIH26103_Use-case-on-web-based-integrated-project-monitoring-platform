import React from 'react';
import { Outlet } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-between py-8 px-4 sm:px-6 lg:px-8">
      {/* Top Banner */}
      <div className="max-w-md w-full mx-auto text-center space-y-2">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-blue-700 text-white font-extrabold text-xl shadow-md ring-4 ring-blue-500/20">
          P
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">PAIMANA</h1>
        <p className="text-xs text-blue-200 tracking-wide font-medium uppercase">
          Predictive Risk Intelligence · MoSPI Central Surveillance
        </p>
        <p className="text-xs text-slate-400 max-w-xs mx-auto">
          Web-Based Integrated Project Monitoring Platform (SIH26103)
        </p>
      </div>

      {/* Auth Card Container */}
      <div className="max-w-md w-full mx-auto my-6">
        <div className="bg-white text-slate-900 rounded-xl shadow-xl border border-slate-200 p-6 sm:p-8">
          <Outlet />
        </div>
      </div>

      {/* Security & Official Use Footer */}
      <div className="max-w-md w-full mx-auto text-center space-y-2 text-[11px] text-slate-500">
        <div className="flex items-center justify-center gap-1.5 text-slate-400">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
          <span>Official MoSPI Infrastructure Surveillance Portal</span>
        </div>
        <p>
          Authorized central ministry, line department, and CPSE project monitoring officials only.
        </p>
      </div>
    </div>
  );
};

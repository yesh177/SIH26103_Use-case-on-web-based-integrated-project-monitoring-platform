import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { FileQuestion, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-6 space-y-4">
      <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 border border-slate-200">
        <FileQuestion className="w-8 h-8" />
      </div>
      <div className="space-y-1 max-w-md">
        <h2 className="text-2xl font-bold text-slate-900">404 — Screen Not Found</h2>
        <p className="text-xs text-slate-500 leading-relaxed">
          The requested surveillance view or project route does not exist in the PAIMANA platform.
        </p>
      </div>
      <Link to="/dashboard">
        <Button variant="primary" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
          Return to Portfolio Overview
        </Button>
      </Link>
    </div>
  );
};

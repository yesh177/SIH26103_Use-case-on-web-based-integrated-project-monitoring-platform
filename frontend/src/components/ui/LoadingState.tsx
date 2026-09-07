import React from 'react';
import { cn } from '../../lib/utils';
import { Loader2 } from 'lucide-react';

export interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading surveillance intelligence...',
  className,
}) => {
  return (
    <div
      className={cn(
        'p-12 flex flex-col items-center justify-center text-center space-y-3 bg-white rounded-lg border border-slate-200 shadow-sm',
        className
      )}
    >
      <Loader2 className="w-7 h-7 text-blue-700 animate-spin" />
      <div className="space-y-1">
        <p className="text-sm font-medium text-slate-800">{message}</p>
        <p className="text-xs text-slate-400">Querying verified point-in-time benchmark records</p>
      </div>
    </div>
  );
};

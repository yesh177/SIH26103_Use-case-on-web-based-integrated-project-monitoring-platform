import React from 'react';
import { cn } from '../../lib/utils';
import { FolderSearch } from 'lucide-react';

export interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Records Found',
  description = 'No project records match the selected filter criteria or query.',
  action,
  icon,
  className,
}) => {
  return (
    <div
      className={cn(
        'p-12 flex flex-col items-center justify-center text-center space-y-3 bg-white rounded-lg border border-slate-200 shadow-sm',
        className
      )}
    >
      <div className="p-3 bg-slate-50 text-slate-400 rounded-full border border-slate-200">
        {icon || <FolderSearch className="w-6 h-6" />}
      </div>
      <div className="space-y-1 max-w-sm">
        <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
        <p className="text-xs text-slate-500 leading-relaxed">{description}</p>
      </div>
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
};

import React from 'react';
import { cn } from '../../lib/utils';
import { ShieldAlert, Info, AlertTriangle } from 'lucide-react';

export interface AdvisoryBannerProps {
  type?: 'governance' | 'non-causal' | 'partial-coverage' | 'custom';
  title?: string;
  message?: string;
  className?: string;
}

export const AdvisoryBanner: React.FC<AdvisoryBannerProps> = ({
  type = 'governance',
  title,
  message,
  className,
}) => {
  const configs = {
    governance: {
      defaultTitle: 'Official MoSPI Surveillance Advisory',
      defaultMessage:
        'Advisory decision support for supervisory review. Automated administrative sanctions, budget penalties, or contract cancellations are strictly prohibited.',
      icon: <ShieldAlert className="w-4 h-4 text-blue-700 shrink-0 mt-0.5" />,
      classes: 'bg-blue-50/70 border-blue-200 text-blue-900',
    },
    'non-causal': {
      defaultTitle: 'Statistical Association Notice',
      defaultMessage:
        'Feature attributions reflect statistical associations observed in retrospective MoSPI holdout cohorts; they do not establish causal fault, administrative negligence, or contractor liability.',
      icon: <Info className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />,
      classes: 'bg-slate-100 border-slate-200 text-slate-800',
    },
    'partial-coverage': {
      defaultTitle: 'Schedule Baseline Unobserved',
      defaultMessage:
        'Schedule Outcome Unavailable: Baseline milestone completion dates unobserved in canonical MoSPI reporting. Cost risk serves as sole attention score.',
      icon: <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />,
      classes: 'bg-amber-50 border-amber-200 text-amber-900',
    },
    custom: {
      defaultTitle: title || 'Notice',
      defaultMessage: message || '',
      icon: <Info className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />,
      classes: 'bg-slate-50 border-slate-200 text-slate-800',
    },
  };

  const current = configs[type];

  return (
    <div
      className={cn(
        'p-3.5 rounded-lg border flex items-start gap-3 text-xs leading-relaxed select-none',
        current.classes,
        className
      )}
    >
      {current.icon}
      <div>
        <span className="font-semibold block mb-0.5">{title || current.defaultTitle}</span>
        <p className="opacity-90">{message || current.defaultMessage}</p>
      </div>
    </div>
  );
};

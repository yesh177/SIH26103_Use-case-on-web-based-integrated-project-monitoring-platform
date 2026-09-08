import React from 'react';
import { cn, formatProbability } from '../../lib/utils';
import { HelpCircle } from 'lucide-react';

export interface RiskIndicatorProps {
  label: string;
  value: number | null | undefined;
  type?: 'cost' | 'schedule' | 'compound' | 'attention';
  subtext?: string;
  className?: string;
}

/**
 * Visual Risk Meter / Value Display
 * Strictly preserves NULL semantics for unobserved schedule outcomes.
 */
export const RiskIndicator: React.FC<RiskIndicatorProps> = ({
  label,
  value,
  type = 'cost',
  subtext,
  className,
}) => {
  const isUnobserved = value === null || value === undefined || isNaN(value);
  const formattedPct = formatProbability(value, 'Unobserved');

  // Determine indicator color intensity
  const getColorClass = () => {
    if (isUnobserved) return 'text-amber-700 bg-amber-50 border-amber-200';
    if (value >= 0.9) return 'text-red-700 bg-red-50 border-red-200';
    if (value >= 0.75) return 'text-amber-800 bg-amber-50 border-amber-200';
    if (value >= 0.5) return 'text-yellow-800 bg-yellow-50 border-yellow-200';
    return 'text-slate-700 bg-slate-50 border-slate-200';
  };

  const getProgressColor = () => {
    if (isUnobserved) return 'bg-amber-400';
    if (value >= 0.9) return 'bg-red-600';
    if (value >= 0.75) return 'bg-amber-500';
    if (value >= 0.5) return 'bg-yellow-500';
    return 'bg-slate-400';
  };

  return (
    <div
      className={cn(
        'p-5 rounded-xl border border-slate-200/80 bg-white shadow-[0_4px_16px_rgba(15,23,42,0.05)] flex flex-col justify-between transition-shadow hover:shadow-[0_8px_24px_rgba(15,23,42,0.08)]',
        className
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
          {label}
        </span>
        {type === 'compound' && (
          <span
            className="text-slate-400 hover:text-slate-600 cursor-help"
            title="min(Pc, Ps) dual-hazard sentinel; strictly NOT a joint mathematical probability"
          >
            <HelpCircle className="w-3.5 h-3.5" />
          </span>
        )}
      </div>

      <div className="my-2.5 flex items-baseline justify-between">
        <span
          className={cn(
            'text-2xl font-bold tracking-tight',
            isUnobserved ? 'text-amber-700 text-lg italic' : 'text-slate-900'
          )}
        >
          {formattedPct}
        </span>
        {!isUnobserved && (
          <span className={cn('text-xs px-2 py-0.5 rounded font-semibold border', getColorClass())}>
            Model Probability
          </span>
        )}
      </div>

      {/* Progress Bar (if observed) or Warning Note (if unobserved) */}
      {!isUnobserved ? (
        <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
          <div
            className={cn('h-1.5 rounded-full transition-all duration-300', getProgressColor())}
            style={{ width: `${Math.min(100, Math.max(0, (value || 0) * 100))}%` }}
          />
        </div>
      ) : (
        <p className="text-[11px] text-amber-700 italic leading-tight">
          Milestone dates unrecorded in source reporting.
        </p>
      )}

      {subtext && <p className="text-[11px] text-slate-500 mt-2">{subtext}</p>}
    </div>
  );
};



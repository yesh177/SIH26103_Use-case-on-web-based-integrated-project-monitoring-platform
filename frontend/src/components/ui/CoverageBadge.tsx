import React from 'react';
import { cn } from '../../lib/utils';
import { RiskCoverage } from '../../types/models';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';

export interface CoverageBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  coverage: RiskCoverage;
  showIcon?: boolean;
  size?: 'sm' | 'md';
}

/**
 * PAIMANA Coverage Status Badge
 * INVARIANT: If PARTIAL, indicates baseline milestone dates were unobserved in source reporting.
 * Missing schedule data must never be hidden or shown as 0% risk.
 */
export const CoverageBadge: React.FC<CoverageBadgeProps> = ({
  coverage,
  showIcon = true,
  size = 'sm',
  className,
  ...props
}) => {
  const isFull = coverage === 'FULL';
  const sizeClasses = size === 'md' ? 'text-xs px-2.5 py-1' : 'text-[11px] px-2 py-0.5';

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-semibold rounded-md border tracking-wide select-none',
        isFull
          ? 'bg-blue-50 text-blue-700 border-blue-200'
          : 'bg-amber-50 text-amber-800 border-amber-200',
        sizeClasses,
        className
      )}
      title={
        isFull
          ? 'Full Coverage: Both cost and schedule baseline milestones observed'
          : 'Partial Coverage: Milestone dates unobserved in source reporting; schedule outcome unobserved'
      }
      {...props}
    >
      {showIcon &&
        (isFull ? (
          <CheckCircle2 className="w-3 h-3 text-blue-600 shrink-0" />
        ) : (
          <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
        ))}
      <span>{isFull ? 'FULL COVERAGE' : 'PARTIAL COVERAGE'}</span>
    </span>
  );
};

CoverageBadge.displayName = 'CoverageBadge';

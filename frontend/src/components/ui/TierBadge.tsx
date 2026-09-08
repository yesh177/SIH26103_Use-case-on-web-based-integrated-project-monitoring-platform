import React from 'react';
import { cn } from '../../lib/utils';
import { AttentionTier } from '../../types/models';

export interface TierBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tier: AttentionTier;
  showDetail?: boolean;
  size?: 'sm' | 'md';
}

/**
 * PAIMANA Attention Tier Badge
 * INVARIANT: Tiers represent relative empirical quantile prioritization (Tier 1..Tier 4).
 * NEVER label as "Critical/High/Medium/Low Risk".
 */
export const TierBadge: React.FC<TierBadgeProps> = ({
  tier,
  showDetail = false,
  size = 'sm',
  className,
  ...props
}) => {
  const tierConfig: Record<
    AttentionTier,
    { label: string; detail: string; classes: string; dotColor: string }
  > = {
    'Tier 1': {
      label: 'Tier 1',
      detail: 'Highest Quantile Tier',
      classes: 'bg-red-50 text-red-700 border-red-200 ring-red-500/10',
      dotColor: 'bg-red-600',
    },
    'Tier 2': {
      label: 'Tier 2',
      detail: '75thâ€“90th %ile',
      classes: 'bg-amber-50 text-amber-800 border-amber-200 ring-amber-500/10',
      dotColor: 'bg-amber-600',
    },
    'Tier 3': {
      label: 'Tier 3',
      detail: '50thâ€“75th %ile',
      classes: 'bg-yellow-50 text-yellow-800 border-yellow-200 ring-yellow-500/10',
      dotColor: 'bg-yellow-600',
    },
    'Tier 4': {
      label: 'Tier 4',
      detail: 'Lower Quantile Tier',
      classes: 'bg-slate-100 text-slate-700 border-slate-200 ring-slate-500/10',
      dotColor: 'bg-slate-500',
    },
  };

  const config = tierConfig[tier] || tierConfig['Tier 4'];
  const sizeClasses = size === 'md' ? 'text-xs px-2.5 py-1' : 'text-[11px] px-2 py-0.5';

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-semibold rounded-md border tracking-wide select-none',
        config.classes,
        sizeClasses,
        className
      )}
      title={`${config.label}: ${config.detail}`}
      {...props}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', config.dotColor)} />
      <span>{config.label}</span>
      {showDetail && <span className="font-normal opacity-75">({config.detail})</span>}
    </span>
  );
};

TierBadge.displayName = 'TierBadge';


import React from 'react';
import { cn } from '../../lib/utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'neutral' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'sm', ...props }, ref) => {
    const variants = {
      default: 'bg-blue-50 text-blue-700 border-blue-200',
      neutral: 'bg-slate-100 text-slate-700 border-slate-200',
      success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      warning: 'bg-amber-50 text-amber-800 border-amber-200',
      danger: 'bg-red-50 text-red-700 border-red-200',
      info: 'bg-sky-50 text-sky-700 border-sky-200',
    };

    const sizes = {
      sm: 'text-[11px] px-2 py-0.5 font-medium',
      md: 'text-xs px-2.5 py-1 font-semibold',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-md border tracking-wide select-none',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);

Badge.displayName = 'Badge';

import React, { useState } from 'react';
import { useParams, NavLink, useNavigate } from 'react-router-dom';
import { PageHeader } from '../../components/common/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { AdvisoryBanner } from '../../components/ui/AdvisoryBanner';
import { Button } from '../../components/ui/Button';
import { useProjectDrivers, useProjectDetail } from '../../hooks/useProjects';
import { cn, formatProbability } from '../../lib/utils';
import {
  FileSpreadsheet,
  Network,
  ClipboardCheck,
  TrendingUp,
  TrendingDown,
  ArrowRight,
} from 'lucide-react';

export const ProjectDriversPage: React.FC = () => {
  const { canonicalProjectKey } = useParams<{ canonicalProjectKey: string }>();
  const navigate = useNavigate();
  const projectKey = canonicalProjectKey || 'PROJ-PAIMANA-400119';

  const [activeTask, setActiveTask] = useState<'cost' | 'schedule'>('cost');

  const { data: detail } = useProjectDetail(projectKey);
  const { data: driversData } = useProjectDrivers(projectKey);

  const activeDrivers =
    activeTask === 'cost' ? driversData?.cost_drivers : driversData?.schedule_drivers;

  const isScheduleEligible = driversData?.schedule_drivers.is_eligible === 1;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <PageHeader
        title="Explainable Risk Drivers"
        subtitle={`Marginal reference perturbation attributions (Delta) grounded in verifiable MoSPI snapshot facts for ${projectKey}.`}
        breadcrumbs={[
          { label: 'Home', href: '/dashboard' },
          { label: 'Risk Ranking', href: '/risk-ranking' },
          { label: detail?.project.project_name || projectKey, href: `/projects/${projectKey}` },
          { label: 'Risk Drivers' },
        ]}
        badge={
          <span className="text-xs font-semibold bg-blue-50 text-blue-800 border border-blue-200 px-2 py-0.5 rounded font-mono">
            Local Sensitivity Delta
          </span>
        }
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate(`/projects/${projectKey}/interventions`)}
            rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
          >
            Intervention Directives
          </Button>
        }
      />

      {/* Screen 3 / 4 / 5 Navigation Sub-Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200 bg-white/70 rounded-t-xl px-2 pt-1 shadow-sm">
        <NavLink
          to={`/projects/${projectKey}`}
          end
          className={({ isActive }) =>
            cn(
              'px-4 py-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition-all -mb-px rounded-t-lg',
              isActive
                ? 'border-blue-700 text-blue-700'
                : 'border-transparent text-slate-500 hover:text-slate-900 hover:border-slate-300'
            )
          }
        >
          <FileSpreadsheet className="w-4 h-4" />
          <span>Multi-Hazard Risk Profile</span>
        </NavLink>

        <NavLink
          to={`/projects/${projectKey}/drivers`}
          className={({ isActive }) =>
            cn(
              'px-4 py-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition-all -mb-px rounded-t-lg',
              isActive
                ? 'border-blue-700 text-blue-700'
                : 'border-transparent text-slate-500 hover:text-slate-900 hover:border-slate-300'
            )
          }
        >
          <Network className="w-4 h-4" />
          <span>Explainable Risk Drivers (Top 3)</span>
        </NavLink>

        <NavLink
          to={`/projects/${projectKey}/interventions`}
          className={({ isActive }) =>
            cn(
              'px-4 py-3 text-xs font-semibold border-b-2 flex items-center gap-2 transition-all -mb-px rounded-t-lg',
              isActive
                ? 'border-blue-700 text-blue-700'
                : 'border-transparent text-slate-500 hover:text-slate-900 hover:border-slate-300'
            )
          }
        >
          <ClipboardCheck className="w-4 h-4" />
          <span>Intervention Protocol Panel</span>
        </NavLink>
      </div>

      {/* Task Toggle: Cost Overrun Drivers vs Schedule Slippage Drivers */}
      <div className="flex items-center gap-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Evaluation Task:
        </span>
        <div className="inline-flex rounded-lg bg-slate-100/80 p-1 border border-slate-200 shadow-sm text-xs">
          <button
            onClick={() => setActiveTask('cost')}
            className={cn(
              'px-4 py-1.5 rounded-md font-semibold transition-all',
              activeTask === 'cost'
                ? 'bg-white text-blue-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            )}
          >
            Cost Overrun Drivers (&gt;5%)
          </button>
          <button
            onClick={() => setActiveTask('schedule')}
            className={cn(
              'px-4 py-1.5 rounded-md font-semibold transition-all',
              activeTask === 'schedule'
                ? 'bg-white text-blue-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            )}
          >
            Schedule Slippage Drivers (&gt;=3M)
          </button>
        </div>
      </div>

      {/* Check if Schedule task is unobserved for partial projects */}
      {activeTask === 'schedule' && !isScheduleEligible ? (
        <AdvisoryBanner
          type="partial-coverage"
          title="Schedule Explainability Unavailable"
          message="Because baseline milestone completion dates were unrecorded in canonical MoSPI tables, prospective schedule slippage is unobserved for this project. Local feature attribution is restricted to the cost overrun hazard."
        />
      ) : (
        /* Top 3 Explainability Driver Cards */
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>
              Top 3 statistical feature drivers computed via Marginal Reference Perturbation (Delta)
            </span>
            <span className="font-mono text-[11px]">
              Task Probability: {formatProbability(activeDrivers?.predicted_risk_probability)}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {activeDrivers?.top_drivers.map((driver) => {
              const isIncreasing = driver.direction === 'INCREASES_RISK';

              return (
                <Card key={driver.rank} className="flex flex-col justify-between">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-100 text-slate-800 font-bold text-xs">
                        #{driver.rank}
                      </span>
                      <Badge
                        variant={isIncreasing ? 'danger' : 'success'}
                        className="font-semibold text-[10px]"
                      >
                        {isIncreasing ? (
                          <span className="flex items-center gap-1">
                            <TrendingUp className="w-3 h-3" /> INCREASES RISK
                          </span>
                        ) : (
                          <span className="flex items-center gap-1">
                            <TrendingDown className="w-3 h-3" /> DECREASES RISK
                          </span>
                        )}
                      </Badge>
                    </div>
                    <CardTitle className="text-sm mt-2 font-mono">
                      {driver.feature.replace('feat_', '')}
                    </CardTitle>
                    <CardDescription>
                      Perturbation Impact Magnitude: Delta = +{(driver.impact * 100).toFixed(2)}%
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-3 pt-0">
                    {/* Visual Impact Bar */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-[11px] text-slate-500 font-medium">
                        <span>Relative Impact</span>
                        <span>+{(driver.impact * 100).toFixed(2)}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div
                          className={cn('h-2 rounded-full', isIncreasing ? 'bg-red-500' : 'bg-emerald-500')}
                          style={{ width: `${Math.min(100, Math.max(10, driver.impact * 300))}%` }}
                        />
                      </div>
                    </div>

                    {/* Observed Source Fact Box */}
                    <div className="p-3 bg-slate-50 rounded-md border border-slate-200 text-xs text-slate-700 leading-relaxed">
                      <span className="font-semibold text-[10px] uppercase text-slate-500 block mb-1">
                        Observed MoSPI Source Fact:
                      </span>
                      <p className="italic">{driver.source_fact}</p>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Mandatory Non-Causal Advisory Footer */}
      <AdvisoryBanner
        type="non-causal"
        message="Feature attributions reflect statistical associations observed in retrospective MoSPI holdout cohorts; they do not establish causal fault or contractor liability."
      />
    </div>
  );
};






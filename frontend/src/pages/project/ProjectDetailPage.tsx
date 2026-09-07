import React from 'react';
import { useParams, NavLink, useNavigate } from 'react-router-dom';
import { PageHeader } from '../../components/common/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { TierBadge } from '../../components/ui/TierBadge';
import { CoverageBadge } from '../../components/ui/CoverageBadge';
import { RiskIndicator } from '../../components/ui/RiskIndicator';
import { AdvisoryBanner } from '../../components/ui/AdvisoryBanner';
import { Button } from '../../components/ui/Button';
import { useProjectDetail } from '../../hooks/useProjects';
import { formatCrores, cn } from '../../lib/utils';
import {
  FileSpreadsheet,
  Network,
  ClipboardCheck,
  Building,
  MapPin,
  Calendar,
  IndianRupee,
  Activity,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';

export const ProjectDetailPage: React.FC = () => {
  const { canonicalProjectKey } = useParams<{ canonicalProjectKey: string }>();
  const navigate = useNavigate();
  const projectKey = canonicalProjectKey || 'PROJ-PAIMANA-400119';

  const { data: detail } = useProjectDetail(projectKey);

  const isPartial = detail?.risk.risk_coverage === 'PARTIAL';

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <PageHeader
        title={detail?.project.project_name || 'Loading Project Profile...'}
        subtitle={`Canonical Project Key: ${projectKey} · MoSPI Source ID: ${detail?.project.source_project_id || '—'}`}
        breadcrumbs={[
          { label: 'Home', href: '/dashboard' },
          { label: 'Risk Ranking', href: '/risk-ranking' },
          { label: detail?.project.project_name || projectKey },
        ]}
        badge={
          detail && (
            <div className="flex items-center gap-2">
              <TierBadge tier={detail.risk.attention_tier} showDetail size="md" />
              <CoverageBadge coverage={detail.risk.risk_coverage} size="md" />
            </div>
          )
        }
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/projects/${projectKey}/drivers`)}
              rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              Inspect Risk Drivers
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate(`/projects/${projectKey}/interventions`)}
              rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              Action Panel
            </Button>
          </div>
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

      {/* Multi-Hazard Risk Summary Cards (Screen 3 Core) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Cost Overrun Risk Card */}
        <RiskIndicator
          label="Cost Overrun Risk (>5%)"
          value={detail?.risk.cost_risk_probability}
          type="cost"
          subtext="Model: RandomForestClassifier (raw_uncalibrated)"
        />

        {/* Schedule Slippage Risk Card */}
        <RiskIndicator
          label="Schedule Slippage Risk (>=3M)"
          value={detail?.risk.schedule_risk_probability}
          type="schedule"
          subtext={
            isPartial
              ? 'Schedule outcome unobserved in source reporting'
              : 'Model: RandomForestClassifier (raw_uncalibrated)'
          }
        />

        {/* Compound Exposure Sentinel Card */}
        <RiskIndicator
          label="Compound Exposure"
          value={detail?.risk.compound_exposure}
          type="compound"
          subtext="min(Pc, Ps) dual-hazard sentinel; strictly NOT a joint probability"
        />
      </div>

      {/* Partial Coverage Alert (if applicable) */}
      {isPartial && (
        <AdvisoryBanner
          type="partial-coverage"
          title="Schedule Baseline Unobserved"
          message="Baseline milestone completion dates were unrecorded in canonical MoSPI reporting for this asset. Cost overrun risk Pc serves as the sole multi-hazard attention score. This indicator highlights missing reporting rather than zero schedule risk."
        />
      )}

      {/* Project Point-in-Time Baseline Metadata */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Administrative & Geographic Identity</CardTitle>
            <CardDescription>Verified MoSPI reporting attributes at July 31, 2025 cutoff</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-2 border-b border-slate-100/80">
              <span className="text-slate-500 flex items-center gap-1.5">
                <Building className="w-3.5 h-3.5" /> Executing Agency
              </span>
              <span className="font-semibold text-slate-900">{detail?.project.agency}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100/80">
              <span className="text-slate-500 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5" /> State / Jurisdiction
              </span>
              <span className="font-semibold text-slate-900">{detail?.project.state}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100/80">
              <span className="text-slate-500 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" /> Active Project Age
              </span>
              <span className="font-semibold text-slate-900">{detail?.project.project_age_months} Months</span>
            </div>
            <div className="flex items-center justify-between py-1.5">
              <span className="text-slate-500 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" /> Observation Snapshot
              </span>
              <span className="font-mono text-slate-700">2025-07-01 (Cutoff: July 31, 2025)</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Financial & Physical Outlay Divergence</CardTitle>
            <CardDescription>Sanctioned capital vs actual progress metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-2 border-b border-slate-100/80">
              <span className="text-slate-500 flex items-center gap-1.5">
                <IndianRupee className="w-3.5 h-3.5" /> Original Sanctioned Cost
              </span>
              <span className="font-semibold text-slate-900">
                {formatCrores(detail?.project.original_cost_crore)}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100/80">
              <span className="text-slate-500 flex items-center gap-1.5">
                <IndianRupee className="w-3.5 h-3.5" /> Cumulative Financial Outlay
              </span>
              <span className="font-semibold text-slate-900">
                {formatCrores(detail?.project.cumulative_expenditure_crore)}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100/80">
              <span className="text-slate-500 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5" /> Physical Progress %
              </span>
              <span className="font-semibold text-slate-900">
                {detail?.project.physical_progress_pct.toFixed(1)}%
              </span>
            </div>
            <div className="flex items-center justify-between py-1.5">
              <span className="text-slate-500 flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5" /> Physical vs Financial Divergence
              </span>
              <span className="inline-flex items-center rounded-md bg-slate-100 border border-slate-200 px-2 py-1 font-bold font-mono text-slate-800">
                +{detail?.project.divergence.toFixed(2)} Index
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Non-Causal Governance Notice */}
      <AdvisoryBanner
        type="non-causal"
        message="Dual-hazard model probabilities describe statistical associations in historical MoSPI reporting; they do not establish causal fault or contractor liability."
      />
    </div>
  );
};








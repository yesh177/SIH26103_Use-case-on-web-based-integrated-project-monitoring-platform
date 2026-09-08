import React from 'react';
import { useParams, NavLink } from 'react-router-dom';
import { PageHeader } from '../../components/common/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { AdvisoryBanner } from '../../components/ui/AdvisoryBanner';
import { useProjectInterventions, useProjectDetail } from '../../hooks/useProjects';
import { cn } from '../../lib/utils';
import {
  FileSpreadsheet,
  Network,
  ClipboardCheck,
  Clock,
  CheckSquare,
  FileCheck2,
} from 'lucide-react';

export const ProjectInterventionsPage: React.FC = () => {
  const { canonicalProjectKey } = useParams<{ canonicalProjectKey: string }>();
  const projectKey = canonicalProjectKey || 'PROJ-PAIMANA-400119';

  const { data: detail } = useProjectDetail(projectKey);
  const { data: intervention } = useProjectInterventions(projectKey);

  const priorityConfigs = {
    PRIORITY_1: {
      label: 'PRIORITY 1 — URGENT EXECUTIVE REVIEW',
      urgencyNote: 'Joint technical review committee convene within 14 business days',
      badgeClass: 'bg-red-50 text-red-700 border-red-200',
    },
    PRIORITY_2: {
      label: 'PRIORITY 2 — MONTHLY COMMITTEE REVIEW',
      urgencyNote: 'Monthly inter-ministerial review committee agenda item',
      badgeClass: 'bg-amber-50 text-amber-800 border-amber-200',
    },
    PRIORITY_3: {
      label: 'PRIORITY 3 — QUARTERLY TRACKING',
      urgencyNote: 'Standard quarterly milestone validation cadence',
      badgeClass: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    },
    PRIORITY_4: {
      label: 'PRIORITY 4 — BASELINE CADENCE',
      urgencyNote: 'Routine CPSE monthly reporting monitoring',
      badgeClass: 'bg-slate-100 text-slate-700 border-slate-200',
    },
  };

  const priorityMeta =
    priorityConfigs[intervention?.intervention_priority || 'PRIORITY_1'];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <PageHeader
        title="Intervention Action Panel"
        subtitle={`Evidence-grounded operational monitoring directives and protocol assignments for ${projectKey}.`}
        breadcrumbs={[
          { label: 'Home', href: '/dashboard' },
          { label: 'Risk Ranking', href: '/risk-ranking' },
          { label: detail?.project.project_name || projectKey, href: `/projects/${projectKey}` },
          { label: 'Interventions' },
        ]}
        badge={
          <span
            className={cn(
              'text-xs font-bold px-3 py-1 rounded-md border tracking-wide uppercase',
              priorityMeta.badgeClass
            )}
          >
            {priorityMeta.label}
          </span>
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

      {/* Official MoSPI Governance Notice - Non-Negotiable Requirement */}
      <AdvisoryBanner
        type="governance"
        title="Official MoSPI Supervisory Protocol Notice"
        message="Advisory decision support for supervisory review. Automated administrative sanctions, budget penalties, or contract cancellations are strictly prohibited."
      />

      {/* Operational Protocol Directives */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Primary Action Card */}
        <Card className="border-blue-200/80 shadow-[0_6px_20px_rgba(37,99,235,0.08)]">
          <CardHeader className="bg-blue-50/40">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-blue-800 uppercase tracking-wider">
                Primary Assigned Protocol
              </span>
              <Badge variant="default" className="font-mono">
                {intervention?.primary_action}
              </Badge>
            </div>
            <CardTitle className="text-lg mt-1 text-slate-900">
              Joint Technical & Financial Audit
            </CardTitle>
            <CardDescription className="flex items-center gap-1.5 text-blue-800">
              <Clock className="w-3.5 h-3.5" />
              <span>{priorityMeta.urgencyNote}</span>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-4 text-xs leading-relaxed text-slate-700">
            <div className="p-3 bg-slate-50 rounded-md border border-slate-200">
              <span className="font-semibold text-slate-900 block mb-1">
                Operational Rationale:
              </span>
              <p>{intervention?.priority_reason}</p>
            </div>

            <div className="space-y-2">
              <span className="font-semibold text-slate-900 block">
                Standard Inspection Checklist:
              </span>
              <ul className="space-y-1.5 text-slate-600">
                <li className="flex items-start gap-2">
                  <CheckSquare className="w-4 h-4 text-blue-700 shrink-0 mt-0.5" />
                  <span>Reconcile reported cumulative financial outlay against physical work packages.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckSquare className="w-4 h-4 text-blue-700 shrink-0 mt-0.5" />
                  <span>Verify whether site obstacles (land acquisition, clearances) drive financial divergence.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckSquare className="w-4 h-4 text-blue-700 shrink-0 mt-0.5" />
                  <span>Conduct independent engineering verification of remaining milestone timelines.</span>
                </li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Secondary Action & Evidence Grounding */}
        <div className="space-y-4">
          {/* Secondary Action Card */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  Secondary Follow-Up Protocol
                </span>
                <Badge variant="neutral" className="font-mono">
                  {intervention?.secondary_action}
                </Badge>
              </div>
              <CardTitle className="text-base mt-1">
                Site Verification & Progress Audit
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0 text-xs text-slate-600">
              <p>
                Deploy regional field engineering team to inspect physical construction progress against reported milestone deliverables before sanctioning revised budget tranches.
              </p>
            </CardContent>
          </Card>

          {/* Evidence Grounding Card */}
          <Card className="bg-slate-50/70 border-slate-200/80 shadow-[0_2px_10px_rgba(15,23,42,0.035)]">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <FileCheck2 className="w-4 h-4 text-blue-700" />
                <span>Deterministic Evidence Trigger</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs space-y-2">
              <div className="flex items-center justify-between py-1 border-b border-slate-200">
                <span className="text-slate-500">Trigger Feature</span>
                <span className="font-mono font-semibold text-slate-800">
                  {intervention?.evidence_feature}
                </span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-200">
                <span className="text-slate-500">Trigger Value</span>
                <span className="font-mono font-bold text-red-700">
                  {intervention?.evidence_value}
                </span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-slate-500">Data Quality Audit Flag</span>
                <Badge variant="info" className="font-mono text-[10px]">
                  {intervention?.data_quality_flag}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Governance Disclaimer */}
      <AdvisoryBanner
        type="custom"
        title="Non-Punitive Surveillance Guarantee"
        message={intervention?.governance_note || 'Intervention advisory protocol only. Automated sanctions or budget freezes are strictly prohibited.'}
      />
    </div>
  );
};






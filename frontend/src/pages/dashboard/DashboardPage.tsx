import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../../components/common/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { TierBadge } from '../../components/ui/TierBadge';
import { CoverageBadge } from '../../components/ui/CoverageBadge';
import { AdvisoryBanner } from '../../components/ui/AdvisoryBanner';
import { Button } from '../../components/ui/Button';
import { usePortfolioSummary } from '../../hooks/useProjects';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  AlertOctagon,
  CheckCircle,
  HelpCircle,
  ArrowRight,
  Layers,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = usePortfolioSummary();

  const attentionTierChartData = [
    { tier: "Tier 1", projects: summary?.tier_distribution?.["Tier 1"] ?? 0, threshold: "= 0.9947" },
    { tier: "Tier 2", projects: summary?.tier_distribution?.["Tier 2"] ?? 0, threshold: "0.9833–<0.9947" },
    { tier: "Tier 3", projects: summary?.tier_distribution?.["Tier 3"] ?? 0, threshold: "0.9067–<0.9833" },
    { tier: "Tier 4", projects: summary?.tier_distribution?.["Tier 4"] ?? 0, threshold: "< 0.9067" },
  ];

  const actionDistributionData = [
    { name: "Data Quality Review", value: summary?.action_distribution?.DATA_QUALITY_REVIEW ?? 0 },
    { name: "Joint Cost/Schedule Review", value: summary?.action_distribution?.JOINT_COST_SCHEDULE_REVIEW ?? 0 },
    { name: "Schedule Review", value: summary?.action_distribution?.SCHEDULE_REVIEW ?? 0 },
    { name: "Completion Status Review", value: summary?.action_distribution?.COMPLETION_STATUS_REVIEW ?? 0 },
    { name: "Cost Review", value: summary?.action_distribution?.COST_REVIEW ?? 0 },
    { name: "Progress Verification", value: summary?.action_distribution?.PROGRESS_VERIFICATION ?? 0 },
    { name: "Expenditure Progress Review", value: summary?.action_distribution?.EXPENDITURE_PROGRESS_REVIEW ?? 0 },
  ];

  const actionChartColors = [
    "#2563EB",
    "#3B82F6",
    "#60A5FA",
    "#93C5FD",
    "#1D4ED8",
    "#1E40AF",
    "#64748B",
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Portfolio Overview Dashboard"
        subtitle="Executive surveillance of 437 central infrastructure projects tracked under MoSPI (July 2025 - July 2026 prospective evaluation cohort)."
        breadcrumbs={[{ label: 'Home' }, { label: 'Portfolio Overview' }]}
        badge={
          <span className="text-[11px] font-semibold bg-blue-50 text-blue-800 border border-blue-200 px-2 py-0.5 rounded">
            FROZEN COHORT N=437
          </span>
        }
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/risk-ranking')}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            View Leaderboard
          </Button>
        }
      />

      {/* Official MoSPI Governance Notice */}
      <AdvisoryBanner
        type="governance"
        message="Advisory decision support for supervisory review. Automated administrative sanctions, budget penalties, or contract cancellations are strictly prohibited."
      />

      {/* 4 Core Macro KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Projects */}
        <Card className="border-slate-200">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Monitored Cohort
              </p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">
                {isLoading ? '...' : summary?.total_projects || 437}
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Projects in Evaluation Cohort</p>
            </div>
            <div className="p-3 bg-blue-50 text-blue-700 rounded-lg border border-blue-100">
              <Layers className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        {/* Tier 1 Priority Focus */}
        <Card className="border-red-200 bg-red-50/30">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-1.5">
                <p className="text-xs font-semibold uppercase tracking-wider text-red-800">
                  Tier 1 Attention
                </p>
                <TierBadge tier="Tier 1" size="sm" />
              </div>
              <h3 className="text-2xl font-bold text-red-700 mt-1">
                {isLoading ? '...' : summary?.tier_distribution['Tier 1'] || 44}
              </h3>
              <p className="text-[11px] text-red-600/80 mt-0.5">Tier 1 Quantile Priority Cohort</p>
            </div>
            <div className="p-3 bg-red-100 text-red-700 rounded-lg border border-red-200">
              <AlertOctagon className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        {/* Full Coverage Assets */}
        <Card className="border-blue-200 bg-blue-50/20">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-1.5">
                <p className="text-xs font-semibold uppercase tracking-wider text-blue-800">
                  Full Coverage
                </p>
                <CoverageBadge coverage="FULL" showIcon={false} size="sm" />
              </div>
              <h3 className="text-2xl font-bold text-blue-800 mt-1">
                {isLoading ? '...' : summary?.coverage_breakdown.full_coverage || 305}
              </h3>
              <p className="text-[11px] text-blue-700/80 mt-0.5">Cost & Schedule Baselines Available</p>
            </div>
            <div className="p-3 bg-blue-100 text-blue-800 rounded-lg border border-blue-200">
              <CheckCircle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        {/* Partial Coverage Assets */}
        <Card className="border-amber-200 bg-amber-50/30">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-1.5">
                <p className="text-xs font-semibold uppercase tracking-wider text-amber-800">
                  Partial Coverage
                </p>
                <CoverageBadge coverage="PARTIAL" showIcon={false} size="sm" />
              </div>
              <h3 className="text-2xl font-bold text-amber-800 mt-1">
                {isLoading ? '...' : summary?.coverage_breakdown.partial_coverage || 132}
              </h3>
              <p className="text-[11px] text-amber-700 mt-0.5">Schedule Milestone Unrecorded</p>
            </div>
            <div className="p-3 bg-amber-100 text-amber-800 rounded-lg border border-amber-200">
              <HelpCircle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Screen 1 Interactive Visualizations Placeholder Shell */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Attention Quantile Distribution */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Attention Score Quantile Distribution</CardTitle>
                <CardDescription>
                  Empirical quantile priority tiers across the 437 projects (max(Pc, Ps))
                </CardDescription>
              </div>
              <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded font-mono">
                Formula: max(Pc, Ps)
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-64 bg-slate-50 border border-slate-200 rounded-lg p-3">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={attentionTierChartData}
                  margin={{ top: 10, right: 20, left: 0, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="tier" tick={{ fontSize: 12 }} />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fontSize: 12 }}
                    label={{
                      value: "Projects",
                      angle: -90,
                      position: "insideLeft",
                      style: { fontSize: 11 },
                    }}
                  />
                  <Tooltip
                    formatter={(value: number) => [`${value} projects`, "Cohort"]}
                    labelFormatter={(label) => {
                      const item = attentionTierChartData.find(
                        (entry) => entry.tier === label
                      );
                      return `${label} · Score ${item?.threshold ?? ""}`;
                    }}
                  />
                  <Bar
                    dataKey="projects"
                    name="Projects"
                    fill="#2563EB"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>          </CardContent>
        </Card>

        {/* Primary Action Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Supervisory Action Distribution</CardTitle>
            <CardDescription>7 Standardized MoSPI Monitoring Protocols</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="min-h-64 bg-slate-50 border border-slate-200 rounded-lg p-3">
              <div className="grid grid-cols-[1.15fr_0.85fr] gap-3 h-full">
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={actionDistributionData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={48}
                        outerRadius={72}
                        paddingAngle={2}
                      >
                        {actionDistributionData.map((entry, index) => (
                          <Cell
                            key={`action-cell-${entry.name}`}
                            fill={actionChartColors[index % actionChartColors.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value: number) => [`${value} projects`, "Protocol"]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="flex flex-col justify-center gap-1 text-[10px]">
                  {actionDistributionData.map((action, index) => (
                    <div
                      key={action.name}
                      className="flex items-center justify-between gap-2"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span
                          className="w-2.5 h-2.5 rounded-sm shrink-0"
                          style={{
                            backgroundColor:
                              actionChartColors[index % actionChartColors.length],
                          }}
                        />
                        <span className="text-slate-600 truncate">
                          {action.name}
                        </span>
                      </div>
                      <span className="font-semibold text-slate-900 shrink-0">
                        {action.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <p className="text-[10px] text-slate-400 text-center pt-2 mt-2 border-t border-slate-200">
                Controlled Action Taxonomy (Section 17.1)
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Non-Causal Technical Disclaimer */}
      <AdvisoryBanner
        type="non-causal"
        message="All model outputs represent empirical statistical associations observed in retrospective MoSPI holdout cohorts. Risk drivers and probabilities do not imply administrative culpability, negligence, or contractual breach."
      />
    </div>
  );
};










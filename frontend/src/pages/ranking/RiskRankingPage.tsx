import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { PageHeader } from '../../components/common/PageHeader';
import { Card, CardContent } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { TierBadge } from '../../components/ui/TierBadge';
import { CoverageBadge } from '../../components/ui/CoverageBadge';
import { AdvisoryBanner } from '../../components/ui/AdvisoryBanner';
import { useProjectRanking } from '../../hooks/useProjects';
import { AttentionTier, RiskCoverage } from '../../types/models';
import { formatProbability } from '../../lib/utils';
import { Search, Filter, ChevronLeft, ChevronRight, ArrowRight, ArrowUp, ArrowDown } from 'lucide-react';

export const RiskRankingPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedTier, setSelectedTier] = useState<AttentionTier | undefined>(undefined);
  const [selectedCoverage, setSelectedCoverage] = useState<RiskCoverage | undefined>(undefined);
  const [selectedState, setSelectedState] = useState<string | undefined>(undefined);
  const [selectedAgency, setSelectedAgency] = useState<string | undefined>(undefined);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState<'rank' | 'attention' | 'cost' | 'schedule'>('rank');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const { data: rankingData, isLoading } = useProjectRanking({
    tier: selectedTier,
    coverage: selectedCoverage,
    state: selectedState,
    agency: selectedAgency,
    search: searchQuery,
    limit: 50,
    offset: (currentPage - 1) * 50,
  });

  const projects = rankingData?.data || [];
  const sortedProjects = [...projects].sort((a, b) => {
    let comparison = 0;

    if (sortField === 'rank') {
      comparison = a.portfolio_rank - b.portfolio_rank;
    } else if (sortField === 'attention') {
      comparison = a.attention_score - b.attention_score;
    } else if (sortField === 'cost') {
      comparison = a.cost_risk_probability - b.cost_risk_probability;
    } else if (sortField === 'schedule') {
      const aValue = a.schedule_risk_probability ?? -1;
      const bValue = b.schedule_risk_probability ?? -1;
      comparison = aValue - bValue;
    }

    return sortDirection === 'asc' ? comparison : -comparison;
  });

  const handleSort = (field: 'rank' | 'attention' | 'cost' | 'schedule') => {
    if (sortField === field) {
      setSortDirection((direction) => direction === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection(field === 'rank' ? 'asc' : 'desc');
    }
    setCurrentPage(1);
  };

  const SortIcon = ({ field }: { field: 'rank' | 'attention' | 'cost' | 'schedule' }) => {
    if (sortField !== field) {
      return null;
    }

    return sortDirection === 'asc'
      ? <ArrowUp className="w-3 h-3 inline ml-1" />
      : <ArrowDown className="w-3 h-3 inline ml-1" />;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Risk Ranking Leaderboard"
        subtitle="Standard competition ranking (min-rank ties #1 to #419) prioritizing executive monitoring attention across 437 central projects."
        breadcrumbs={[{ label: 'Home', href: '/dashboard' }, { label: 'Risk Ranking Leaderboard' }]}
        badge={
          <span className="text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded">
            Ranked by Attention Score DESC
          </span>
        }
      />

      {/* Control & Filter Toolbar */}
      <Card>
        <CardContent className="p-4 space-y-3">
          <div className="flex flex-col md:flex-row items-center gap-3">
            {/* Search Input */}
            <div className="flex-1 w-full md:min-w-[280px] lg:min-w-[320px] rounded-lg">
              <Input
                placeholder="Search project name, key, agency, or state..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={<Search className="w-4 h-4" />}
              />
            </div>

            {/* Quick Tier Filters */}
            <div className="flex items-center gap-1.5 shrink-0 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
              <span className="text-xs font-semibold text-slate-500 mr-1 flex items-center gap-1">
                <Filter className="w-3.5 h-3.5" /> Tier:
              </span>
              <button
                onClick={() => setSelectedTier(undefined)}
                className={`px-2.5 py-1 rounded text-xs font-semibold border transition-colors ${
                  selectedTier === undefined
                    ? 'bg-blue-700 text-white border-blue-700'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                All
              </button>
              {(['Tier 1', 'Tier 2', 'Tier 3', 'Tier 4'] as AttentionTier[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setSelectedTier(selectedTier === t ? undefined : t)}
                  className={`px-2.5 py-1 rounded text-xs font-semibold border transition-colors ${
                    selectedTier === t
                      ? 'bg-slate-900 text-white border-slate-900'
                      : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            {/* State & Agency Filters */}
            <select
              value={selectedState ?? ""}
              onChange={(e) => setSelectedState(e.target.value || undefined)}
              className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              <option value="">All States</option>
              <option value="Madhya Pradesh">Madhya Pradesh</option>
              <option value="Jammu and Kashmir">Jammu and Kashmir</option>
              <option value="Odisha">Odisha</option>
            </select>

            <select
              value={selectedAgency ?? ""}
              onChange={(e) => setSelectedAgency(e.target.value || undefined)}
              className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              <option value="">All Agencies</option>
              <option value="WEST CENTRAL RAILWAY">West Central Railway</option>
              <option value="NORTHERN RAILWAY">Northern Railway</option>
              <option value="NHAI">NHAI</option>
            </select>

            {/* Coverage Toggle */}
            <div className="flex items-center gap-1 shrink-0 bg-slate-100/80 p-1 rounded-lg border border-slate-200 shadow-sm text-xs">
              <button
                onClick={() => setSelectedCoverage(undefined)}
                className={`px-2.5 py-1 rounded font-medium transition-colors ${
                  selectedCoverage === undefined ? 'bg-white text-slate-900 shadow-2xs font-semibold' : 'text-slate-600'
                }`}
              >
                All Coverage
              </button>
              <button
                onClick={() => setSelectedCoverage('FULL')}
                className={`px-2.5 py-1 rounded font-medium transition-colors ${
                  selectedCoverage === 'FULL' ? 'bg-white text-blue-700 shadow-2xs font-semibold' : 'text-slate-600'
                }`}
              >
                Full Only
              </button>
              <button
                onClick={() => setSelectedCoverage('PARTIAL')}
                className={`px-2.5 py-1 rounded font-medium transition-colors ${
                  selectedCoverage === 'PARTIAL' ? 'bg-white text-amber-800 shadow-2xs font-semibold' : 'text-slate-600'
                }`}
              >
                Partial Only
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Leaderboard Table Container */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-100/80 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4 w-16">
  <button onClick={() => handleSort("rank")} className="font-semibold hover:text-blue-700">
    Rank <SortIcon field="rank" />
  </button>
</th>
                <th className="py-3 px-4">Project Name & Key</th>
                <th className="py-3 px-4">Agency / State</th>
                <th className="py-3 px-4">Coverage</th>
                <th className="py-3 px-4 text-right">
  <button onClick={() => handleSort("cost")} className="font-semibold hover:text-blue-700">
    Cost Risk (Pc) <SortIcon field="cost" />
  </button>
</th>
                <th className="py-3 px-4 text-right">
  <button onClick={() => handleSort("schedule")} className="font-semibold hover:text-blue-700">
    Schedule (Ps) <SortIcon field="schedule" />
  </button>
</th>
                <th className="py-3 px-4 text-right">
  <button onClick={() => handleSort("attention")} className="font-semibold hover:text-blue-700">
    Attention <SortIcon field="attention" />
  </button>
</th>
                <th className="py-3 px-4">Priority Tier</th>
                <th className="py-3 px-4">Primary Protocol</th>
                <th className="py-3 px-4 text-center w-20">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400">
                    Loading leaderboard rankings...
                  </td>
                </tr>
              ) : projects.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400">
                    No projects found matching the filter criteria.
                  </td>
                </tr>
              ) : (
                sortedProjects.map((proj) => (
                  <tr
                    key={proj.canonical_project_key}
                    className="hover:bg-blue-50/40 transition-colors cursor-pointer group border-b border-slate-100 last:border-b-0"
                    onClick={() => navigate(`/projects/${proj.canonical_project_key}`)}
                  >
                    <td className="py-3.5 px-4 font-bold text-slate-900">
                      <span
                        className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs ${
                          proj.portfolio_rank <= 10
                            ? 'bg-blue-50 text-blue-700 font-bold border border-blue-100'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        #{proj.portfolio_rank}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 max-w-xs">
                      <Link
                        to={`/projects/${proj.canonical_project_key}`}
                        className="font-semibold text-slate-900 group-hover:text-blue-700 line-clamp-1"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {proj.project_name}
                      </Link>
                      <span className="font-mono text-[10px] text-slate-400 block mt-0.5">
                        {proj.canonical_project_key}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="block font-medium text-slate-800 line-clamp-1">{proj.agency}</span>
                      <span className="text-[11px] text-slate-500 block">{proj.state}</span>
                    </td>
                    <td className="py-3.5 px-4">
                      <CoverageBadge coverage={proj.risk_coverage} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono font-semibold text-slate-900">
                      {formatProbability(proj.cost_risk_probability)}
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono font-medium">
                      {proj.schedule_risk_probability !== null ? (
                        <span className="text-slate-900">{formatProbability(proj.schedule_risk_probability)}</span>
                      ) : (
                        <span className="text-amber-700 italic text-[11px]">Unobserved</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono font-bold text-blue-700">
                      {formatProbability(proj.attention_score)}
                    </td>
                    <td className="py-3.5 px-4">
                      <TierBadge tier={proj.attention_tier} size="sm" />
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-block text-[11px] bg-slate-100 text-slate-800 px-2 py-0.5 rounded font-mono">
                        {proj.primary_action}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/projects/${proj.canonical_project_key}`);
                        }}
                        className="p-1 text-slate-400 group-hover:text-blue-700"
                        title="View Full Profile"
                      >
                        <ArrowRight className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Shell */}
        <div className="p-4 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <div>
            Showing {projects.length === 0 ? 0 : (currentPage - 1) * 50 + 1} to {(currentPage - 1) * 50 + projects.length} of {rankingData?.total_records || 0}{rankingData?.total_records && rankingData.total_records < 437 ? " representative demo records" : " monitored assets"}
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
              leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
            >
              Previous
            </Button>

            <span className="px-3 py-1 bg-slate-100 text-slate-800 rounded font-semibold text-xs">
              Page {currentPage} of {Math.max(1, Math.ceil((rankingData?.total_records || 0) / 50))}
            </span>

            <Button
              variant="outline"
              size="sm"
              disabled={currentPage >= Math.max(1, Math.ceil((rankingData?.total_records || 0) / 50))}
              onClick={() => setCurrentPage((page) => page + 1)}
              rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
            >
              Next
            </Button>
          </div>
        </div>
      </Card>

      {/* Partial Coverage Reminder Notice */}
      <AdvisoryBanner
        type="partial-coverage"
        message="For the 132 projects lacking baseline schedule milestones, attention score equals cost risk Pc alone. Partial coverage status is displayed prominently to avoid misinterpreting missing schedule records as zero risk."
      />
    </div>
  );
};

















import {
  PortfolioSummary,
  ProjectSummary,
  UnifiedProjectDetail,
  RiskDriversProfile,
  RiskScoreMetrics,
  InterventionDirectives,
} from '../types/models';
import { PaginatedResponse, RankingResponse, ProjectQueryParams, RankingQueryParams } from '../types/api';
import {
  MOCK_PORTFOLIO_SUMMARY,
  MOCK_PROJECT_SUMMARIES,
  MOCK_PROJECT_DETAIL,
  MOCK_RISK_DRIVERS,
} from './mockData';

/**
 * Mock Data Service mimicking docs/api_contract.md endpoints
 * Used for local UI development before full FastAPI integration
 */
export const mockService = {
  getPortfolioSummary: async (): Promise<PortfolioSummary> => {
    await delay(150);
    return { ...MOCK_PORTFOLIO_SUMMARY };
  },

  getProjects: async (params?: ProjectQueryParams): Promise<PaginatedResponse<ProjectSummary>> => {
    await delay(200);
    let filtered = [...MOCK_PROJECT_SUMMARIES];

    if (params?.tier) {
      filtered = filtered.filter((p) => p.attention_tier === params.tier);
    }
    if (params?.coverage) {
      filtered = filtered.filter((p) => p.risk_coverage === params.coverage);
    }
    if (params?.search) {
      const q = params.search.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.project_name.toLowerCase().includes(q) ||
          p.canonical_project_key.toLowerCase().includes(q) ||
          p.agency.toLowerCase().includes(q)
      );
    }

    return {
      total_records: filtered.length,
      page: params?.page || 1,
      page_size: params?.page_size || 20,
      total_pages: Math.ceil(filtered.length / (params?.page_size || 20)) || 1,
      data: filtered,
    };
  },

  getRanking: async (params?: RankingQueryParams): Promise<RankingResponse<ProjectSummary>> => {
    await delay(180);
    let filtered = [...MOCK_PROJECT_SUMMARIES].sort((a, b) => a.portfolio_rank - b.portfolio_rank);

    if (params?.tier) {
      filtered = filtered.filter((p) => p.attention_tier === params.tier);
    }
    if (params?.coverage) {
      filtered = filtered.filter((p) => p.risk_coverage === params.coverage);
    }
    if (params?.state) {
      filtered = filtered.filter((p) => p.state === params.state);
    }
    if (params?.agency) {
      filtered = filtered.filter((p) => p.agency === params.agency);
    }
    if (params?.search) {
      const q = params.search.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.project_name.toLowerCase().includes(q) ||
          p.canonical_project_key.toLowerCase().includes(q) ||
          p.agency.toLowerCase().includes(q) ||
          p.state.toLowerCase().includes(q)
      );
    }

    const offset = params?.offset || 0;
    const limit = params?.limit || 50;

    return {
      total_records: filtered.length,
      limit,
      offset,
      data: filtered.slice(offset, offset + limit),
    };
  },

  getProjectDetail: async (key: string): Promise<UnifiedProjectDetail> => {
    await delay(200);
    const summary = MOCK_PROJECT_SUMMARIES.find((p) => p.canonical_project_key === key);
    if (!summary) {
      // Return default sample detail with the requested key
      return {
        ...MOCK_PROJECT_DETAIL,
        project: { ...MOCK_PROJECT_DETAIL.project, canonical_project_key: key },
        risk: { ...MOCK_PROJECT_DETAIL.risk, canonical_project_key: key },
        intervention: { ...MOCK_PROJECT_DETAIL.intervention, canonical_project_key: key },
      };
    }
    return {
      project: {
        ...MOCK_PROJECT_DETAIL.project,
        canonical_project_key: summary.canonical_project_key,
        project_name: summary.project_name,
        state: summary.state,
        agency: summary.agency,
      },
      risk: {
        ...MOCK_PROJECT_DETAIL.risk,
        canonical_project_key: summary.canonical_project_key,
        portfolio_rank: summary.portfolio_rank,
        attention_score: summary.attention_score,
        attention_tier: summary.attention_tier,
        risk_coverage: summary.risk_coverage,
        cost_risk_probability: summary.cost_risk_probability,
        schedule_risk_probability: summary.schedule_risk_probability,
        compound_exposure: summary.compound_exposure,
      },
      intervention: {
        ...MOCK_PROJECT_DETAIL.intervention,
        canonical_project_key: summary.canonical_project_key,
        intervention_priority: summary.intervention_priority,
        primary_action: summary.primary_action,
      },
    };
  },

  getProjectRisk: async (key: string): Promise<RiskScoreMetrics> => {
    await delay(150);
    const detail = await mockService.getProjectDetail(key);
    return detail.risk;
  },

  getProjectDrivers: async (key: string): Promise<RiskDriversProfile> => {
    await delay(200);
    return {
      ...MOCK_RISK_DRIVERS,
      canonical_project_key: key,
    };
  },

  getProjectInterventions: async (key: string): Promise<InterventionDirectives> => {
    await delay(150);
    const detail = await mockService.getProjectDetail(key);
    return detail.intervention;
  },
};

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}


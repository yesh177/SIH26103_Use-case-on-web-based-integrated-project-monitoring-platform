import { AttentionTier, RiskCoverage } from './models';

/**
 * Standard Paginated Response Structure
 */
export interface PaginatedResponse<T> {
  total_records: number;
  page: number;
  page_size: number;
  total_pages: number;
  data: T[];
}

/**
 * Leaderboard Ranking Response Structure
 */
export interface RankingResponse<T> {
  total_records: number;
  limit: number;
  offset: number;
  data: T[];
}

/**
 * Query Parameters for GET /projects
 */
export interface ProjectQueryParams {
  page?: number;
  page_size?: number;
  state?: string;
  agency?: string;
  tier?: AttentionTier;
  coverage?: RiskCoverage;
  sort_by?: 'portfolio_rank' | 'attention_score' | 'cost_risk_probability' | 'project_name';
  order?: 'asc' | 'desc';
  search?: string;
}

/**
 * Query Parameters for GET /projects/ranking
 */
export interface RankingQueryParams {
  limit?: number;
  offset?: number;
  state?: string;
  agency?: string;
  tier?: AttentionTier;
  coverage?: RiskCoverage;
  search?: string;
}

/**
 * Standard Error Response Envelope (RFC 7807 / PAIMANA Contract)
 */
export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details?: unknown;
    timestamp?: string;
  };
}



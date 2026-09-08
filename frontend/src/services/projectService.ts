import apiClient from './apiClient';
import { mockService } from '../mock/mockService';
import {
  PortfolioSummary,
  ProjectSummary,
  UnifiedProjectDetail,
  RiskDriversProfile,
  RiskScoreMetrics,
  InterventionDirectives,
} from '../types/models';
import { PaginatedResponse, RankingResponse, ProjectQueryParams, RankingQueryParams } from '../types/api';

/**
 * Service Configuration
 * By default in this frontend-first stage, use the mock service.
 * When VITE_USE_MOCK is explicitly 'false', calls are routed through the live Axios client.
 */
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

export const projectService = {
  getPortfolioSummary: async (): Promise<PortfolioSummary> => {
    if (USE_MOCK) return mockService.getPortfolioSummary();
    const res = await apiClient.get<PortfolioSummary>('/portfolio/summary');
    return res.data;
  },

  getProjects: async (params?: ProjectQueryParams): Promise<PaginatedResponse<ProjectSummary>> => {
    if (USE_MOCK) return mockService.getProjects(params);
    const res = await apiClient.get<PaginatedResponse<ProjectSummary>>('/projects', { params });
    return res.data;
  },

  getRanking: async (params?: RankingQueryParams): Promise<RankingResponse<ProjectSummary>> => {
    if (USE_MOCK) return mockService.getRanking(params);
    const res = await apiClient.get<RankingResponse<ProjectSummary>>('/projects/ranking', { params });
    return res.data;
  },

  getProjectDetail: async (key: string): Promise<UnifiedProjectDetail> => {
    if (USE_MOCK) return mockService.getProjectDetail(key);
    const res = await apiClient.get<UnifiedProjectDetail>(`/projects/${key}`);
    return res.data;
  },

  getProjectRisk: async (key: string): Promise<RiskScoreMetrics> => {
    if (USE_MOCK) return mockService.getProjectRisk(key);
    const res = await apiClient.get<RiskScoreMetrics>(`/projects/${key}/risk`);
    return res.data;
  },

  getProjectDrivers: async (key: string): Promise<RiskDriversProfile> => {
    if (USE_MOCK) return mockService.getProjectDrivers(key);
    const res = await apiClient.get<RiskDriversProfile>(`/projects/${key}/drivers`);
    return res.data;
  },

  getProjectInterventions: async (key: string): Promise<InterventionDirectives> => {
    if (USE_MOCK) return mockService.getProjectInterventions(key);
    const res = await apiClient.get<InterventionDirectives>(`/projects/${key}/interventions`);
    return res.data;
  },
};

export default projectService;

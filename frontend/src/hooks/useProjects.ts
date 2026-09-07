import { useQuery } from '@tanstack/react-query';
import projectService from '../services/projectService';
import { ProjectQueryParams, RankingQueryParams } from '../types/api';

export const QUERY_KEYS = {
  portfolioSummary: ['portfolio', 'summary'] as const,
  projectsList: (params?: ProjectQueryParams) => ['projects', 'list', params] as const,
  projectRanking: (params?: RankingQueryParams) => ['projects', 'ranking', params] as const,
  projectDetail: (key: string) => ['projects', 'detail', key] as const,
  projectRisk: (key: string) => ['projects', 'risk', key] as const,
  projectDrivers: (key: string) => ['projects', 'drivers', key] as const,
  projectInterventions: (key: string) => ['projects', 'interventions', key] as const,
};

export function usePortfolioSummary() {
  return useQuery({
    queryKey: QUERY_KEYS.portfolioSummary,
    queryFn: () => projectService.getPortfolioSummary(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useProjectsList(params?: ProjectQueryParams) {
  return useQuery({
    queryKey: QUERY_KEYS.projectsList(params),
    queryFn: () => projectService.getProjects(params),
    staleTime: 60 * 1000,
  });
}

export function useProjectRanking(params?: RankingQueryParams) {
  return useQuery({
    queryKey: QUERY_KEYS.projectRanking(params),
    queryFn: () => projectService.getRanking(params),
    staleTime: 60 * 1000,
  });
}

export function useProjectDetail(canonicalProjectKey: string) {
  return useQuery({
    queryKey: QUERY_KEYS.projectDetail(canonicalProjectKey),
    queryFn: () => projectService.getProjectDetail(canonicalProjectKey),
    enabled: Boolean(canonicalProjectKey),
    staleTime: 5 * 60 * 1000,
  });
}

export function useProjectDrivers(canonicalProjectKey: string) {
  return useQuery({
    queryKey: QUERY_KEYS.projectDrivers(canonicalProjectKey),
    queryFn: () => projectService.getProjectDrivers(canonicalProjectKey),
    enabled: Boolean(canonicalProjectKey),
    staleTime: 5 * 60 * 1000,
  });
}

export function useProjectInterventions(canonicalProjectKey: string) {
  return useQuery({
    queryKey: QUERY_KEYS.projectInterventions(canonicalProjectKey),
    queryFn: () => projectService.getProjectInterventions(canonicalProjectKey),
    enabled: Boolean(canonicalProjectKey),
    staleTime: 5 * 60 * 1000,
  });
}

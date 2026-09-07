/**
 * PAIMANA Data Models & Controlled Vocabularies
 * Authoritative Source: docs/api_contract.md and reports/MASTER_PRD.md
 */

export type AttentionTier = 'Tier 1' | 'Tier 2' | 'Tier 3' | 'Tier 4';

export type RiskCoverage = 'FULL' | 'PARTIAL';

export type InterventionPriority = 'PRIORITY_1' | 'PRIORITY_2' | 'PRIORITY_3' | 'PRIORITY_4';

export type PrimaryAction =
  | 'DATA_QUALITY_REVIEW'
  | 'JOINT_COST_SCHEDULE_REVIEW'
  | 'SCHEDULE_REVIEW'
  | 'COMPLETION_STATUS_REVIEW'
  | 'COST_REVIEW'
  | 'PROGRESS_VERIFICATION'
  | 'EXPENDITURE_PROGRESS_REVIEW';

export type RiskFocus =
  | 'SCHEDULE_RISK'
  | 'UNOBSERVED_SCHEDULE'
  | 'JOINT_COST_SCHEDULE'
  | 'COST_RISK'
  | 'BASELINE_MONITORING'
  | 'PROGRESS_FINANCIAL_DIVERGENCE'
  | 'COMPLETION_STATUS';

export type DriverDirection = 'INCREASES_RISK' | 'DECREASES_RISK' | 'NEUTRAL';

export type DataQualityFlag =
  | 'COMPLETE_BASELINE_DATA'
  | 'SCHEDULE_OUTCOME_UNOBSERVED'
  | 'MISSING_APPROVAL_DATE';

export type ProbabilityVariant = 'raw_uncalibrated';

/**
 * Baseline Project Descriptive Metadata (Entity 1: projects)
 */
export interface ProjectMetadata {
  canonical_project_key: string;
  source_project_id: number;
  project_name: string;
  state: string;
  agency: string;
  original_cost_crore: number;
  cumulative_expenditure_crore: number;
  expenditure_ratio?: number;
  physical_progress_pct: number;
  divergence: number;
  project_age_months: number;
  remaining_duration_months?: number | null;
  snapshot_date?: string;
}

/**
 * Isolated Risk Metrics and Probabilities (Entity 2: project_risk_scores)
 */
export interface RiskScoreMetrics {
  canonical_project_key: string;
  source_project_id?: number;
  project_name?: string;
  state?: string;
  agency?: string;
  attention_score: number;
  portfolio_rank: number;
  attention_tier: AttentionTier;
  risk_coverage: RiskCoverage;
  cost_risk_probability: number;
  schedule_risk_probability: number | null;
  compound_exposure: number | null;
  is_eligible_cost_target?: number;
  is_eligible_schedule_target?: number;
  models?: {
    cost_model: string;
    cost_probability_variant: ProbabilityVariant;
    schedule_model: string;
    schedule_probability_variant: ProbabilityVariant;
  };
  scoring_method_version?: string;
  snapshot_date?: string;
  prediction_cutoff_date?: string;
}

/**
 * Single local marginal reference perturbation driver
 */
export interface ExplainableDriverItem {
  rank: number;
  feature: string;
  feature_value?: number;
  impact: number;
  direction: DriverDirection;
  source_fact: string;
}

/**
 * Task-level explainable drivers (Cost or Schedule)
 */
export interface TaskRiskDrivers {
  task: 'cost_overrun' | 'schedule_slippage';
  is_eligible: number;
  predicted_risk_probability: number | null;
  top_drivers: ExplainableDriverItem[];
}

/**
 * Project Explainability Profile (Entity 3: project_risk_explanations)
 */
export interface RiskDriversProfile {
  canonical_project_key: string;
  cost_drivers: TaskRiskDrivers;
  schedule_drivers: TaskRiskDrivers;
  explanation_method: string;
  disclaimer: string;
}

/**
 * Operational Intervention Directives (Entity 4: project_intervention_priorities)
 */
export interface InterventionDirectives {
  canonical_project_key: string;
  intervention_priority: InterventionPriority;
  primary_action: PrimaryAction;
  secondary_action: PrimaryAction | string;
  risk_focus: RiskFocus;
  priority_reason: string;
  evidence_feature: string;
  evidence_value: number;
  evidence_direction?: DriverDirection;
  data_quality_flag: DataQualityFlag;
  governance_note: string;
}

/**
 * Summary Project Record for Catalogs and Leaderboard (GET /projects & GET /projects/ranking)
 */
export interface ProjectSummary {
  portfolio_rank: number;
  canonical_project_key: string;
  source_project_id: number;
  project_name: string;
  state: string;
  agency: string;
  attention_score: number;
  attention_tier: AttentionTier;
  risk_coverage: RiskCoverage;
  cost_risk_probability: number;
  schedule_risk_probability: number | null;
  compound_exposure: number | null;
  intervention_priority: InterventionPriority;
  primary_action: PrimaryAction;
}

/**
 * Unified Single-Project Profile (GET /projects/{canonical_project_key})
 */
export interface UnifiedProjectDetail {
  project: ProjectMetadata;
  risk: RiskScoreMetrics;
  intervention: InterventionDirectives;
}

/**
 * Portfolio Aggregate Summary (GET /portfolio/summary)
 */
export interface PortfolioSummary {
  total_projects: number;
  coverage_breakdown: {
    full_coverage: number;
    partial_coverage: number;
  };
  tier_distribution: Record<AttentionTier, number>;
  intervention_priority_distribution: Record<InterventionPriority, number>;
  action_distribution: Record<string, number>;
  risk_focus_distribution: Record<string, number>;
}

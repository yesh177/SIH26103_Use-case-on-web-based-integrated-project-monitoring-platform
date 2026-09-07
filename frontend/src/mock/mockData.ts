import {
  PortfolioSummary,
  ProjectSummary,
  UnifiedProjectDetail,
  RiskDriversProfile,
} from '../types/models';

/**
 * Portfolio-wide aggregate summary matching Master PRD & database_seed_contract.md
 */
export const MOCK_PORTFOLIO_SUMMARY: PortfolioSummary = {
  total_projects: 437,
  coverage_breakdown: {
    full_coverage: 305,
    partial_coverage: 132,
  },
  tier_distribution: {
    'Tier 1': 44,
    'Tier 2': 73,
    'Tier 3': 102,
    'Tier 4': 218,
  },
  intervention_priority_distribution: {
    PRIORITY_1: 44,
    PRIORITY_2: 73,
    PRIORITY_3: 102,
    PRIORITY_4: 218,
  },
  action_distribution: {
    DATA_QUALITY_REVIEW: 128,
    JOINT_COST_SCHEDULE_REVIEW: 90,
    SCHEDULE_REVIEW: 81,
    COMPLETION_STATUS_REVIEW: 79,
    COST_REVIEW: 29,
    PROGRESS_VERIFICATION: 24,
    EXPENDITURE_PROGRESS_REVIEW: 6,
  },
  risk_focus_distribution: {
    SCHEDULE_RISK: 159,
    UNOBSERVED_SCHEDULE: 128,
    JOINT_COST_SCHEDULE: 90,
    COST_RISK: 29,
    BASELINE_MONITORING: 24,
    PROGRESS_FINANCIAL_DIVERGENCE: 6,
    COMPLETION_STATUS: 1,
  },
};

/**
 * Initial sample projects for Leaderboard & Catalog
 * Represents Rank #1 (Full Coverage) and Rank #44 (Partial Coverage)
 */
export const MOCK_PROJECT_SUMMARIES: ProjectSummary[] = [
  {
    portfolio_rank: 1,
    canonical_project_key: 'PROJ-PAIMANA-400119',
    source_project_id: 16723,
    project_name: 'LALITPUR-SATNA-REWA-SINGRULI NL',
    state: 'Madhya Pradesh',
    agency: 'WEST CENTRAL RAILWAY',
    attention_score: 0.998,
    attention_tier: 'Tier 1',
    risk_coverage: 'FULL',
    cost_risk_probability: 0.998,
    schedule_risk_probability: 0.97,
    compound_exposure: 0.97,
    intervention_priority: 'PRIORITY_1',
    primary_action: 'JOINT_COST_SCHEDULE_REVIEW',
  },
  {
    portfolio_rank: 2,
    canonical_project_key: 'PROJ-PAIMANA-400220',
    source_project_id: 18451,
    project_name: 'UDHAMPUR-SRINAGAR-BARAMULLA RAIL LINK',
    state: 'Jammu and Kashmir',
    agency: 'NORTHERN RAILWAY',
    attention_score: 0.9975,
    attention_tier: 'Tier 1',
    risk_coverage: 'FULL',
    cost_risk_probability: 0.9975,
    schedule_risk_probability: 0.965,
    compound_exposure: 0.965,
    intervention_priority: 'PRIORITY_1',
    primary_action: 'JOINT_COST_SCHEDULE_REVIEW',
  },
  {
    portfolio_rank: 44,
    canonical_project_key: 'PROJ-PAIMANA-602099',
    source_project_id: 20412,
    project_name: 'FOUR LANING OF PARADIP PORT CONNECTIVITY',
    state: 'Odisha',
    agency: 'NATIONAL HIGHWAYS AUTHORITY OF INDIA',
    attention_score: 0.9947,
    attention_tier: 'Tier 1',
    risk_coverage: 'PARTIAL',
    cost_risk_probability: 0.9947,
    schedule_risk_probability: null, // Strictly null for partial coverage
    compound_exposure: null, // Strictly null for partial coverage
    intervention_priority: 'PRIORITY_1',
    primary_action: 'DATA_QUALITY_REVIEW',
  },
];

/**
 * Sample Unified Detail Profile for Rank #1 Project
 */
export const MOCK_PROJECT_DETAIL: UnifiedProjectDetail = {
  project: {
    canonical_project_key: 'PROJ-PAIMANA-400119',
    source_project_id: 16723,
    project_name: 'LALITPUR-SATNA-REWA-SINGRULI NL',
    state: 'Madhya Pradesh',
    agency: 'WEST CENTRAL RAILWAY',
    original_cost_crore: 247.66,
    cumulative_expenditure_crore: 5214.37,
    expenditure_ratio: 21.05,
    physical_progress_pct: 58.0,
    divergence: 20.47,
    project_age_months: 322.0,
    remaining_duration_months: -120.0,
    snapshot_date: '2025-07-01',
  },
  risk: {
    canonical_project_key: 'PROJ-PAIMANA-400119',
    attention_score: 0.998,
    portfolio_rank: 1,
    attention_tier: 'Tier 1',
    risk_coverage: 'FULL',
    cost_risk_probability: 0.998,
    schedule_risk_probability: 0.97,
    compound_exposure: 0.97,
    is_eligible_cost_target: 1,
    is_eligible_schedule_target: 1,
    models: {
      cost_model: 'RandomForestClassifier',
      cost_probability_variant: 'raw_uncalibrated',
      schedule_model: 'RandomForestClassifier',
      schedule_probability_variant: 'raw_uncalibrated',
    },
    scoring_method_version: 'module4_v1',
    snapshot_date: '2025-07-01',
    prediction_cutoff_date: '2025-07-01',
  },
  intervention: {
    canonical_project_key: 'PROJ-PAIMANA-400119',
    intervention_priority: 'PRIORITY_1',
    primary_action: 'JOINT_COST_SCHEDULE_REVIEW',
    secondary_action: 'PROGRESS_VERIFICATION',
    risk_focus: 'JOINT_COST_SCHEDULE',
    priority_reason:
      'High joint cost and schedule risk. Divergence 20.47 indicates expenditure outpacing physical progress.',
    evidence_feature: 'feat_physical_vs_financial_divergence',
    evidence_value: 20.47,
    evidence_direction: 'INCREASES_RISK',
    data_quality_flag: 'COMPLETE_BASELINE_DATA',
    governance_note:
      'Intervention advisory protocol only. Automated sanctions or budget freezes are strictly prohibited.',
  },
};

/**
 * Sample Explainable Drivers Profile
 */
export const MOCK_RISK_DRIVERS: RiskDriversProfile = {
  canonical_project_key: 'PROJ-PAIMANA-400119',
  cost_drivers: {
    task: 'cost_overrun',
    is_eligible: 1,
    predicted_risk_probability: 0.998,
    top_drivers: [
      {
        rank: 1,
        feature: 'feat_physical_vs_financial_divergence',
        feature_value: 20.47,
        impact: 0.1245,
        direction: 'INCREASES_RISK',
        source_fact:
          'Expenditure ratio (21.05) exceeds physical progress (58.00%) by 20.47 divergence index.',
      },
      {
        rank: 2,
        feature: 'feat_project_age_months',
        feature_value: 322.0,
        impact: 0.0812,
        direction: 'INCREASES_RISK',
        source_fact: 'Project has been active for 322.0 months since original sanction date.',
      },
      {
        rank: 3,
        feature: 'feat_cumulative_expenditure_crore',
        feature_value: 5214.37,
        impact: 0.0543,
        direction: 'INCREASES_RISK',
        source_fact:
          'Recorded cumulative expenditure is ₹5,214.37 Crore against ₹247.66 Crore baseline.',
      },
    ],
  },
  schedule_drivers: {
    task: 'schedule_slippage',
    is_eligible: 1,
    predicted_risk_probability: 0.97,
    top_drivers: [
      {
        rank: 1,
        feature: 'feat_remaining_original_duration_months',
        feature_value: -120.0,
        impact: 0.142,
        direction: 'INCREASES_RISK',
        source_fact: 'Project is 120.0 months past its originally sanctioned completion date.',
      },
      {
        rank: 2,
        feature: 'feat_physical_progress_pct',
        feature_value: 58.0,
        impact: 0.076,
        direction: 'INCREASES_RISK',
        source_fact: 'Cumulative physical completion is at 58.00%.',
      },
      {
        rank: 3,
        feature: 'feat_expenditure_to_original_cost_ratio',
        feature_value: 21.05,
        impact: 0.041,
        direction: 'INCREASES_RISK',
        source_fact: 'Cumulative expenditure ratio has reached 21.05.',
      },
    ],
  },
  explanation_method: 'tree_feature_importance_marginal_perturbation_v1',
  disclaimer:
    'Feature attributions reflect statistical associations observed in retrospective MoSPI holdout cohorts; they do not establish causal fault or contractor liability.',
};

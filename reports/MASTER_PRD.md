# PRODUCT REQUIREMENTS DOCUMENT (PRD)
## PAIMANA PREDICTIVE RISK INTELLIGENCE
### Integrated Decision-Support Platform for Central Infrastructure Monitoring

---

# 1. Document Control

* **Project Name**: PAIMANA Predictive Risk Intelligence
* **Problem Statement ID**: SIH26103 — Web-Based Integrated Project Monitoring Platform
* **Document Purpose**: Single Authoritative Master Product Requirements Document (PRD) consolidating the validated, frozen intelligence specifications from Modules 1 through 4 into an enterprise product blueprint for implementation, handoff, and jury presentation.
* **Document Status**: Frozen & Authoritative Master Specification
* **Authoritative Source**: Consolidates and unifies:
  - Canonical Data Extraction & Identity Resolution (`reports/module2b_canonical_snapshot_validation.md`, `reports/module2b_identity_resolution_validation.md`)
  - Point-in-Time Dataset Construction (`reports/module2c_pit_dataset_validation.md`)
  - Empirical Baselines & Linear Benchmarks (`reports/module3_cuf_vs_enhanced_results.md`)
  - Machine Learning Random Forest Benchmark (`reports/module3_random_forest_benchmark_results.md`)
  - Probability Calibration Evaluation (`reports/module3_probability_calibration_validation.md`)
  - Multi-Hazard Risk Scoring & Quality Audit (`reports/module4_risk_scoring_schema.md`, `reports/module4_risk_score_quality_audit.md`)
  - Explainable Risk Drivers (`reports/module4_explainability_validation.md`)
  - Intervention Prioritisation (`reports/module4_intervention_prioritisation.md`)
  - Product Contract & Engineering Handoff (`reports/module4_product_contract.md`, `reports/module4_frontend_backend_handoff.md`)
* **Scope**: Complete end-to-end intelligence chain across Modules 1 through 4, establishing data schemas, mathematical invariants, API contracts, UI components, governance boundaries, and pitch narratives.
* **Version**: 1.0.0 (Frozen Architecture)
* **Date**: September 2026

---

# 2. Executive Summary

Infrastructure monitoring across central ministries—coordinated via the Ministry of Statistics and Programme Implementation (MoSPI) and executing Central Public Sector Enterprises (CPSEs)—traditionally operates on retrospective accounting. Existing monitoring tools provide descriptive reporting: they document what expenditures have been incurred and what delays have already accumulated. However, descriptive dashboards cannot proactively indicate which active projects are statistically predisposed to future escalation or why.

**SIH26103** calls for an integrated, web-based project monitoring platform that transitions infrastructure oversight from reactive reporting to proactive, early-warning intelligence.

**Our Proposed System**:
> PAIMANA Predictive Risk Intelligence adds a predictive and prescriptive decision-support layer over project monitoring data, transforming descriptive monitoring into early-warning risk forecasting, explainable prioritisation, and evidence-grounded monitoring support.

PAIMANA achieves this by establishing a mathematically rigorous, point-in-time (PIT) longitudinal surveillance architecture. Operating on historical MoSPI project snapshots, the platform computes prospective 12-month risk probabilities for both cost overrun (>5%) and schedule slippage (>=3 months), aggregates them into a multi-hazard attention score, explains the underlying statistical drivers grounded in verifiable source facts, and maps distressed assets into conservative, non-punitive monitoring protocols.

PAIMANA does **not** claim autonomous project management or real-time causal determination; rather, it delivers an auditable, coverage-aware executive surveillance engine.

---

# 3. Problem Statement

### 3.1 SIH26103 Requirements Mapping
Problem Statement SIH26103 requires seven critical capabilities for modernizing infrastructure project monitoring. The table below documents the mapping between each requirement, our validated capability, implementation status, and concrete evidence within the repository:

| SIH Requirement | Our Capability | Status | Evidence |
| :--- | :--- | :---: | :--- |
| **1. Cost-Overrun Prediction** | Prospective binary classification of cost overrun $> 5\%$ over a 12-month horizon using point-in-time project features. | Implemented & Validated | `src/models/train_random_forest_benchmark.py`, `reports/module3_random_forest_benchmark_results.md` |
| **2. Time-Overrun Prediction** | Prospective binary classification of schedule slippage $\ge 3$ months over a 12-month forward window for eligible assets. | Implemented & Validated | `src/models/train_random_forest_benchmark.py`, `reports/module3_random_forest_benchmark_results.md` |
| **3. Project Risk Ranking** | Multi-hazard `attention_score` aggregating independent cost and schedule probabilities into empirical quantile tiers (Tiers 1–4). | Implemented & Validated | `src/scoring/generate_project_risk_scores.py`, `reports/module4_risk_scoring_schema.md` |
| **4. Driver Analysis** | Two-level explainability: global MDI feature rankings combined with local marginal reference perturbation grounded in MoSPI source facts. | Implemented & Validated | `src/explainability/explain_risk_drivers.py`, `reports/module4_explainability_validation.md` |
| **5. ML vs Conventional Statistical Methods** | Controlled benchmark comparing empirical majority-class baselines, Logistic Regression baselines, and Random Forest nonlinear models. | Implemented & Validated | `reports/module3_cuf_vs_enhanced_results.md`, `reports/module3_random_forest_benchmark_results.md` |
| **6. CUF vs Enhanced Variables** | Rigorous ablation demonstrating measurable predictive gain from domain-engineered PIT features over core conventional reporting fields. | Implemented & Validated | `src/models/evaluate_cuf_vs_enhanced.py`, `reports/module3_cuf_vs_enhanced_results.md` |
| **7. Early-Warning Decision Support** | Evidence-grounded intervention engine mapping predicted risks and data completeness into 7 standardized monitoring protocols. | Implemented & Validated | `src/interventions/generate_intervention_priorities.py`, `reports/module4_intervention_prioritisation.md` |

---

# 4. Product Vision

PAIMANA is a **Predictive Project Risk Intelligence Platform**.

Its mission is to transform public infrastructure oversight across the four-stage intelligence hierarchy:
$$\text{Descriptive Monitoring} \longrightarrow \text{Predictive Surveillance} \longrightarrow \text{Explainable Attribution} \longrightarrow \text{Prioritised Decision Support}$$

### Explicit System Boundaries (What PAIMANA Is NOT)
To maintain engineering credibility and governance compliance, PAIMANA is explicitly bounded:
* **NOT a generic dashboard**: It does not merely visualize static Excel spreadsheets or re-plot historic charts; it evaluates statistical risk horizons.
* **NOT an autonomous decision-maker**: It never makes automated executive decisions, overrides human engineers, or directs funds.
* **NOT a causal inference engine**: It does not prove root causes, contractor negligence, or legal culpability; it surfaces statistical risk associations.
* **NOT an engineering certification system**: It does not certify structural safety, soil stability, or physical construction quality.
* **NOT a sanctions or penalty engine**: It strictly forbids automated contractor blacklisting, contractual penalties, or budget freezes.

---

# 5. Core USP

### USP 1 — Point-in-Time Predictive Forecasting
Unlike naive ML models that train on static cross-sectional tables containing future leakage, PAIMANA strictly enforces Point-in-Time (PIT) isolation. All feature values are computed strictly from information available on or before the July 31, 2025 cutoff, forecasting forward to July 2026 outcomes.

### USP 2 — Temporal Validation
Evaluated via a rigorous retrospective 12-month temporal holdout protocol rather than arbitrary random cross-validation, guaranteeing realistic real-world prospective simulation.

### USP 3 — CUF vs Enhanced Feature Evaluation
Empirically proves the necessity of domain engineering. Demonstrates that adding logarithmic cost scaling, expenditure burn ratios, physical-financial divergence indices, project age, and completion flags dramatically enhances predictive power over raw core reporting fields alone.

### USP 4 — Explainable Risk Ranking
Replaces opaque "black-box" scores with transparent, two-tier explainability: global Random Forest MDI importances paired with project-specific local marginal reference perturbations ($\Delta = P_{\text{actual}} - P_{\text{ref}}$) directly linked to verifiable MoSPI snapshot facts.

### USP 5 — Evidence-Grounded Intervention Prioritisation
Bridges predictive analytics and administrative action by mapping statistical vulnerabilities to 7 standardized, non-punitive monitoring protocols (e.g. Field Audit, Milestone Review, Data Quality Review).

### USP 6 — Coverage-Aware Intelligence
Refuses to hide data blind spots. Projects missing baseline milestone dates are explicitly surfaced as `PARTIAL` coverage and `SCHEDULE_OUTCOME_UNOBSERVED`, guaranteeing that missing data is never misinterpreted as zero risk.

---

# 6. Users & Stakeholders

The platform serves four primary personas within the infrastructure monitoring ecosystem:

### 6.1 Project Monitoring Officials (MoSPI / Central Line Ministries)
* **Role**: Operational oversight officers tracking monthly physical progress and financial expenditures across central CPSE projects.
* **Goals**: Rapidly identify which active projects are deviating from baseline targets before delays compound into multi-year crises.
* **Information Needed**: Multi-hazard attention scores, physical-financial divergence indices, top risk drivers, and actionable inspection protocols.
* **Relevant Screens**: Risk Ranking Leaderboard, Project Detail Profile, Explainable Driver Panel, Intervention Action Panel.

### 6.2 Portfolio / Programme Managers (CPSE Leadership / Infrastructure Directors)
* **Role**: Senior executives managing multi-project portfolios (e.g., Railways, NHAI, Power CPSEs).
* **Goals**: Allocate scarce field engineering inspection teams and supervisory resources to projects exhibiting compound distress.
* **Information Needed**: High-level portfolio risk distribution, agency-wide vulnerability concentrations, action breakdown.
* **Relevant Screens**: Portfolio Overview Dashboard, Risk Ranking Leaderboard.

### 6.3 Analytical & Research Users (Public Policy & Infrastructure Economists)
* **Role**: Quantitative analysts studying systematic patterns in infrastructure cost escalation and schedule slippage.
* **Goals**: Evaluate feature importances, assess macro-level divergence patterns, and audit model performance metrics across project cohorts.
* **Information Needed**: CUF vs Enhanced ablations, confusion matrices, ROC/PR curves, Brier scores, feature attribution matrices.
* **Relevant Screens**: Portfolio Overview Dashboard, Driver Panel.

### 6.4 Administrative Decision-Support Users (Secretariat / Steering Committees)
* **Role**: High-level committees reviewing annual capital expenditure outlays and inter-ministerial coordination hurdles.
* **Goals**: Establish structured agendas for quarterly inter-ministerial review meetings with defensible, objective evidence.
* **Information Needed**: Clear executive summaries, verifiable source facts, non-causal advisory notes.
* **Relevant Screens**: Project Detail Profile, Intervention Action Panel.

*(Note: These user personas describe operational product roles within an integrated monitoring platform and do not alter existing statutory MoSPI administrative frameworks).*

---

# 7. End-to-End Product Workflow

The complete PAIMANA pipeline processes raw administrative data into actionable supervisory intelligence across four operational categories:

```text
MoSPI / PAIMANA Source Data (June 2025 Table 7, July 2025 Table 4, July 2026 Table 6)
        ↓ [OBSERVED]
Canonical Source Tables & Field Extraction
        ↓ [RULE-DERIVED]
Project Identity Resolution (Deterministic ID Matching & Conflict Auditing)
        ↓ [RULE-DERIVED]
Longitudinal Snapshot Panel (4,161 Total Project Snapshots)
        ↓ [OBSERVED / PIT-DERIVED]
Point-in-Time Feature Dataset (N=437 Physical Projects; Cutoff: July 31, 2025)
        ↓ [MODEL-DERIVED]
Predictive Random Forest Models (Cost Overrun >5% & Schedule Slippage >=3M)
        ↓ [MODEL-DERIVED]
Risk Probabilities (Cost Risk Probability P_c, Schedule Risk Probability P_s)
        ↓ [RULE-DERIVED]
Portfolio Ranking (Attention Score max(P_c, P_s), Min-Rank Ties, Quantile Tiers 1-4)
        ↓ [MODEL-DERIVED]
Explainable Drivers (Top 3 Marginal Reference Perturbation Signals Δ)
        ↓ [OBSERVED]
Source Evidence (Direct MoSPI Snapshot Groundings & Observed Figures)
        ↓ [RULE-DERIVED]
Intervention Prioritisation (Controlled 7-Action Taxonomy & Governance Safeguards)
        ↓ [PRESENTATION-DERIVED]
Backend REST Services (7 Standard OpenAPI Endpoints)
        ↓ [PRESENTATION-DERIVED]
Frontend Client Applications (5 Responsive React/Tailwind Dashboards & Components)
```

---

# 8. Data Architecture

The PAIMANA data architecture operates on frozen, cryptographically verified canonical tables:

### 8.1 Authoritative Source Snapshots
1. **June 2025 Table 7** (`data/processed/table7_june_2025_projects.csv`): 1,595 projects extracted from MoSPI Flash Report Table 7. SHA-256: `9cc4e30c4d06eaa0403a3f88e212ebca6c227dd5c3a438db6fb3771e4c61eb43`.
2. **July 2025 Table 4** (`data/processed/table4_july_2025_projects.csv`): 740 central projects with expenditure and progress details. SHA-256: `ed2253c43c3baf16d4ef02d5b6ca03ae6c56d6332655de86fb009ee1cce243c3`.
3. **July 2026 Table 6** (`data/processed/table6_july_2026_projects.csv`): 1,826 central projects providing retrospective outcome verification. SHA-256: `6d0ec47f89e91cb84ad269f692d76a71b97a811a85e7067e08c6c6bf56738ac9`.

### 8.2 Identity Resolution & Longitudinal Panel
* **Project Identity Map** (`data/processed/project_identity_map.csv`): Links project records across observation dates using deterministic identity resolution rules. SHA-256: `16b25040421d4c528a91a2460b82e8f0520c9edbfc282835f42c0a3908c4c9bb`.
* **Snapshot Panel** (`data/processed/project_snapshot_panel.csv`): 4,161 total observations tracking project trajectories. SHA-256: `9f614585fa04bb064a1803fceed38a0b493766eff9e82d016008d9cab2e94f47`.
* **Core Identity Resolution Principles**:
  - **No blind fuzzy matching**: Name-based fuzzy matches without structural confirmation are rejected.
  - **No synthetic identities**: Unmatched projects retain their distinct identity rather than being forcibly merged.
  - **No forced multi-to-one collapses**: Projects with conflicting agencies or states remain separate canonical entities.

### 8.3 The Primary Longitudinal PIT Cohort ($N=437$)
The production-frozen modeling cohort consists of exactly **437 central physical infrastructure projects** observed at the July 31, 2025 cutoff and tracked forward to July 2026:
* **PIT Feature Dataset Path**: `data/interim/pit_features_july2025_to_july2026.csv`.
* **Cryptographic Hash (SHA-256)**: `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329`.
* **Total Cohort**: 437 projects.
* **Cost-Eligible Cohort**: 437 projects (100% evaluated for cost overrun).
* **Schedule-Eligible Cohort**: 305 projects (complete baseline milestone reporting).
* **Schedule-Unobserved Cohort**: 132 projects (missing baseline schedule milestones; strictly marked as `PARTIAL` coverage).

---

# 9. Point-in-Time Methodology

The PIT design guarantees that predictive models never access target data or post-cutoff information during training or evaluation:

* **Observation Cutoff Date**: **July 31, 2025**. All feature attributes are constructed strictly from data reported up to this calendar cutoff.
* **Prediction Horizon**: **12 Months Forward** (Cutoff July 31, 2025 $\longrightarrow$ Evaluation Date July 31, 2026).
* **Leakage Prevention**: All features (cost ratios, progress indicators, age, remaining duration) are strictly computed as of July 2025. No July 2026 data is permitted in the feature space.
* **Target Construction**:
  1. **Cost Overrun Target (`cost_overrun_5pct_2026`)**:
     $$Y_{\text{cost}} = \mathbb{I}\left(\frac{\text{Revised Cost}_{2026} - \text{Original Cost}_{2025}}{\text{Original Cost}_{2025}} > 0.05\right)$$
     In the 437-project cohort: 132 positive (30.21% event rate), 305 negative.
  2. **Schedule Slippage Target (`time_overrun_3m_2026`)**:
     $$Y_{\text{schedule}} = \mathbb{I}\left(\text{Anticipated Completion Date}_{2026} - \text{Original Completion Date}_{2025} \ge 3 \text{ months}\right)$$
     In the 305-project schedule cohort: 257 positive (84.26% event rate), 48 negative.
  3. **Missing Outcome Handling**: 132 projects lacking valid July 2026 completion dates are assigned `target_time_overrun_3m_july2026 = NaN` and `is_eligible_schedule_target = 0`. They are strictly excluded from schedule model fitting and evaluation.

---

# 10. Feature Architecture

The PAIMANA model operates strictly on the authorized **Enhanced Feature Set** (10 numeric features + 2 categorical features).

### 10.1 Numeric Predictors ($N=10$)
1. `feat_log_original_cost`: Natural logarithm of sanctioned cost $\ln(\text{original\_cost\_crore})$. Captures project scale non-linearly.
2. `feat_original_cost_crore`: Sanctioned baseline budget in ₹ Crores.
3. `feat_cumulative_expenditure_crore`: Total financial outlay disbursed through July 2025 in ₹ Crores.
4. `feat_expenditure_to_original_cost_ratio`: Financial outlay burn ratio: $\text{cumulative\_expenditure} / \text{original\_cost}$.
5. `feat_physical_progress_pct`: Reported cumulative physical completion percentage ($[0.0, 100.0]$).
6. `feat_physical_vs_financial_divergence`: Divergence index: $(\text{expenditure\_ratio}) - (\text{physical\_progress\_pct} / 100.0)$. Positive values indicate expenditure significantly outpacing ground execution.
7. `feat_project_age_months`: Elapsed duration in months from sanction date to July 2025.
8. `feat_is_missing_approval_date`: Binary flag ($1$ if sanction date is missing, $0$ otherwise).
9. `feat_remaining_original_duration_months`: Months between July 2025 and original completion date (negative if project is overdue).
10. `feat_is_past_original_completion`: Binary indicator ($1$ if July 2025 date is past original completion date).

### 10.2 Categorical Predictors ($N=2$)
1. `feat_state`: Project geographic jurisdiction or multi-state corridor.
2. `feat_agency`: Executing Central Public Sector Enterprise (CPSE) or department.

> [!IMPORTANT]
> **Sector Exclusion**: As established in the Module 3 Phase 5A protocol correction, **Sector is strictly excluded** from the predictive feature set. Sector classifications in MoSPI reporting introduce structural collinearity and historical reporting biases; only `feat_state` and `feat_agency` are permitted as categorical inputs.

---

# 11. ML Architecture

PAIMANA evaluates three model paradigms under a leak-safe, reproducible scikit-learn pipeline:

### 11.1 Baselines
* **Majority-Class Baseline**: Predicts the empirical majority class of the training split ($0$ for cost overrun, $1$ for schedule slippage). Serves as the fundamental non-informative baseline.

### 11.2 Linear Benchmark: Logistic Regression
* **Pipeline Configuration**:
  - `ColumnTransformer` with `SimpleImputer(strategy='median')` for numeric columns.
  - `SimpleImputer(strategy='most_frequent')` and `OneHotEncoder(handle_unknown='ignore')` for categorical columns.
  - `StandardScaler(with_mean=False)` to preserve one-hot sparsity.
  - Model: `LogisticRegression(max_iter=2000, random_state=42, class_weight=None)`.
  - All preprocessing parameters fitted strictly on the training partition.

### 11.3 Preferred Prototype Architecture: Random Forest
* **Pipeline Configuration**:
  - Exact same leak-safe `ColumnTransformer` preprocessing as Logistic Regression.
  - Model: `RandomForestClassifier(n_estimators=300, max_depth=None, min_samples_split=2, min_samples_leaf=1, max_features='sqrt', bootstrap=True, class_weight=None, random_state=42, n_jobs=1)`.
* **Rationale for Random Forest Selection**:
  In controlled retrospective evaluations, Random Forest captured non-linear interactions (particularly between project scale, divergence, and age) that linear models could not represent. It delivered superior discrimination (ROC-AUC 0.8783 for Cost Overrun, 0.9000 for Schedule Slippage) and higher precision-recall performance without requiring synthetic sampling or class re-weighting.

---

# 12. Model Evaluation

All models were evaluated under a rigorous, deterministic protocol:
* **Protocol**: Retrospective 12-month holdout evaluation.
* **Partitioning**: Deterministic 80/20 stratified split (`random_state=42`, `stratify=y`).
* **Cost Cohort**: $N = 437$ (Train $N=349$, Test $N=88$).
* **Schedule Cohort**: $N = 305$ (Train $N=244$, Test $N=61$).
* **Core Evaluation Metrics**: ROC-AUC, PR-AUC, Brier Score, Balanced Accuracy, Precision, Recall, F1 Score.

### Validated Holdout Results (Phase 5 Random Forest Benchmark)
In this retrospective 12-month holdout experiment:
* **Cost Overrun (>5%)**:
  - Random Forest Test ROC-AUC: **0.8783** (vs Logistic Regression 0.8257, vs Majority Baseline 0.5000)
  - Random Forest Test PR-AUC: **0.8243** (vs Logistic Regression 0.7615, vs Majority Baseline 0.3068)
  - Random Forest Test Brier Score: **0.1232** (vs Logistic Regression 0.1536)
* **Schedule Slippage (>=3 months)**:
  - Random Forest Test ROC-AUC: **0.9000** (vs Logistic Regression 0.8843, vs Majority Baseline 0.5000)
  - Random Forest Test PR-AUC: **0.9806** (vs Logistic Regression 0.9768, vs Majority Baseline 0.8361)
  - Random Forest Test Brier Score: **0.0958** (vs Logistic Regression 0.1101)

*(Note: These empirical results reflect performance on the retrospective 2025–2026 holdout partition; they do not imply guaranteed future nationwide prediction accuracy).*

---

# 13. CUF vs Enhanced Evaluation

Module 3 Phase 4 conducted a controlled feature ablation to determine whether the domain-engineered Point-in-Time features (Enhanced) deliver measurable improvement over conventional Core fields (CUF):

* **CUF (Core Utility Features)**: Sanctioned cost, cumulative expenditure, physical progress percentage, state, agency ($N=5$ features).
* **Enhanced Features**: CUF variables augmented with logarithmic cost scale, expenditure burn ratio, physical-vs-financial divergence index, project age, approval missingness flag, remaining duration, and past-completion flag ($N=12$ features).
* **Controlled Conditions**: Evaluated under identical Logistic Regression baseline, identical 80/20 stratified split, and identical median/one-hot preprocessing.

### Observed Predictive Gains
* **Cost Overrun Forecasting**:
  - ROC-AUC increased from **0.7590** (CUF) to **0.8257** (Enhanced): **+0.0668 (+8.8% gain)**.
  - PR-AUC increased from **0.5945** (CUF) to **0.7615** (Enhanced): **+0.1670 (+28.1% gain)**.
  - Brier Score improved from **0.1903** to **0.1536**.
* **Schedule Slippage Forecasting**:
  - ROC-AUC increased from **0.6824** (CUF) to **0.8843** (Enhanced): **+0.2020 (+29.6% gain)**.
  - PR-AUC increased from **0.9193** (CUF) to **0.9768** (Enhanced): **+0.0575 (+6.3% gain)**.
  - Brier Score improved from **0.1404** to **0.1101**.

*Conclusion*: Domain-engineered features capture critical structural warning signs—most notably expenditure outpacing physical milestones—providing measurable prospective value within the evaluated cohort.

---

# 14. Risk Scoring

The Phase 4 scoring engine computes individual hazard probabilities and synthesizes them into portfolio-level risk metrics:

* **Risk Scores Dataset Path**: `data/processed/project_risk_scores.csv`.
* **Cryptographic Hash (SHA-256)**: `6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d`.
* **Prediction Partitions Metadata**: `data/processed/project_risk_score_partitions.csv` explicitly tracks the evaluation status of each project score: `MODELFIT` (in-sample prototype scoring), `CALIBRATION_HOLDOUT` (held out during model fitting), or `TEST_HOLDOUT` (validated out-of-sample holdout).

### 14.1 Cost Risk Probability ($P_c$)
$$P_c = P(\text{Cost Overrun} > 5\% \mid X_{\text{PIT}}) \in [0.0, 1.0]$$
Scored for all 437 projects in the primary cohort. Of these, 261 are prototype in-sample catalog scores (`MODELFIT`), 88 are calibration holdout scores, and 88 are validated out-of-sample holdout predictions (`TEST_HOLDOUT`).

### 14.2 Schedule Risk Probability ($P_s$)
$$P_s = P(\text{Schedule Slippage} \ge 3\text{M} \mid X_{\text{PIT}}) \in [0.0, 1.0]$$
Scored for the 305 schedule-eligible projects (183 `MODELFIT` in-sample, 61 `CALIBRATION_HOLDOUT`, and 61 `TEST_HOLDOUT` validated out-of-sample holdout). For the 132 schedule-ineligible projects, $P_s$ is strictly `NULL` (`NOT_ELIGIBLE`).

### 14.3 Attention Score
$$\text{attention\_score} = \begin{cases} \max(P_c, P_s) & \text{if } \text{risk\_coverage} = \text{FULL} \\ P_c & \text{if } \text{risk\_coverage} = \text{PARTIAL} \end{cases}$$
Acts as a multi-hazard sentinel: an asset exhibiting critical distress in *either* cost or schedule is elevated for supervisory monitoring. **$\text{attention\_score} = \max(P_c, P_s)$ is a comparative portfolio prioritization index, not a calibrated probability of joint failure.**

### 14.4 Compound Exposure
$$\text{compound\_exposure} = \begin{cases} \min(P_c, P_s) & \text{if } \text{risk\_coverage} = \text{FULL} \\ \text{NULL} & \text{if } \text{risk\_coverage} = \text{PARTIAL} \end{cases}$$

> [!WARNING]
> **Compound Exposure Semantic Invariant**: Compound exposure measures co-occurring risk severity across both dimensions. **It is strictly NOT a joint mathematical probability** $P(\text{Cost} \cap \text{Schedule})$. In uncalibrated models, $\min(P_c, P_s)$ is a heuristic sentinel of dual-hazard vulnerability, not the joint distribution of independent events.

---

# 15. Risk Ranking

### 15.1 Portfolio Ranking
* **Method**: Standard Competition Ranking (`rank(method='min', ascending=False)`) descending by `attention_score`.
* **Tie Handling**: Tied scores receive identical ranks; subsequent ranks skip accordingly (resulting in ranks 1 through 419 across 437 projects).

### 15.2 Empirical Quantile Attention Tiers
Projects are categorized into four operational attention tiers based strictly on empirical quantile cutoffs:
* **Tier 1** ($\ge Q90 = 0.994667$): Top 10% highest attention scores (**$N=44$**).
* **Tier 2** ($\ge Q75 = 0.983333 \text{ and } < Q90$): 75th to 90th percentile (**$N=73$**).
* **Tier 3** ($\ge Q50 = 0.906667 \text{ and } < Q75$): 50th to 75th percentile (**$N=102$**).
* **Tier 4** ($< Q50$): Lower 50% attention scores (**$N=218$**).

> [!CAUTION]
> **Prohibited Tier Terminology**: Tiers 1 through 4 MUST NEVER be described as "Critical Risk", "High Risk", "Medium Risk", or "Low Risk". They represent relative supervisory prioritization within this specific monitored cohort, not absolute probabilistic severity.

### 15.3 Partial Coverage Ranking Caveat
Because `attention_score` for `PARTIAL` coverage projects defaults to $P_c$ alone (as schedule risk is unobserved), an asset with severe unrecorded schedule distress could theoretically fall into a lower attention tier. **User interfaces must prominently display coverage status alongside attention tier.**

---

# 16. Explainability

PAIMANA implements a two-level explainability framework to unpack why an asset received its model-derived risk score:

* **Risk Explanations Dataset Path**: `data/interim/project_risk_explanations.csv`.
* **Cryptographic Hash (SHA-256)**: `5b73c881fdc3b25d757d04c8edbb4d0eb62e5e0455813f9bd8c65ae168e244d2`.

### 16.1 Global Explainability
* **Method**: Mean Decrease in Impurity (MDI) feature importance extracted from the trained Random Forest models.
* **Aggregation**: One-hot encoded categorical indicator importances are summed back to their parent features (`feat_state`, `feat_agency`).

### 16.2 Local Explainability: Marginal Reference Perturbation
* **Method**: For each individual project and each task, feature sensitivity is quantified by computing the change in predicted probability when the feature is replaced by its cohort baseline reference value:
  $$\Delta = P(X_{\text{actual}}) - P(X_{\text{actual}} \text{ with } X_j = X_{j, \text{ref}})$$
* **Reference Values**:
  - Numeric features: Training cohort **median**.
  - Categorical features: Training cohort **mode** (most frequent class).
* **Directional Attribution**:
  - $\Delta > 0$: `INCREASES_RISK` (observed value elevates predicted probability).
  - $\Delta < 0$: `DECREASES_RISK` (observed value attenuates predicted probability).
  - $\Delta = 0$: `NEUTRAL`.

### 16.3 Non-Causal Semantic Boundary
Every local explanation pairs the top 3 features with observed MoSPI source facts (e.g. *"Expenditure ratio (21.05) exceeds physical progress (58.00%) by 20.47 divergence index"*). Explanations describe statistical associations in historical data, never causal roots or contractor culpability.

---

# 17. Intervention Prioritisation

The intervention engine translates predictive risk scores, explainable drivers, and data quality indicators into structured operational monitoring actions:

* **Intervention Priorities Dataset Path**: `data/processed/project_intervention_priorities.csv`.
* **Cryptographic Hash (SHA-256)**: `3dfacd2805610e0a1a9ff3f10461c97322a3bf62ca1dc348fc6baca13e012ec5`.

### 17.1 Controlled Action Taxonomy (7 Protocols)
1. **`DATA_QUALITY_REVIEW`** ($N=128$ primary): Audit and reconcile missing baseline milestone dates, approval documents, and completion estimates.
2. **`JOINT_COST_SCHEDULE_REVIEW`** ($N=90$ primary): Convene joint review committee to address concurrent cost overrun and schedule slippage distress.
3. **`SCHEDULE_REVIEW`** ($N=81$ primary): Review critical path execution milestones and contractor deployment schedules.
4. **`COMPLETION_STATUS_REVIEW`** ($N=79$ primary): Re-baseline completion schedules for projects operating past their original target completion dates.
5. **`COST_REVIEW`** ($N=29$ primary): Conduct focused expenditure audits on projects exhibiting high financial outlay escalation.
6. **`PROGRESS_VERIFICATION`** ($N=24$ primary, $N=231$ secondary): Conduct physical site inspections to verify completed works against reported expenditures.
7. **`EXPENDITURE_PROGRESS_REVIEW`** ($N=6$ primary, $N=24$ secondary): Investigate severe divergence between recorded financial outlays and reported physical progress.

### 17.2 Intervention Priority Mapping
* `PRIORITY_1` ($N=44$): Tier 1 assets requiring executive review within 14 business days.
* `PRIORITY_2` ($N=73$): Tier 2 assets requiring monthly committee monitoring.
* `PRIORITY_3` ($N=102$): Tier 3 assets requiring quarterly milestone tracking.
* `PRIORITY_4` ($N=218$): Tier 4 assets requiring standard reporting cadence.

### 17.3 Non-Punitive Governance
Intervention recommendations are strictly supervisory advisory actions. The platform enforces a hard prohibition against automated administrative sanctions, automated budget cuts, contract cancellations, or agency penalties.

---

# 18. Partial Coverage

A critical failure mode of naive surveillance systems is treating missing records as "safe" or "zero risk." PAIMANA enforces strict uncertainty semantics:

* **Unobserved Schedule Outcomes**: Exactly 132 projects in the July 2025 cohort lack baseline milestone completion dates in canonical MoSPI tables.
* **Strict NULL Representation**:
  - `schedule_risk_probability`: Strictly `NULL` / `NaN` / `None`.
  - `compound_exposure`: Strictly `NULL` / `NaN` / `None`.
  - `data_quality_flag`: `SCHEDULE_OUTCOME_UNOBSERVED`.
* **Prohibited Imputations**: Backend APIs, databases, and frontend clients MUST NEVER convert `NULL` schedule probabilities to $0.0$, $-1$, or "Low Risk".
* **Frontend Rendering Requirement**: UIs must display an amber `PARTIAL COVERAGE` badge and explicitly state: **"Schedule outcome unavailable (Baseline milestone dates unobserved)"**.

---

# 19. Product Requirements

* **FR-01: Portfolio Overview Dashboard**: Render aggregate portfolio KPI cards (total projects, tier counts, coverage breakdown) and distribution charts.
* **FR-02: Multi-Hazard Risk Ranking**: Display interactive leaderboard sorting projects by `portfolio_rank` and `attention_score`.
* **FR-03: Project Detail Profile**: Render complete project profile including baseline cost, cumulative spend, physical progress, and risk breakdown.
* **FR-04: Multi-Hazard Probability Display**: Display independent $P_c$ and $P_s$ probabilities with formatting to one decimal place (e.g. `99.7%`).
* **FR-05: Explainable Risk Drivers**: Display top 3 statistical drivers for Cost and Schedule with magnitude bars and directional badges.
* **FR-06: Verifiable Evidence Grounding**: Pair every driver and intervention recommendation with an observed source fact from MoSPI reporting.
* **FR-07: Evidence-Grounded Interventions**: Display primary/secondary actions, priority level, and protocol checklist.
* **FR-08: Coverage & Data Quality Visibility**: Distinctly badge `FULL` vs `PARTIAL` coverage and display missing baseline flags.
* **FR-09: Filtering & Search**: Enable multi-attribute filtering by State, Agency, Attention Tier, Risk Focus, and Coverage status, alongside text search.
* **FR-10: Persistent Governance Disclaimers**: Affix non-causal and non-punitive advisory notices to all analytical cards and export reports.

---

# 20. Frontend Requirements

As defined in the Phase 8 engineering handoff, the frontend consists of 5 responsive screens:

1. **Portfolio Overview Dashboard**: Header metrics (437 Total, 44 Tier 1, 305 Full, 132 Partial), Attention Score histogram, Action distribution donut chart, Agency bar chart.
2. **Risk Ranking Leaderboard**: Tabular view with columns (Rank, Project Name, Agency, State, Coverage Badge, Cost Risk %, Schedule Risk %, Attention Score, Tier Badge, Action Badge).
3. **Project Detail Profile**: Header metadata, side-by-side Cost Risk Card, Schedule Risk Card (with partial coverage warning banner when unobserved), and Compound Exposure Card.
4. **Explainable Risk Drivers Panel**: Two tabs (Cost Drivers vs Schedule Drivers), rank 1–3 feature cards, impact bars, observed fact callouts, and non-causal disclaimer.
5. **Intervention Action Panel**: Priority badge, primary and secondary action protocol checklists, evidence grounding card, and official MoSPI advisory notice.

---

# 21. Backend Requirements

FastAPI services exposing standard RESTful JSON interfaces:

```text
GET /projects                                 -> Paginated project catalog with tier/coverage filters
GET /projects/{canonical_project_key}         -> Comprehensive single-project unified profile
GET /projects/ranking                         -> Ranked leaderboard ordered strictly by portfolio_rank
GET /projects/{canonical_project_key}/risk    -> Multi-hazard probabilities, attention score, coverage
GET /projects/{canonical_project_key}/drivers -> Top 3 explainable drivers and MoSPI source facts
GET /projects/{canonical_project_key}/interventions -> Recommended monitoring actions and evidence
GET /portfolio/summary                        -> Executive portfolio aggregates and distributions
```

---

# 22. Database Requirements

PostgreSQL schema enforcing relational integrity with `canonical_project_key` as foreign key:

1. **`projects`**: Baseline project identity, cost, expenditure, progress, and divergence metadata ($N=437$).
2. **`project_risk_scores`**: Probabilities $P_c, P_s$, coverage status, attention score, compound exposure, tier, rank ($N=437$).
3. **`project_risk_explanations`**: Task-level top 3 features, values, impacts, directions, source facts ($N=874$).
4. **`project_intervention_priorities`**: Priority level, primary/secondary action, risk focus, evidence feature, data quality flags ($N=437$).

---

# 23. Non-Functional Requirements

* **NFR-01: Reproducibility**: Execution of the data pipeline from raw source tables must deterministically produce identical SHA-256 hashes.
* **NFR-02: Cryptographic Lineage Integrity**: All upstream and downstream CSV artifacts must match frozen checksums.
* **NFR-03: Auditability**: Every generated score must record its model name, variant, and `scoring_method_version`.
* **NFR-04: Graceful Null Handling**: Unobserved schedule targets must propagate cleanly as JSON `null` without throwing runtime exceptions.
* **NFR-05: High Performance**: API endpoints must respond in $< 100$ ms for single-project lookups and $< 250$ ms for paginated portfolio queries.
* **NFR-06: Comprehensive Testability**: Maintain 100% test coverage across data schemas, scoring formulas, explainability bounds, and API contracts.

---

# 24. Governance & Safety

### 24.1 Strictly Prohibited System Behaviors
* **No Causal Claims**: Model probabilities must never be presented as legal or operational root causes.
* **No Agency or State Blaming**: Feature attributions must never be used to declare CPSEs or state governments "corrupt" or "incompetent."
* **No Engineering Certification**: The system must never certify construction quality or physical integrity.
* **No Autonomous Sanctions**: Automated administrative sanctions, budget reductions, contractual penalties, blacklisting, or tender cancellations are strictly forbidden.
* **No Guaranteed Outcomes**: Claims of "100% certainty" or "infallible predictions" are barred.

### 24.2 Mandatory Governance Requirements
* **Evidence Grounding**: Every high-attention alert must display verifiable point-in-time MoSPI facts.
* **Uncertainty Disclosure**: Partial coverage assets must prominently display unobserved data warnings.
* **Human Oversight Notice**: All intervention recommendations must state:  
  *“Advisory decision support for supervisory review. Automated administrative sanctions are strictly prohibited.”*

---

# 25. Success Metrics

### 25.1 Model Performance Metrics (Validated on Retrospective 12-Month Holdout)
* **Cost Overrun (>5%)**: Random Forest ROC-AUC $\ge 0.70$ (Achieved: **0.8783**), PR-AUC $\ge 0.50$ (Achieved: **0.8243**), Brier Score $\le 0.20$ (Achieved: **0.1232**).
* **Schedule Slippage (>=3M)**: Random Forest ROC-AUC $\ge 0.80$ (Achieved: **0.9000**), PR-AUC $\ge 0.90$ (Achieved: **0.9806**), Brier Score $\le 0.12$ (Achieved: **0.0958**).

### 25.2 Product Operational Metrics
* **Coverage Accounting**: Exactly 100% of primary cohort assets ($N=437$) scored for Cost; exactly 100% of schedule-eligible assets ($N=305$) scored for Schedule.
* **Data Quality Visibility**: Exactly 100% of missing schedule baseline assets ($N=132$) surfaced with explicit unobserved flags.
* **Explainability Completeness**: Exactly 100% of projects ($N=437$) supplied with top 3 risk drivers and source facts for both tasks ($N=874$ records).
* **Actionable Prioritisation**: Exactly 100% of projects ($N=437$) mapped to controlled monitoring protocols.

---

# 26. Team Responsibility Matrix

| Workstream | Primary Owner | Key Deliverables & Responsibilities |
| :--- | :--- | :--- |
| **Data & AI Lead** | Data/AI Team | Canonical snapshot ingestion, identity resolution, PIT feature extraction, model benchmarking, probability calibration, risk scoring, explainability, and intervention logic. |
| **Backend Engineering** | Backend Team | Provisioning FastAPI REST services, implementing the 7 endpoint contracts, error handling, pagination, and OpenAPI documentation. |
| **Database Administration** | Database Team | Provisioning PostgreSQL 15+ relational schema, defining tables, foreign keys, indexes, and ETL seeding from frozen CSVs. |
| **Frontend UI/UX** | Frontend Team | Building the 5 core React 18 / Vite components, implementing responsive Tailwind layouts, coverage badge states, and null rendering. |
| **Integration & QA** | Joint Engineering | End-to-end integration testing, schema contract validation, and full automated test suite execution. |
| **Product & Pitch** | Executive Team | Hackathon pitch deck, live interactive demo execution, technical storytelling, and safe claims governance. |

---

# 27. Implementation Boundaries

* **DONE (Completed & Frozen)**:
  - Modules 1 through 4: Canonical data ingestion, project identity resolution, longitudinal panel, PIT feature construction, model training and benchmarking, probability calibration evaluation, risk scoring engine, quality audit, explainability engine, intervention prioritisation, product contract, and handoff specifications.
* **NEXT (Module 5 Application Phase)**:
  - Database schema provisioning, FastAPI backend service implementation, React frontend dashboard construction, and API integration testing.
* **FUTURE (Post-Hackathon / Production Roadmaps)**:
  - Multi-year continuous snapshot ingestion, automated monthly data pipelines, production Platt calibration on expanded holdouts, external state-level validation, and real-time CPSE webhooks.

---

# 28. Demo Flow

1. **Open Portfolio Overview**: Display national summary KPI cards (437 projects, 44 Tier 1 priority assets, 305 Full Coverage, 132 Partial Coverage).
2. **Review Attention Distribution**: Showcase the multi-hazard attention histogram and agency distress concentrations.
3. **Open Risk Ranking Leaderboard**: Present the ranked project catalog; demonstrate multi-attribute filtering by State, Agency, and Attention Tier.
4. **Select High-Priority Asset**: Drill into Rank #1 project (e.g. `proj_16723_02b9f3d9` — West Central Railway).
5. **Inspect Risk Profile**: Highlight $P_c = 99.8\%$, $P_s = 97.0\%$, and `compound_exposure = 0.9700`.
6. **Examine Explainable Drivers**: Open Driver Panel to display how `feat_physical_vs_financial_divergence` (+20.47) and `feat_expenditure_to_original_cost_ratio` elevate attention.
7. **Verify Observed Source Facts**: Review the underlying MoSPI figures proving expenditure outlays outpaced physical execution.
8. **Inspect Recommended Intervention**: View the assigned `JOINT_COST_SCHEDULE_REVIEW` and `PROGRESS_VERIFICATION` protocol checklists.
9. **Demonstrate Partial Coverage Handling**: Select an asset with missing baseline schedule data; demonstrate the amber `PARTIAL COVERAGE` badge, `NULL` schedule probability, and `DATA_QUALITY_REVIEW` assignment.
10. **Conclude with Governance**: Highlight the official MoSPI advisory disclaimer forbidding automated budget cuts or penalties.

---

# 29. Pitch Technical Story

* **The Problem**: Public infrastructure monitoring today tells decision-makers *what already happened*—logging historical cost overruns and accrued delays after capital has already been spent.
* **The Gap**: Descriptive project dashboards overwhelm administrators with thousands of data rows without indicating *where failure will occur next*.
* **The Solution**: PAIMANA Predictive Risk Intelligence—an early-warning surveillance engine that converts descriptive reporting into prospective foresight.
* **The Intelligence**: Point-in-Time machine learning models trained on retrospective longitudinal snapshots, delivering calibrated multi-hazard risk probabilities.
* **The Trust**: Two-level explainability combining global feature importance with local marginal perturbations, grounded in verifiable MoSPI snapshot facts.
* **The Action**: Evidence-grounded intervention prioritisation mapping statistical vulnerabilities into concrete, non-punitive supervisory inspection protocols.
* **The Differentiation**: Mathematically rigorous PIT isolation, empirical CUF-vs-Enhanced validation, and explicit partial coverage handling that refuses to disguise missing data as zero risk.

---

# 30. Limitations

This section explicitly documents known operational and methodological limitations:
1. **Retrospective Holdout Scope**: Model performance is established on a retrospective 12-month holdout (2025 $\to$ 2026); prospective nationwide deployment requires continuous longitudinal validation.
2. **Cohort Size**: The current primary longitudinal cohort contains 437 central projects; expanded ingestion of historic PDF reports will broaden sample depth.
3. **Identity Resolution Ambiguities**: Projects lacking unique identifiers or exhibiting conflicting metadata are kept unmerged, resulting in conservative coverage.
4. **Schedule Outcome Missingness**: 132 projects lack baseline milestone dates, restricting schedule prediction to 305 assets.
5. **Random Forest Probability Concentration**: Raw Random Forest probabilities exhibit peak concentrations near 0 and 1, functioning as an operational priority ranking rather than perfectly smooth linear odds.
6. **No External Regional Validation**: Models have not yet been evaluated on municipal or state-level public works datasets.
7. **No Causal Determinism**: Predictions represent empirical statistical associations, not engineering or management root causes.
8. **No Autonomous Authority**: Recommendations are strictly supervisory aids; human engineering review is always mandatory.
9. **Data Completeness Dependency**: Prediction quality depends directly on the timeliness and veracity of monthly CPSE reporting to MoSPI.
10. **Prototype Catalog Partition Composition**: The prototype risk catalog scores all 437 projects using a model trained on ~60% of the cohort (modelfit partition); predictions for the training subset are in-sample, while 20% are validated out-of-sample holdout predictions and 20% are calibration holdout. Per-row partition status is explicitly tracked in `data/processed/project_risk_score_partitions.csv`.

---

# 31. Future Roadmap

*(Clearly labeled as future, post-hackathon initiatives)*:
* **Roadmap Phase 1: Expanded Historical Ingestion**: Ingest historic MoSPI monthly reports from 2020–2024 to create a multi-year panel dataset.
* **Roadmap Phase 2: Production Probability Calibration**: Train isotonic and beta calibration models on larger multi-year longitudinal validation sets.
* **Roadmap Phase 3: Live CPSE Portal Ingestion**: Build automated ingestion connectors to pull monthly progress directly from CPSE enterprise systems.
* **Roadmap Phase 4: Concept Drift & Retraining Pipeline**: Implement automated statistical drift monitoring to schedule periodic model retraining.
* **Roadmap Phase 5: State Infrastructure Ingestion**: Adapt the feature engineering pipeline to monitor state-funded capital infrastructure projects.

---

# 32. Traceability Matrix

| Requirement / Claim | PRD Section | Authoritative Existing Artifact | Verified Test / Evidence | Implementation Status |
| :--- | :---: | :--- | :--- | :---: |
| **SIH26103 Compliance** | Section 3 | Problem Statement SIH26103 Specification | All 7 requirements mapped to functional code | **VERIFIED** |
| **Point-in-Time Dataset** | Section 8, 9 | `data/interim/pit_features_july2025_to_july2026.csv` | SHA-256: `052def4381273ba1538d08080ddafb14d71c2527af3bba4e12a91aaa703ef329`, $N=437$, 26 columns | **VERIFIED** |
| **Enhanced Feature Set** | Section 10 | `reports/module2c_pit_dataset_validation.md` | 10 numeric, 2 categorical (state, agency) | **VERIFIED** |
| **Sector Exclusion** | Section 10 | `reports/module3_random_forest_benchmark_results.md` | Sector strictly excluded from predictors | **VERIFIED** |
| **CUF vs Enhanced Gain** | Section 13 | `reports/module3_cuf_vs_enhanced_results.md` | Cost ROC-AUC +0.0668; Schedule ROC-AUC +0.2020 | **VERIFIED** |
| **RF Candidate Selection**| Section 11, 12| `reports/module3_random_forest_benchmark_results.md` | Cost ROC-AUC 0.8783; Schedule ROC-AUC 0.9000 | **VERIFIED** |
| **Probability Calibration**| Section 11, 14| `reports/module3_probability_calibration_validation.md`| Raw RF selected for prototype risk scoring | **VERIFIED** |
| **Multi-Hazard Scoring** | Section 14 | `data/processed/project_risk_scores.csv` | SHA-256: `6fac347429377e6b5535e4e52d6a7fbeb5a0f0bda0c685237c8b920b7397fc1d`, $N=437$, 21 columns | **VERIFIED** |
| **Quantile Attention Tiers**| Section 15 | `reports/module4_risk_scoring_schema.md` | Tier 1: 44, Tier 2: 73, Tier 3: 102, Tier 4: 218 | **VERIFIED** |
| **Partial Coverage Semantics**| Section 18 | `reports/module4_product_contract.md` | 132 projects strictly NULL schedule probability | **VERIFIED** |
| **Compound Exposure Bound**| Section 14 | `reports/module4_product_contract.md` | $\min(P_c, P_s)$, strictly non-joint probability | **VERIFIED** |
| **Explainability Engine** | Section 16 | `data/interim/project_risk_explanations.csv` | SHA-256: `5b73c881fdc3b25d757d04c8edbb4d0eb62e5e0455813f9bd8c65ae168e244d2`, $N=874$, 29 columns | **VERIFIED** |
| **Intervention Priorities** | Section 17 | `data/processed/project_intervention_priorities.csv`| SHA-256: `3dfacd2805610e0a1a9ff3f10461c97322a3bf62ca1dc348fc6baca13e012ec5`, $N=437$, 16 columns | **VERIFIED** |
| **7 REST API Contracts** | Section 21 | `reports/module4_frontend_backend_handoff.md` | 7 endpoints defined with JSON schemas | **VERIFIED** |
| **4 Relational Entities** | Section 22 | `reports/module4_frontend_backend_handoff.md` | PostgreSQL DDL with PK/FK constraints | **VERIFIED** |
| **5 Frontend Components** | Section 20 | `reports/module4_frontend_backend_handoff.md` | 5 dashboard components specified | **VERIFIED** |
| **Non-Punitive Governance**| Section 24 | `reports/module4_product_contract.md` | Automated administrative sanctions & causal claims barred | **VERIFIED** |
| **Repository Test Suite** | Section 23 | `tests/test_*.py` | 356 / 356 unit tests passing (100%) | **VERIFIED** |

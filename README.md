# PAIMANA — Predictive Risk Intelligence

> **Smart India Hackathon 2026 · Problem Statement SIH26103**
> *Use Case on Web-Based Integrated Project Monitoring Platform*

> [!WARNING]
> This project is under **active development**. No trained models, benchmark results, or production endpoints exist yet.

---

## 1 · Project Overview

**PAIMANA Predictive Risk Intelligence** aims to move infrastructure-project monitoring from *descriptive reporting* to *predictive, explainable decision support*.

Rather than building another monitoring dashboard, the system is designed to surface **why** a project is likely to overrun — in cost or time — and **how confident** that prediction is, so that decision-makers can intervene early.

---

## 2 · Problem

India's public infrastructure projects are tracked through platforms such as the Online Computerised Monitoring System (OCMS). These systems capture Cost Utilisation Factor (CUF) variables and milestone data, providing a rich foundation for monitoring.

Existing project-monitoring data provides an opportunity to build an additional **predictive decision-support layer** that can identify potential future risks before they materialise. Specific opportunities include:

- Predicting cost and schedule overruns *before* they occur, rather than identifying them after the fact.
- Systematically ranking projects by predicted risk severity to support resource allocation.
- Surfacing the drivers behind overruns in an explainable, actionable form.
- Comparing conventional statistical indicators with ML-based approaches on the same feature set.

---

## 3 · Proposed Solution

Build a modular analytics layer that can sit alongside existing monitoring platforms and provide:

| Capability | Purpose |
|---|---|
| **Risk prediction** | Estimate the probability/risk of future cost and schedule overruns for each project. |
| **Risk ranking** | Prioritise projects by predicted risk to support resource allocation. |
| **Explainability** | Surface the top contributing factors behind each prediction (e.g., SHAP values, feature importance). |
| **Approach comparison** | Benchmark conventional/statistical methods against ML approaches on the same data. |
| **Feature comparison** | Evaluate current CUF variables against enhanced or derived predictive features. |
| **Early-warning support** | Flag projects crossing risk thresholds for timely intervention. |

---

## 4 · Core Capabilities (Planned)

- Predict potential **cost-overrun risk** per project.
- Predict potential **schedule/time-overrun risk** per project.
- Rank projects by **composite predicted risk**.
- Provide **interpretable explanations** of major risk drivers.
- Compare **statistical baselines** with **ML-based models** on identical datasets.
- Compare **standard CUF variables** with **engineered predictive features**.
- Support **early-warning alerts** and **intervention prioritisation**.

---

## 5 · High-Level Architecture (Planned)

The diagram below shows the intended system architecture. Not all components are implemented yet.

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                             │
│  Raw / Synthetic Data  →  Cleaning & Validation  →  Store   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   FEATURE ENGINEERING                       │
│  CUF Variables  ·  Derived Features  ·  Temporal Signals    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   MODELLING LAYER                           │
│  Statistical Baselines  ·  ML Models  ·  Explainability     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  PRESENTATION LAYER                         │
│  Risk Rankings  ·  Driver Explanations  ·  Early Warnings   │
└─────────────────────────────────────────────────────────────┘
```

---

## 6 · Repository Structure

```
paimana-predictive-risk/
├── data/
│   ├── raw/              # Original, unprocessed datasets
│   └── processed/        # Cleaned and transformed data
├── notebooks/            # Exploratory analysis & experiments
├── src/
│   ├── data/             # Data ingestion and preprocessing
│   ├── features/         # Feature engineering pipelines
│   ├── models/           # Model training, evaluation, comparison
│   └── evaluation/       # Metrics, explainability, reporting
├── docs/                 # Project documentation
├── tests/                # Unit and integration tests
├── .gitignore
└── README.md
```

---

## 7 · Current Development Status

| Phase | Status |
|---|---|
| Repository scaffolding | ✅ Complete |
| Initial PAIMANA data acquisition/extraction | ✅ Complete |
| May–July 2026 project-month dataset | ✅ Prepared |
| Data validation | 🔄 In progress |
| Historical data expansion | 🔄 In progress |
| Point-in-time feature design | 🔲 Planned |
| Future-outcome/label construction | 🔲 Planned |
| Statistical baseline | 🔲 Planned |
| ML baseline | 🔲 Planned |
| Advanced ML comparison | 🔲 Planned |
| Explainability | 🔲 Planned |
| Risk ranking & intervention layer | 🔲 Planned |
| Web presentation layer | 🔲 Planned |

> [!NOTE]
> The current May–July 2026 dataset is an initial project-month dataset used for data understanding and pipeline development. It is not being presented as the final training dataset. Additional historical reporting periods are being acquired to support robust point-in-time temporal modelling.

> [!NOTE]
> No models have been trained yet. No performance metrics or accuracy figures are available at this stage. All capabilities listed above describe the **intended** system design.

---

## 8 · Technology Stack

| Layer | Technologies | Status |
|---|---|---|
| Language | Python 3.10+ | Confirmed |
| Data processing | Pandas, NumPy | Confirmed |
| Visualisation | Matplotlib | Confirmed |
| ML frameworks | Scikit-learn, XGBoost / LightGBM | Tentative |
| Explainability | SHAP, feature-importance methods | Tentative |
| Web framework | Flask / Streamlit / Dash | Tentative |
| Version control | Git, GitHub | Confirmed |

> [!NOTE]
> Items marked **Tentative** may change as the project evolves. Final technology choices will be documented before the presentation phase.

---

## 9 · Roadmap

1. **Data acquisition and provenance** — Source project-monitoring data; document provenance and scope.
2. **Project-month dataset construction** — Build structured project-month observations from raw reports.
3. **Data validation and exploratory analysis** — Validate data quality; understand distributions, correlations, and baseline overrun patterns.
4. **Historical panel expansion** — Acquire additional reporting periods to enable temporal modelling.
5. **Point-in-time feature engineering** — Derive predictive features using only information available at prediction time.
6. **Future outcome/label construction** — Define and construct target variables for cost- and schedule-overrun prediction.
7. **Statistical baseline** — Implement conventional statistical approaches as a benchmark.
8. **ML baseline and model comparison** — Train and evaluate ML models; compare against statistical baselines.
9. **CUF vs enhanced-feature experiment** — Evaluate standard CUF variables against engineered predictive features.
10. **Explainability and risk-driver analysis** — Integrate interpretability methods; surface risk drivers per project.
11. **Risk ranking and intervention prioritisation** — Rank projects by composite risk; support intervention decisions.
12. **Web/API integration** — Build a presentation layer for risk rankings, explanations, and early warnings.
13. **End-to-end validation and SIH demonstration** — Full pipeline testing, documentation, and submission.

---

## 10 · Contributing

> [!IMPORTANT]
> Contribution guidelines are not yet finalised. Team members should coordinate via the project's communication channels before pushing changes.

A `CONTRIBUTING.md` with branching strategy, commit conventions, and code-review expectations will be added as the team workflow stabilises.

---

<sub>Built for Smart India Hackathon 2026 · SIH26103</sub>

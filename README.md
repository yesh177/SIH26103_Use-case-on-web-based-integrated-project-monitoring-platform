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

India's public infrastructure projects are tracked through platforms such as the Online Computerised Monitoring System (OCMS). These systems capture Cost Utilisation Factor (CUF) variables and milestone data, but monitoring remains largely **retrospective**:

- Overruns are identified *after* they occur, not predicted in advance.
- There is no systematic ranking of projects by predicted risk severity.
- The drivers behind overruns are not surfaced in an explainable, actionable form.
- Conventional statistical indicators and potential ML-based approaches have not been compared side-by-side on the same feature set.

---

## 3 · Proposed Solution

Build a modular analytics layer that can sit alongside existing monitoring platforms and provide:

| Capability | Purpose |
|---|---|
| **Risk prediction** | Estimate the probability and magnitude of cost-overrun and schedule-overrun for each project. |
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

## 5 · High-Level Architecture

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
| Problem framing & literature review | 🔄 In progress |
| Data acquisition strategy | 🔲 Planned |
| Feature engineering | 🔲 Planned |
| Baseline statistical models | 🔲 Planned |
| ML model development | 🔲 Planned |
| Explainability integration | 🔲 Planned |
| Web-based presentation layer | 🔲 Planned |

> [!NOTE]
> No models have been trained yet. No performance metrics or accuracy figures are available at this stage. All capabilities listed above describe the **intended** system design.

---

## 8 · Technology Stack

| Layer | Technologies | Status |
|---|---|---|
| Language | Python 3.10+ | Confirmed |
| Data processing | Pandas, NumPy | Confirmed |
| Visualisation | Matplotlib, Seaborn | Tentative |
| ML frameworks | Scikit-learn, XGBoost / LightGBM | Tentative |
| Explainability | SHAP, feature-importance methods | Tentative |
| Web framework | Flask / Streamlit / Dash | Tentative |
| Version control | Git, GitHub | Confirmed |

> [!NOTE]
> Items marked **Tentative** may change as the project evolves. Final technology choices will be documented before the presentation phase.

---

## 9 · Roadmap

1. **Data strategy** — Define data requirements; source or synthesise representative datasets.
2. **Exploratory analysis** — Understand variable distributions, correlations, and baseline overrun patterns.
3. **Feature engineering** — Derive predictive features beyond raw CUF variables.
4. **Baseline modelling** — Implement conventional statistical approaches for cost- and time-overrun prediction.
5. **ML modelling** — Train and evaluate ML models; compare against baselines.
6. **Explainability** — Integrate interpretability methods; surface risk drivers per project.
7. **Presentation layer** — Build a web interface for risk ranking, explanations, and early warnings.
8. **Validation & documentation** — End-to-end testing, documentation, and SIH submission.

---

## 10 · Contributing

> [!IMPORTANT]
> Contribution guidelines are not yet finalised. Team members should coordinate via the project's communication channels before pushing changes.

A `CONTRIBUTING.md` with branching strategy, commit conventions, and code-review expectations will be added as the team workflow stabilises.

---

<sub>Built for Smart India Hackathon 2026 · SIH26103</sub>

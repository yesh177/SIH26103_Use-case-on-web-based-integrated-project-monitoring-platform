# PAIMANA Target Definition & Temporal Validation Framework

> **Project:** SIH26103 — Use Case on Web-Based Integrated Project Monitoring Platform  
> **Product:** PAIMANA Predictive Risk Intelligence  
> **Document:** `docs/target_definition.md`  
> **Reference Inputs:** `PAIMANA_Data_Dictionary.xlsx.xlsx`, `reports/module1_data_validation.md`  
> **Status:** SPECIFICATION READY — HISTORICAL DATA REQUIRED BEFORE MODEL TRAINING  

---

## 1. Core Principles of Target Construction

In longitudinal project monitoring, defining an outcome target requires strict adherence to temporal sequence and causality.

$$\mathcal{Y}_i(t, \Delta) = \mathcal{G}\Big(\mathbf{z}_i(t+\Delta), \, \mathbf{z}_i(t)\Big)$$

Where:
- $t$ is the **prediction snapshot date** (cutoff for feature extraction).
- $t + \Delta$ is the **future evaluation horizon** ($\Delta \ge 1$ months).
- $\mathbf{z}_i(t)$ represents the monitoring status of project $i$ recorded at $t$.
- $\mathbf{z}_i(t+\Delta)$ represents the realized status of project $i$ recorded at $t+\Delta$.

### The Three Cardinal Distinctions
To eliminate label leakage, this specification strictly distinguishes between three concepts:

```
┌───────────────────────────────────────────────┬─────────────────────────────────────────────────────────────┐
│ Category                                      │ Definition & Mathematical Formulation                       │
├───────────────────────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 1. Current Delay / Status (Feature)           │ State of project schedule already acknowledged by time t:   │
│                                               │ Slippage(t) = max(0, revised_doc(t) - original_doc)         │
│                                               │ Status: PERMITTED AS INPUT FEATURE; NOT A PREDICTION TARGET │
├───────────────────────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 2. Future Deterioration (Primary Target)      │ Incremental delay or cost escalation occurring between      │
│                                               │ snapshot t and future horizon t + Δ:                        │
│                                               │ ΔSlip(t, t+Δ) = revised_doc(t+Δ) - revised_doc(t)           │
│                                               │ Status: PRIMARY TARGET FRAMEWORK                            │
├───────────────────────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 3. Realized Final Overrun (Long Horizon)      │ Final overrun upon actual commissioning (t_completion):     │
│                                               │ Final_Slip = actual_doc - original_doc                      │
│                                               │ Status: OBSERVABLE ONLY UPON FULL PROJECT COMPLETION        │
└───────────────────────────────────────────────┴─────────────────────────────────────────────────────────────┘
```

> [!WARNING]
> **Why `revised_end_date > original_end_date` CANNOT Be Used as the Target:**  
> A project whose `revised_doc > original_end_date` at time $t$ is **already delayed today**. Using this condition as the label means predicting what is already explicitly published in the monitoring report. A model trained on this target simply memorizes the current status flag, creating instantaneous data leakage and 100% artificial accuracy.

---

## 2. Future Schedule-Overrun Target Framework

A predictive early-warning system must forecast whether an ongoing project will suffer **further slippage or schedule deterioration** over an upcoming decision horizon $\Delta$ (e.g., 2 months, 6 months).

### 2.1 Candidate Formulation 1: Incremental Schedule Slippage (Continuous Target)
Measures the actual calendar days by which the anticipated completion date is postponed between $t$ and $t+\Delta$:

$$\Delta \text{Slippage\_Days}(t, \Delta) = \max\Big(0, \, \big(\text{revised\_end\_date}(t+\Delta) - \text{revised\_end\_date}(t)\big).\text{days}\Big)$$

- *Precondition:* Both $\text{revised\_end\_date}(t)$ and $\text{revised\_end\_date}(t+\Delta)$ must be observed.
- *Default for unrevised at $t$:* If a project had no formal revision at $t$, $\text{revised\_end\_date}(t) = \text{original\_end\_date}$.
- *Interpretation:* Zero indicates the schedule remained stable or improved. Values $> 0$ quantify the magnitude of newly incurred delay.

### 2.2 Candidate Formulation 2: Binary Schedule Deterioration Flag (Classification Target)
Classifies whether a project experiences a meaningful future schedule shock:

$$\mathcal{Y}_{\text{schedule\_deterioration}}(t, \Delta, \theta_s) = \begin{cases} 
1, & \text{if } \Delta \text{Slippage\_Days}(t, \Delta) > \theta_s \\
0, & \text{if } \Delta \text{Slippage\_Days}(t, \Delta) \le \theta_s \\
\text{UNOBSERVABLE}, & \text{if observation at } t+\Delta \text{ is missing}
\end{cases}$$

Where $\theta_s$ is the **slippage tolerance threshold** (e.g., $\theta_s = 0$ days for any postponement, or $\theta_s = 30$ days to filter minor administrative adjustments).  
*Rule:* The exact threshold $\theta_s$ will be selected based on stakeholder requirements and empirical distribution, not arbitrarily hardcoded.

### 2.3 Candidate Formulation 3: Horizon Milestone Failure (Imminent Completion Risk)
For projects whose scheduled completion date falls within the prediction window $[t, t+\Delta]$:

$$\mathcal{Y}_{\text{horizon\_miss}}(t, \Delta) = \begin{cases}
1, & \text{if } \text{revised\_end\_date}(t) \le t + \Delta \text{ AND } \text{physical\_progress}(t+\Delta) < 100.0 \\
0, & \text{if } \text{revised\_end\_date}(t) \le t + \Delta \text{ AND } \text{physical\_progress}(t+\Delta) = 100.0 \\
\text{N/A (Censored)}, & \text{if } \text{revised\_end\_date}(t) > t + \Delta
\end{cases}$$

Identifies projects claiming imminent completion that fail to commission within their target window.

---

## 3. Future Cost-Overrun Target Framework

Predicts whether a project will incur an authorized cost revision or financial budget escalation over future horizon $\Delta$.

### 3.1 Candidate Formulation 1: Incremental Budget Escalation (Continuous Target)
Measures newly authorized cost revisions between $t$ and $t+\Delta$:

$$\Delta \text{Cost\_Escalation}(t, \Delta) = \max\Big(0, \, \text{revised\_cost}(t+\Delta) - \max\big(\text{revised\_cost}(t), \, \text{original\_cost}\big)\Big)$$

- *Interpretation:* Measures the exact ₹ Crore of budget expansion occurring after prediction cutoff $t$.

### 3.2 Candidate Formulation 2: Binary Cost Escalation Flag (Classification Target)
Flags any project undergoing a material future budget expansion:

$$\mathcal{Y}_{\text{cost\_escalation}}(t, \Delta, \theta_c) = \begin{cases} 
1, & \text{if } \frac{\Delta \text{Cost\_Escalation}(t, \Delta)}{\text{original\_cost}} > \theta_c \\
0, & \text{if } \frac{\Delta \text{Cost\_Escalation}(t, \Delta)}{\text{original\_cost}} \le \theta_c \\
\text{UNOBSERVABLE}, & \text{if observation at } t+\Delta \text{ is missing}
\end{cases}$$

Where $\theta_c$ is the percentage cost escalation threshold (e.g., $\theta_c = 0.05$ for a $>5\%$ budget increase).

---

## 4. Handling Unobservable Outcomes & Right Censoring

A rigorous predictive architecture must handle real-world project tracking dynamics without guessing or fabricating missing outcomes:

```
Case A: Full Longitudinal Follow-up
Snapshot t (May) ──────────► Horizon t+Δ (July) ──► Target label CALCULATED

Case B: Unobserved Horizon (Right-Censored / Missing Report)
Snapshot t (May) ──────────► Horizon t+Δ (Missing) ─► Target label = UNOBSERVABLE (Excluded from train loss)

Case C: Project Commissioned / Completed in Horizon
Snapshot t (May) ──────────► Completed at t+1 ──────► Final realization recorded, project retired cleanly
```

1. **Unobservable Status:** If a project observed at snapshot $t$ has no corresponding record at $t+\Delta$ (due to missing monthly reports, dropping out of monitoring, or administrative gaps), the label must be marked `UNOBSERVABLE`.
2. **No Guessing / No Backfill:** Under no circumstances should missing future records be imputed with the snapshot value or synthetic assumptions. Rows with `UNOBSERVABLE` targets can be used for descriptive monitoring audits, but **must be excluded from the supervised loss function during training**.

---

## 5. Temporal Cross-Validation Scheme

### 5.1 Why Random Train/Test Split is Strictly Prohibited
In tabular data with temporal or longitudinal panel structure, applying standard random cross-validation (`train_test_split`, random $K$-fold) introduces catastrophic **temporal autocorrelation leakage**:

- A project $i$ observed across multiple months (e.g., May, June, July) would have its May and July records placed in the training set and its June record placed in the test set.
- The model would interpolate between known historical points rather than forecasting into the future.
- Features strongly correlated with the static project identity (such as exact scale, ministry quirks, or location) would be memorized, producing artificially high validation metrics that collapse entirely in true forward production.

### 5.2 Blocked Longitudinal Temporal Splitting
All empirical benchmarking must follow strict forward-chaining temporal partitions:

```
  Reporting Period:      t0      t1      t2      t3      t4      t5      t6
                      ┌───────┬───────┬───────┬───────┬───────┬───────┬───────┐
  Partition Scheme:   │     TRAINING SET      │  VALIDATION   │   TEST SET    │
                      │  Snapshot Cutoffs     │   Snapshot    │   Snapshot    │
                      └───────┴───────┴───────┴───────┴───────┴───────┴───────┘
                                                  ▲               ▲
                                                  │               │
                                    Tune Hyperparameters    Final Benchmark
```

- **Training Partition ($\mathcal{T}_{\text{train}}$):** Historical periods $t \in [t_{\text{start}}, t_{\text{train\_end}}]$.
- **Validation Partition ($\mathcal{T}_{\text{val}}$):** Intermediate periods $t \in (t_{\text{train\_end}}, t_{\text{val\_end}}]$ used strictly for model selection and hyperparameter tuning.
- **Out-of-Time Test Partition ($\mathcal{T}_{\text{test}}$):** Most recent reporting periods $t > t_{\text{val\_end}}$ held out entirely until final un-blinded evaluation.
- **Purging / Embargo Rule:** If the target uses a horizon of $\Delta$ months, an embargo buffer of $\Delta$ months must separate the training feature cutoff from the evaluation partition to ensure that target outcome windows never overlap across splits.

---

## 6. Current Status

```text
STATUS: SPECIFICATION READY — HISTORICAL DATA REQUIRED BEFORE MODEL TRAINING
```

*This target framework is fully formulated. Threshold selection and target calculation will be executed only once authentic multi-month longitudinal panel data is ingested.*

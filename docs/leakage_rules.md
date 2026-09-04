# PAIMANA Anti-Leakage Rules & Boundary Criteria

> **Project:** SIH26103 — Use Case on Web-Based Integrated Project Monitoring Platform  
> **Product:** PAIMANA Predictive Risk Intelligence  
> **Document:** `docs/leakage_rules.md`  
> **Reference Inputs:** `PAIMANA_Data_Dictionary.xlsx.xlsx`, `reports/module1_data_validation.md`  
> **Status:** SPECIFICATION READY — HISTORICAL DATA REQUIRED BEFORE MODEL TRAINING  

---

## 1. Objective & Scope

In infrastructure project risk prediction, **data leakage** occurs when information from the future, the prediction target itself, or post-outcome events is inadvertently introduced into the feature set. Data leakage creates artificially inflated evaluation scores (e.g. 99% AUC) that fail entirely when deployed on live projects.

This document establishes seven binding, automated **Pass/Fail boundary rules** that govern feature engineering, data transformation, and model training.

---

## 2. Binding Anti-Leakage Rules

```
┌──────────┬──────────────────────────────┬────────────────────────────────────────┬─────────────┐
│ Rule ID  │ Focus Area                   │ Primary Failure Mechanism              │ Gate Type   │
├──────────┼──────────────────────────────┼────────────────────────────────────────┼─────────────┤
│ LR-01    │ Future Revised Cost          │ Using cost revisions approved after t  │ HARD FAIL   │
│ LR-02    │ Future Expenditure           │ Using spending recorded after t        │ HARD FAIL   │
│ LR-03    │ Future Physical Progress     │ Using execution progress achieved > t  │ HARD FAIL   │
│ LR-04    │ Future Revised End Date      │ Using schedule revisions posted > t    │ HARD FAIL   │
│ LR-05    │ Target-Derived Features      │ Engineering features from the label    │ HARD FAIL   │
│ LR-06    │ Post-Outcome Realizations    │ Using completion date of active proj   │ HARD FAIL   │
│ LR-07    │ Random Temporal Mixing       │ Mixing temporal snapshots in train/val │ HARD FAIL   │
└──────────┴──────────────────────────────┴────────────────────────────────────────┴─────────────┘
```

---

### Rule LR-01: Future Revised Cost Exclusion
- **Principle:** Only cost revisions formally sanctioned on or before snapshot cutoff date $t$ may enter the feature vector.
- **PASS Criteria:**
  $$\forall x \in \mathbf{x}_i(t), \quad \tau\big(\texttt{revised\_cost}\big) \le t$$
- **FAIL Condition:** The feature vector contains $\texttt{revised\_cost}(t+\Delta)$ or any ratio computed using post-cutoff financial revisions.
- **Enforcement:** Automated schema assert checks timestamps of cost revisions against snapshot $t$.

---

### Rule LR-02: Future Expenditure Exclusion
- **Principle:** Financial expenditure represents time-cumulative disbursements. Expenditures recorded during month $t+1$ or later are strictly unobservable at time $t$.
- **PASS Criteria:**
  $$\texttt{expenditure\_feature}_i(t) \equiv \texttt{expenditure}_i(\tau \le t)$$
- **FAIL Condition:** Any feature utilizes cumulative expenditure timestamped after $t$, or incorporates future billing receipts.
- **Enforcement:** Automated pipeline rejects any expenditure column where source report period $> t$.

---

### Rule LR-03: Future Physical Progress Exclusion
- **Principle:** Progress percentages ($[0, 100]\%$) must reflect actual engineer-certified site progress logged as of month $t$.
- **PASS Criteria:**
  $$\texttt{physical\_progress\_pct}_i(t) \text{ reflects state at } t$$
- **FAIL Condition:** Progress achieved in subsequent monitoring cycles is passed to the model, or backward-interpolated to simulate past progress.
- **Enforcement:** Strict verification that progress is an exact match for month $t$'s Table 6 extraction.

---

### Rule LR-04: Future Revised Completion Date Exclusion
- **Principle:** Project completion dates are continuously extended as delays occur. Using a revised date that was announced in month $t+1$ to predict delay at month $t$ completely bypasses the prediction task.
- **PASS Criteria:**
  $$\texttt{revised\_end\_date}_i(t) \text{ was published and officially recorded on or before } t$$
- **FAIL Condition:** The model is provided $\texttt{revised\_end\_date}(t+\Delta)$ as an input feature.
- **Enforcement:** Pipeline cross-checks revision notification dates; future revised dates are quarantined exclusively for target label construction.

---

### Rule LR-05: Target-Derived Variable Prohibition
- **Principle:** Features must be independent of the target definition. No feature may be mathematically derived from or proxy the future target label.
- **PASS Criteria:**
  $$\frac{\partial \mathbf{x}_i(t)}{\partial \mathcal{Y}_i(t, \Delta)} \equiv 0$$
- **Enforced Matching Invariant:** When `is_feature_matrix=True`, any column matching any of the following patterns triggers an immediate **HARD FAIL (LR-05)**:
  1. Prefix match: Case-insensitive `^future_` (e.g., `future_slip_days`, `future_cost_change`, `future_schedule_deterioration`).
  2. Suffix match: Case-insensitive `_target$` (e.g., `cost_overrun_target`, `delay_target`).
  3. Generic target aliases: `target`, `label`, `y`.
- **FAIL Condition:** Features proxying future targets are present in the feature matrix.

---

### Rule LR-06: Post-Outcome Realizations & Project Status Leakage
- **Principle:** For ongoing infrastructure projects, actual commissioning dates and final cost overrun amounts are unknown.
- **PASS Criteria:**
  - Actual commissioning date is populated **only** if the project achieved completion prior to $t$.
  - For projects active at $t$, completion-derived statistics are excluded.
- **Enforced Matching Invariant:** When `is_feature_matrix=True`, the presence of any of the following columns triggers an immediate **HARD FAIL (LR-06)**:
  `actual_completion_date`, `commissioning_date`, `actual_doc`, `final_cost`, `final_cost_overrun`.
- **FAIL Condition:** Features include final project audit results, actual completion dates, or post-commissioning settlement figures.

---

### Rule LR-07: Anti-Mixing Temporal Split Invariant
- **Principle:** Evaluation must simulate live deployment: training on past observations, testing on future observations.
- **PASS Criteria:**
  $$\max\big(\mathcal{T}_{\text{train}}\big) < \min\big(\mathcal{T}_{\text{val}}\big) \le \max\big(\mathcal{T}_{\text{val}}\big) < \min\big(\mathcal{T}_{\text{test}}\big)$$
- **FAIL Condition:**
  - Random sampling (`train_test_split`, stratified $K$-fold) applied to longitudinal project-month rows.
  - Project $i$ at month $t+1$ is in training set while project $i$ at month $t$ is in test set.
- **Implementation Status:**
  ```text
  STATUS: SPECIFICATION ACTIVE — NOT-YET-IMPLEMENTED IN validate_panel.py
  OWNERSHIP: Belongs to the downstream temporal splitting / model evaluation module (e.g. src/data/temporal_split.py).
  ```
  `validate_panel.py` validates single-file datasets and feature matrices; partition temporal enforcement will be owned by the dataset splitting pipeline when model development commences.

---

## 3. Pre-Training Leakage Audit Protocol

Before any machine learning model is trained, the feature generation pipeline must execute an automated test suite verifying all seven rules:

```python
def test_leakage_invariants(X_train, y_train, snapshot_date):
    """
    Automated pre-flight leakage test suite.
    Any AssertionError immediately halts pipeline execution.
    """
    # 1. Verify primary key integrity (Entity leakage)
    assert "project_code" not in X_train.columns, "LR-Entity: project_code must not be a feature"
    assert "project_name" not in X_train.columns, "LR-Entity: project_name must not be a feature"
    
    # 2. Verify temporal purity of raw inputs (LR-01 .. LR-04)
    if "reporting_period" in X_train.columns:
        assert (X_train["reporting_period"] <= snapshot_date).all(), "LR-01..04: Features exceed snapshot cutoff"
    
    # 3. Verify no target presence in features (LR-05 prefix/suffix matching)
    for col in X_train.columns:
        c_lower = col.lower().strip()
        assert not c_lower.startswith("future_"), f"LR-05: Target prefix column found: {col}"
        assert not c_lower.endswith("_target"), f"LR-05: Target suffix column found: {col}"
        assert c_lower not in {"target", "label", "future_cost_change"}, f"LR-05: Target column found: {col}"
    
    # 4. Verify no post-outcome variables (LR-06)
    post_outcome = {"actual_completion_date", "commissioning_date", "actual_doc", "final_cost", "final_cost_overrun"}
    assert not any(c.lower().strip() in post_outcome for c in X_train.columns), "LR-06: Post-outcome date present"
    
    print("[PASS] Pre-flight Anti-Leakage Audit passed all active invariants.")
```

---

## 4. Current Status

```text
STATUS: SPECIFICATION READY — HISTORICAL DATA REQUIRED BEFORE MODEL TRAINING
```

*These anti-leakage rules are codified as mandatory constraints for all subsequent pipeline modules.*

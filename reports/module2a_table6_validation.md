# Module 2A — July 2026 Table 6 Validation Report

Generated: `2026-09-05 11:17:48`

## 1. Source

- Source file: `data/raw/flash_reports/FlashReport_July_2026.pdf`
- Source table: Table 6 — All Ongoing Projects
- PDF pages processed: 55–152
- Reporting period: July 2026

## 2. Extraction Result

- Expected projects: **1775**
- Extracted projects: **1775**
- Unique project IDs: **1775**
- Duplicate project IDs: **0**
- Duplicate serial numbers: **0**
- Missing serial numbers: **0**

## 3. Critical Field Completeness

| Field | Missing values |
|---|---:|
| `project_id` | 0 |
| `project_name` | 0 |
| `state` | 0 |
| `original_cost_crore` | 0 |
| `revised_cost_crore` | 0 |
| `cumulative_expenditure_crore` | 0 |
| `physical_progress_pct` | 0 |

## 4. Numeric Validation

- Invalid physical progress values: **0**
- Negative original costs: **0**
- Negative revised costs: **0**
- Negative expenditure values: **0**
- Projects where revised cost < original cost: **316**
- Projects where expenditure > revised cost: **59**

The two comparison conditions above are retained as source-observed anomalies and are not automatically corrected.

## 5. Aggregate Reconciliation

| Metric | Official report | Extracted dataset | Difference |
|---|---:|---:|---:|
| Original cost (₹ crore) | 3,370,138 | 3,370,138.22 | +0.22 |
| Revised cost (₹ crore) | 3,710,642 | 3,710,641.55 | -0.45 |
| Cumulative expenditure (₹ crore) | 1,926,100 | 1,926,099.57 | -0.43 |

The extracted totals reconcile with the rounded report-level totals.

## 6. Physical Progress

- Minimum: **0.00%**
- Maximum: **100.00%**
- Average: **59.00%**

## 7. Dataset Lineage

```text
Official July 2026 Flash Report
        ↓
Table 6 — All Ongoing Projects
        ↓
PDF pages 55–152
        ↓
pdfplumber table extraction
        ↓
table6_july_2026_projects.csv
        ↓
Structural + semantic validation
        ↓
Aggregate reconciliation
```

## 8. Validation Status

### PASS — July 2026 Table 6 dataset validated

The raw PDF remains immutable. The extracted CSV is a derived dataset and must not be treated as the original source.
"""
PAIMANA Unified Longitudinal Data & AI Pipeline.

Authoritative Specifications:
- docs/data_contract.md (Canonical Ingestion Schema & Integrity Invariants)
- docs/leakage_rules.md (Rules LR-01 through LR-07 Anti-Leakage Constraints)
- docs/pit_feature_specification.md (Longitudinal Snapshot Formalism & Feature Inventory)
- docs/target_definition.md (Continuous & Binary Target Formulations across Horizons)
- docs/validation_pipeline.md (Four-Tier Validation Protocol)

Orchestration Architecture:
1. Input Data Validation: Enforces data contract schema, primary key uniqueness, bounds (validate_panel.py).
2. Point-in-Time Feature Engineering: Calculates baseline and 12 authoritative derived/velocity features (longitudinal_pit_features.py).
3. Multi-Horizon Target Construction: Computes continuous and binary cost and schedule targets for horizons Δ ∈ {1, 3, 6, 12} months (build_targets.py).
4. Feature Matrix Partitioning: Explicitly separates Model A (official CUF baseline) vs Model B (enhanced PIT).
5. Temporal Partitioning: Applies forward-chaining / blocked temporal split with embargo buffer (temporal_split.py).
6. Anti-Leakage Auditing: Enforces LR-01 through LR-07 pre-flight verification.
7. Lineage & Metadata Reporting: Produces structured audit metadata for reproducible ML experiments.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from src.data.temporal_split import (
    BlockedTemporalSplitter,
    TemporalSplitError,
    TemporalSplitResult,
    verify_temporal_split,
)
from src.data.validate_panel import (
    PanelDataValidator,
    ValidationReport,
)
from src.features.build_targets import (
    TargetBuilder,
    TargetColumnConfig,
    TargetConstructionError,
    TargetLeakageError,
    audit_feature_target_separation,
)
from src.features.longitudinal_pit_features import (
    LongitudinalPITFeatureBuilder,
    PITColumnConfig,
    PITFeatureError,
)


# ==============================================================================
# 1. PIPELINE CONFIGURATION & RESULT CONTAINERS
# ==============================================================================

@dataclass
class LongitudinalPipelineConfig:
    """Orchestration configuration for the longitudinal Data/AI pipeline."""
    # Target horizons
    horizons: List[int] = field(default_factory=lambda: [1, 3, 6, 12])
    cost_overrun_threshold: float = 0.05
    schedule_deterioration_threshold: float = 0.0

    # Temporal splitting
    perform_temporal_split: bool = True
    train_ratio: float = 0.70
    val_ratio: float = 0.0
    test_ratio: Optional[float] = None
    embargo_periods: int = 0
    train_end: Optional[str] = None
    test_start: Optional[str] = None
    val_end: Optional[str] = None

    # Validation
    enforce_strict_validation: bool = True
    allow_warnings: bool = True

    # Column configuration
    pit_config: Optional[PITColumnConfig] = None
    target_config: Optional[TargetColumnConfig] = None


@dataclass
class LongitudinalPipelineResult:
    """Encapsulates the complete dataset outputs and audit lineage."""
    annotated_dataset: pd.DataFrame
    model_a_features: pd.DataFrame
    model_b_features: pd.DataFrame
    target_matrix: pd.DataFrame
    temporal_split: Optional[TemporalSplitResult] = None
    validation_report: Optional[ValidationReport] = None
    audit_metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        """Return human-readable summary of pipeline execution."""
        return {
            "total_observations": len(self.annotated_dataset),
            "model_a_feature_count": len(self.model_a_features.columns),
            "model_b_feature_count": len(self.model_b_features.columns),
            "target_column_count": len(self.target_matrix.columns),
            "horizons": self.audit_metadata.get("horizons", []),
            "temporal_split_status": "ENABLED" if self.temporal_split is not None else "DISABLED",
            "leakage_audit_status": self.audit_metadata.get("leakage_audit_status", "UNKNOWN"),
        }

    def save(self, output_dir: Union[str, Path]) -> Dict[str, str]:
        """
        Save all pipeline artifacts and metadata to a specified directory.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        paths = {}

        # 1. Annotated full dataset
        p_annot = out_path / "longitudinal_annotated_dataset.csv"
        self.annotated_dataset.to_csv(p_annot, index=False)
        paths["annotated_dataset"] = str(p_annot)

        # 2. Model A feature matrix
        p_ma = out_path / "model_a_features.csv"
        self.model_a_features.to_csv(p_ma, index=False)
        paths["model_a_features"] = str(p_ma)

        # 3. Model B feature matrix
        p_mb = out_path / "model_b_features.csv"
        self.model_b_features.to_csv(p_mb, index=False)
        paths["model_b_features"] = str(p_mb)

        # 4. Target matrix
        p_tgt = out_path / "target_matrix.csv"
        self.target_matrix.to_csv(p_tgt, index=False)
        paths["target_matrix"] = str(p_tgt)

        # 5. Temporal partitions (if present)
        if self.temporal_split is not None:
            p_train = out_path / "train_partition.csv"
            p_test = out_path / "test_partition.csv"
            self.temporal_split.train.to_csv(p_train, index=False)
            self.temporal_split.test.to_csv(p_test, index=False)
            paths["train_partition"] = str(p_train)
            paths["test_partition"] = str(p_test)
            if self.temporal_split.val is not None:
                p_val = out_path / "val_partition.csv"
                self.temporal_split.val.to_csv(p_val, index=False)
                paths["val_partition"] = str(p_val)

        # 6. Audit metadata JSON
        p_meta = out_path / "pipeline_metadata.json"
        with open(p_meta, "w", encoding="utf-8") as f:
            json.dump(self.audit_metadata, f, indent=2, default=str)
        paths["metadata"] = str(p_meta)

        return paths


# ==============================================================================
# 2. UNIFIED PIPELINE RUNNER
# ==============================================================================

class LongitudinalDatasetPipeline:
    """
    Unified execution pipeline connecting data validation, PIT feature engineering,
    multi-horizon target construction, and Rule LR-07 temporal partitioning.
    """

    def __init__(self, config: Optional[LongitudinalPipelineConfig] = None):
        """Initialize the pipeline with configuration."""
        self.config = config or LongitudinalPipelineConfig()

    def run(self, df: pd.DataFrame) -> LongitudinalPipelineResult:
        """
        Execute the full longitudinal Data/AI pipeline on an input longitudinal panel.

        Args:
            df: Input panel DataFrame at (project_code, reporting_period) grain.

        Returns:
            LongitudinalPipelineResult containing datasets, partitions, and audit metadata.

        Raises:
            ValueError, PITFeatureError, TargetConstructionError, or TemporalSplitError
            if validation fails or leakage is detected.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected pandas DataFrame, got {type(df)}.")
        if df.empty:
            raise ValueError("Input longitudinal dataset is empty.")

        metadata: Dict[str, Any] = {
            "initial_rows": len(df),
            "horizons": self.config.horizons,
            "cost_overrun_threshold": self.config.cost_overrun_threshold,
            "schedule_deterioration_threshold": self.config.schedule_deterioration_threshold,
        }

        # -------------------------------------------------------------
        # Step 1: Ingestion Validation (docs/data_contract.md)
        # -------------------------------------------------------------
        validator = PanelDataValidator(allow_snapshot_only=True)
        val_report = validator.validate(df)

        if self.config.enforce_strict_validation and val_report.hard_fails:
            fail_msgs = [f"[{f.rule_id}] {f.message}" for f in val_report.hard_fails]
            raise ValueError(f"Ingestion Data Contract Violation (Hard Stop):\n" + "\n".join(fail_msgs))

        metadata["validation_status"] = val_report.status
        metadata["validation_hard_fails"] = len(val_report.hard_fails)
        metadata["validation_warnings"] = len(val_report.warnings)

        # -------------------------------------------------------------
        # Step 2: Point-in-Time Feature Engineering (docs/pit_feature_specification.md)
        # -------------------------------------------------------------
        pit_builder = LongitudinalPITFeatureBuilder(config=self.config.pit_config)
        df_pit = pit_builder.build_pit_features(df, config=self.config.pit_config)

        # -------------------------------------------------------------
        # Step 3: Multi-Horizon Target Construction (docs/target_definition.md)
        # -------------------------------------------------------------
        target_builder = TargetBuilder(
            horizons=self.config.horizons,
            cost_overrun_threshold=self.config.cost_overrun_threshold,
            schedule_deterioration_threshold=self.config.schedule_deterioration_threshold,
            config=self.config.target_config,
        )
        df_annotated = target_builder.build_targets(df_pit, config=self.config.target_config)

        # -------------------------------------------------------------
        # Step 4: Model A vs Model B Feature Separation
        # -------------------------------------------------------------
        model_a_features = pit_builder.extract_model_a_features(df_pit, config=self.config.pit_config)
        model_b_features = pit_builder.extract_model_b_features(df_pit, config=self.config.pit_config)

        # Extract dedicated target matrix (target columns and observability flags)
        target_col_names = []
        for h in self.config.horizons:
            target_col_names.extend([
                f"target_cost_escalation_{h}m_cr",
                f"target_cost_escalation_pct_{h}m",
                f"target_cost_overrun_{h}m_binary",
                f"target_schedule_slippage_{h}m_days",
                f"target_schedule_deterioration_{h}m_binary",
                f"target_horizon_miss_{h}m_binary",
                f"is_observable_cost_{h}m",
                f"is_observable_schedule_{h}m",
                f"is_observable_{h}m",
            ])
        existing_target_cols = [c for c in target_col_names if c in df_annotated.columns]
        target_matrix = df_annotated[existing_target_cols].copy()

        # -------------------------------------------------------------
        # Step 5: Anti-Leakage Pre-Flight Verification (LR-01 .. LR-06)
        # -------------------------------------------------------------
        audit_feature_target_separation(model_a_features, target_columns=existing_target_cols)
        audit_feature_target_separation(model_b_features, target_columns=existing_target_cols)
        metadata["leakage_audit_status"] = "PASS"

        # -------------------------------------------------------------
        # Step 6: Temporal Partitioning (Rule LR-07)
        # -------------------------------------------------------------
        split_result: Optional[TemporalSplitResult] = None
        if self.config.perform_temporal_split:
            # Determine period and entity column names
            p_cfg = self.config.pit_config or PITColumnConfig.auto_detect(df)
            time_col = p_cfg.period_col
            entity_col = p_cfg.entity_col

            splitter = BlockedTemporalSplitter(
                time_column=time_col,
                entity_column=entity_col,
                embargo_periods=self.config.embargo_periods,
            )

            if self.config.train_end is not None:
                split_result = splitter.split_by_cutoffs(
                    df_annotated,
                    train_end=self.config.train_end,
                    test_start=self.config.test_start,
                    val_end=self.config.val_end,
                )
            else:
                split_result = splitter.split_by_ratio(
                    df_annotated,
                    train_ratio=self.config.train_ratio,
                    val_ratio=self.config.val_ratio,
                    test_ratio=self.config.test_ratio,
                )

            metadata["temporal_split"] = split_result.summary()

        metadata["final_rows"] = len(df_annotated)
        metadata["unique_projects"] = df_annotated[pit_builder.config.entity_col if pit_builder.config else "project_code"].nunique() if "project_code" in df_annotated.columns or (pit_builder.config and pit_builder.config.entity_col in df_annotated.columns) else 0
        metadata["reporting_periods"] = sorted(df_annotated[pit_builder.config.period_col if pit_builder.config else "reporting_period"].unique().tolist()) if "reporting_period" in df_annotated.columns or (pit_builder.config and pit_builder.config.period_col in df_annotated.columns) else []

        return LongitudinalPipelineResult(
            annotated_dataset=df_annotated,
            model_a_features=model_a_features,
            model_b_features=model_b_features,
            target_matrix=target_matrix,
            temporal_split=split_result,
            validation_report=val_report,
            audit_metadata=metadata,
        )


# ==============================================================================
# 3. CONVENIENCE FUNCTION
# ==============================================================================

def run_longitudinal_pipeline(
    df: pd.DataFrame,
    horizons: Sequence[int] = (1, 3, 6, 12),
    perform_temporal_split: bool = True,
    train_ratio: float = 0.70,
    embargo_periods: int = 0,
    **kwargs: Any,
) -> LongitudinalPipelineResult:
    """
    Convenience functional interface to execute the full longitudinal Data/AI pipeline.
    """
    cfg = LongitudinalPipelineConfig(
        horizons=list(horizons),
        perform_temporal_split=perform_temporal_split,
        train_ratio=train_ratio,
        embargo_periods=embargo_periods,
        **kwargs,
    )
    pipeline = LongitudinalDatasetPipeline(config=cfg)
    return pipeline.run(df)


# ==============================================================================
# 4. CLI COMMAND-LINE INTERFACE
# ==============================================================================

def main() -> None:
    """CLI runner for the longitudinal dataset pipeline."""
    parser = argparse.ArgumentParser(
        description="PAIMANA Unified Longitudinal Data & AI Pipeline"
    )
    parser.add_argument("input_csv", type=str, help="Path to input panel CSV")
    parser.add_argument("--output-dir", type=str, default="data/processed/longitudinal_pipeline", help="Directory to save artifacts")
    parser.add_argument("--horizons", type=int, nargs="+", default=[1, 3, 6, 12], help="Target horizons")
    parser.add_argument("--train-ratio", type=float, default=0.70, help="Temporal split train ratio")
    parser.add_argument("--embargo", type=int, default=0, help="Embargo buffer periods")
    parser.add_argument("--no-split", action="store_true", help="Disable temporal splitting")

    args = parser.parse_args()

    if not os.path.exists(args.input_csv):
        print(f"[ERROR] Input file not found: {args.input_csv}")
        sys.exit(1)

    df = pd.read_csv(args.input_csv)
    print(f"[INFO] Loaded input dataset: {args.input_csv} ({len(df)} rows)")

    cfg = LongitudinalPipelineConfig(
        horizons=args.horizons,
        perform_temporal_split=not args.no_split,
        train_ratio=args.train_ratio,
        embargo_periods=args.embargo,
    )

    pipeline = LongitudinalDatasetPipeline(config=cfg)
    try:
        result = pipeline.run(df)
        paths = result.save(args.output_dir)

        print("=" * 65)
        print("PAIMANA LONGITUDINAL PIPELINE EXECUTION SUCCESS")
        print("=" * 65)
        print(f"Annotated Dataset:     {paths['annotated_dataset']}")
        print(f"Model A Features:      {paths['model_a_features']}")
        print(f"Model B Features:      {paths['model_b_features']}")
        print(f"Target Matrix:         {paths['target_matrix']}")
        if "train_partition" in paths:
            print(f"Train Partition:       {paths['train_partition']}")
            print(f"Test Partition:        {paths['test_partition']}")
        print(f"Metadata JSON:         {paths['metadata']}")
        print("=" * 65)
    except Exception as e:
        print(f"[FAIL] Pipeline execution error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()

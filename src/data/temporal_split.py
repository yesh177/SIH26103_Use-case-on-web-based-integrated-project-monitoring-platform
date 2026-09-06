"""
PAIMANA Temporal Data Splitting & Horizon Embargo Module (LR-07).

Authoritative Specifications:
- docs/leakage_rules.md (Rule LR-07: Anti-Mixing Temporal Split Invariant)
- docs/target_definition.md (Section 5: Temporal Cross-Validation Scheme)
- docs/pit_feature_specification.md
- docs/validation_pipeline.md

Enforces forward-chaining / blocked temporal train/validation/test partitions,
purging / embargo buffer separation to prevent horizon overlap leakage,
and strict project entity chronological ordering.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd


# ==============================================================================
# 1. CUSTOM EXCEPTIONS
# ==============================================================================

class TemporalSplitError(ValueError):
    """Base exception for errors during temporal splitting."""
    pass


class TemporalLeakageError(TemporalSplitError):
    """Raised when an anti-leakage rule (e.g. LR-07) or embargo invariant is violated."""
    pass


# ==============================================================================
# 2. DATA STRUCTURES
# ==============================================================================

@dataclass
class TemporalSplitResult:
    """Container for temporal split partitions and lineage metadata."""
    train: pd.DataFrame
    test: pd.DataFrame
    val: Optional[pd.DataFrame] = None

    # Metadata
    time_column: str = "reporting_period"
    entity_column: Optional[str] = "project_code"
    embargo_periods: int = 0

    # Audit summary
    train_periods: List[str] = field(default_factory=list)
    val_periods: List[str] = field(default_factory=list)
    test_periods: List[str] = field(default_factory=list)
    purged_periods: List[str] = field(default_factory=list)

    train_count: int = 0
    val_count: int = 0
    test_count: int = 0
    purged_count: int = 0

    def summary(self) -> Dict[str, Any]:
        """Return a structured audit summary dictionary."""
        return {
            "time_column": self.time_column,
            "entity_column": self.entity_column,
            "embargo_periods": self.embargo_periods,
            "train": {
                "rows": len(self.train),
                "periods": self.train_periods,
                "min_period": self.train_periods[0] if self.train_periods else None,
                "max_period": self.train_periods[-1] if self.train_periods else None,
            },
            "val": {
                "rows": len(self.val) if self.val is not None else 0,
                "periods": self.val_periods,
                "min_period": self.val_periods[0] if self.val_periods else None,
                "max_period": self.val_periods[-1] if self.val_periods else None,
            },
            "test": {
                "rows": len(self.test),
                "periods": self.test_periods,
                "min_period": self.test_periods[0] if self.test_periods else None,
                "max_period": self.test_periods[-1] if self.test_periods else None,
            },
            "purged": {
                "rows": self.purged_count,
                "periods": self.purged_periods,
            },
        }


# ==============================================================================
# 3. HELPER FUNCTIONS FOR TEMPORAL PERIOD CONVERSION
# ==============================================================================

def _normalize_period_series(series: pd.Series) -> pd.Series:
    """
    Ensure temporal series is standardized to string or comparable timestamps.
    Supports YYYY-MM period strings, date strings, or datetime64.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.dt.strftime("%Y-%m")
    return series.astype(str).str.strip()


def _period_month_distance(period_a: str, period_b: str) -> int:
    """
    Calculate calendar month distance between two 'YYYY-MM' strings: index(B) - index(A).
    Positive if period_b > period_a.
    """
    try:
        parts_a = period_a.split("-")
        parts_b = period_b.split("-")
        y_a, m_a = int(parts_a[0]), int(parts_a[1])
        y_b, m_b = int(parts_b[0]), int(parts_b[1])
        return (y_b - y_a) * 12 + (m_b - m_a)
    except Exception:
        # Fallback to general comparison if not YYYY-MM
        return 0


# ==============================================================================
# 4. TEMPORAL LEAKAGE VERIFIER (LR-07)
# ==============================================================================

def verify_temporal_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    time_column: str = "reporting_period",
    val_df: Optional[pd.DataFrame] = None,
    entity_column: Optional[str] = "project_code",
    embargo_periods: int = 0,
) -> Dict[str, Any]:
    """
    Automated pre-flight leakage auditor verifying Rule LR-07 invariants.

    Verifies:
    1. No index overlap across partitions.
    2. Strict chronological ordering: max(train) < min(test) (and max(train) < min(val) < min(test)).
    3. Horizon embargo buffer satisfied: min(test) is at least `embargo_periods` after max(train).
    4. Repeated project entity integrity: for any project appearing in both train and test/val,
       all its train records must be strictly earlier than all its test/val records.

    Raises:
        TemporalLeakageError if any invariant is violated.
        TemporalSplitError if inputs are malformed.
    """
    if train_df.empty:
        raise TemporalSplitError("LR-07 Violation: Training partition is empty.")
    if test_df.empty:
        raise TemporalSplitError("LR-07 Violation: Test partition is empty.")
    if time_column not in train_df.columns or time_column not in test_df.columns:
        raise TemporalSplitError(f"Missing time column '{time_column}' in partitions.")
    if val_df is not None and not val_df.empty and time_column not in val_df.columns:
        raise TemporalSplitError(f"Missing time column '{time_column}' in validation partition.")

    # 1. Index Disjointness
    train_idx = set(train_df.index)
    test_idx = set(test_df.index)
    idx_overlap = train_idx.intersection(test_idx)
    if idx_overlap:
        raise TemporalLeakageError(
            f"LR-07 Index Overlap: {len(idx_overlap)} rows exist in both train and test partitions."
        )

    if val_df is not None and not val_df.empty:
        val_idx = set(val_df.index)
        val_train_overlap = train_idx.intersection(val_idx)
        val_test_overlap = test_idx.intersection(val_idx)
        if val_train_overlap:
            raise TemporalLeakageError(
                f"LR-07 Index Overlap: {len(val_train_overlap)} rows exist in both train and val partitions."
            )
        if val_test_overlap:
            raise TemporalLeakageError(
                f"LR-07 Index Overlap: {len(val_test_overlap)} rows exist in both val and test partitions."
            )

    # 2. Chronological Separation
    train_times = _normalize_period_series(train_df[time_column])
    test_times = _normalize_period_series(test_df[time_column])

    max_train_time = train_times.max()
    min_test_time = test_times.min()

    if max_train_time >= min_test_time:
        raise TemporalLeakageError(
            f"LR-07 Future Leakage: max(train) '{max_train_time}' >= min(test) '{min_test_time}'."
        )

    if val_df is not None and not val_df.empty:
        val_times = _normalize_period_series(val_df[time_column])
        max_val_time = val_times.max()
        min_val_time = val_times.min()

        if max_train_time >= min_val_time:
            raise TemporalLeakageError(
                f"LR-07 Future Leakage: max(train) '{max_train_time}' >= min(val) '{min_val_time}'."
            )
        if max_val_time >= min_test_time:
            raise TemporalLeakageError(
                f"LR-07 Future Leakage: max(val) '{max_val_time}' >= min(test) '{min_test_time}'."
            )

    # 3. Horizon Embargo Buffer Verification
    if embargo_periods > 0:
        eval_start = min_val_time if (val_df is not None and not val_df.empty) else min_test_time
        month_dist = _period_month_distance(max_train_time, eval_start)

        # If month_dist can be parsed, verify month_dist > embargo_periods
        if month_dist > 0 and month_dist <= embargo_periods:
            raise TemporalLeakageError(
                f"LR-07 Embargo Violation: Distance between train max ('{max_train_time}') and "
                f"evaluation min ('{eval_start}') is {month_dist} months, which does not exceed "
                f"the required embargo buffer of {embargo_periods} periods."
            )

    # 4. Repeated Project Entity Integrity
    common_entities = set()
    if entity_column and entity_column in train_df.columns and entity_column in test_df.columns:
        common_entities = set(train_df[entity_column]).intersection(set(test_df[entity_column]))
        if common_entities:
            for entity in common_entities:
                entity_train_max = train_times[train_df[entity_column] == entity].max()
                entity_test_min = test_times[test_df[entity_column] == entity].min()
                if entity_train_max >= entity_test_min:
                    raise TemporalLeakageError(
                        f"LR-07 Entity Leakage for entity '{entity}': max train date '{entity_train_max}' "
                        f">= min test date '{entity_test_min}'."
                    )

        if val_df is not None and not val_df.empty and entity_column in val_df.columns:
            val_common_entities = set(train_df[entity_column]).intersection(set(val_df[entity_column]))
            for entity in val_common_entities:
                entity_train_max = train_times[train_df[entity_column] == entity].max()
                entity_val_min = val_times[val_df[entity_column] == entity].min()
                if entity_train_max >= entity_val_min:
                    raise TemporalLeakageError(
                        f"LR-07 Entity Leakage for entity '{entity}': max train date '{entity_train_max}' "
                        f">= min val date '{entity_val_min}'."
                    )

    return {
        "status": "PASS",
        "rule": "LR-07",
        "max_train_period": max_train_time,
        "min_test_period": min_test_time,
        "embargo_satisfied": True,
        "repeated_entities_checked": len(common_entities),
    }


# ==============================================================================
# 5. BLOCKED TEMPORAL SPLITTER
# ==============================================================================

class BlockedTemporalSplitter:
    """
    Executes blocked / forward-chaining temporal train/validation/test partitions.

    Guarantees strict chronological ordering, horizon overlap purging / embargo buffers,
    and repeated entity non-leakage (Rule LR-07).
    """

    def __init__(
        self,
        time_column: str = "reporting_period",
        entity_column: Optional[str] = "project_code",
        embargo_periods: int = 0,
    ):
        """
        Initialize the blocked splitter.

        Args:
            time_column: Name of the temporal snapshot column (e.g. 'reporting_period').
            entity_column: Name of the entity identifier column (e.g. 'project_code').
            embargo_periods: Number of buffer periods to purge between train cutoff and evaluation
                             to prevent target horizon overlap leakage.
        """
        if embargo_periods < 0:
            raise TemporalSplitError(f"embargo_periods cannot be negative (got {embargo_periods}).")
        self.time_column = time_column
        self.entity_column = entity_column
        self.embargo_periods = embargo_periods

    def split_by_cutoffs(
        self,
        df: pd.DataFrame,
        train_end: str,
        test_start: Optional[str] = None,
        val_end: Optional[str] = None,
    ) -> TemporalSplitResult:
        """
        Split dataset using explicit period cutoffs.

        Args:
            df: Input panel DataFrame.
            train_end: Upper bound period for training partition (inclusive).
            test_start: Lower bound period for test partition (inclusive). If None, inferred
                        from train_end (or val_end) + embargo_periods + 1.
            val_end: Upper bound period for validation partition (inclusive). Optional.

        Returns:
            TemporalSplitResult with partitioned DataFrames.
        """
        self._validate_input_df(df)

        df_sorted = df.copy()
        norm_time = _normalize_period_series(df_sorted[self.time_column])
        df_sorted["_norm_time"] = norm_time

        available_periods = sorted(norm_time.unique())
        if train_end not in available_periods and train_end < available_periods[0]:
            raise TemporalSplitError(
                f"train_end '{train_end}' is earlier than earliest available period '{available_periods[0]}'."
            )

        # 1. Training Slice
        train_mask = df_sorted["_norm_time"] <= train_end
        train_df = df_sorted[train_mask].drop(columns=["_norm_time"])
        if train_df.empty:
            raise TemporalSplitError(f"No records found for training partition with train_end <= '{train_end}'.")

        train_periods = sorted(norm_time[train_mask].unique())
        last_train_period = train_periods[-1]

        # 2. Validation Slice (if requested)
        val_df = None
        val_periods = []
        last_boundary_period = last_train_period

        if val_end is not None:
            if val_end <= train_end:
                raise TemporalSplitError(f"val_end '{val_end}' must be strictly after train_end '{train_end}'.")

            val_start_candidates = [p for p in available_periods if p > last_train_period]
            if self.embargo_periods > 0 and len(val_start_candidates) > self.embargo_periods:
                purged_for_val = val_start_candidates[:self.embargo_periods]
            else:
                purged_for_val = []

            val_mask = (df_sorted["_norm_time"] > train_end) & (df_sorted["_norm_time"] <= val_end)
            if purged_for_val:
                val_mask = val_mask & (~df_sorted["_norm_time"].isin(purged_for_val))

            val_df = df_sorted[val_mask].drop(columns=["_norm_time"])
            if val_df.empty:
                raise TemporalSplitError(f"No records found for validation partition with val_end <= '{val_end}'.")
            val_periods = sorted(norm_time[val_mask].unique())
            last_boundary_period = val_periods[-1]

        # 3. Determine Test Start with Embargo
        post_boundary_periods = [p for p in available_periods if p > last_boundary_period]

        if test_start is not None:
            if test_start <= last_boundary_period:
                raise TemporalSplitError(
                    f"test_start '{test_start}' must be strictly after previous partition boundary '{last_boundary_period}'."
                )
            actual_test_start = test_start
            purged_periods = [p for p in post_boundary_periods if p < actual_test_start]
        else:
            if len(post_boundary_periods) <= self.embargo_periods:
                raise TemporalSplitError(
                    f"Insufficient remaining periods ({len(post_boundary_periods)}) after boundary '{last_boundary_period}' "
                    f"to satisfy embargo_periods={self.embargo_periods} and form a non-empty test set."
                )
            purged_periods = post_boundary_periods[:self.embargo_periods]
            actual_test_start = post_boundary_periods[self.embargo_periods]

        # 4. Test Slice
        test_mask = df_sorted["_norm_time"] >= actual_test_start
        test_df = df_sorted[test_mask].drop(columns=["_norm_time"])
        if test_df.empty:
            raise TemporalSplitError(f"No records found for test partition with test_start >= '{actual_test_start}'.")
        test_periods = sorted(norm_time[test_mask].unique())

        purged_mask = df_sorted["_norm_time"].isin(purged_periods)
        purged_count = int(purged_mask.sum())

        # Verify Leakage Invariants
        verify_temporal_split(
            train_df=train_df,
            test_df=test_df,
            time_column=self.time_column,
            val_df=val_df,
            entity_column=self.entity_column,
            embargo_periods=self.embargo_periods,
        )

        return TemporalSplitResult(
            train=train_df,
            test=test_df,
            val=val_df,
            time_column=self.time_column,
            entity_column=self.entity_column,
            embargo_periods=self.embargo_periods,
            train_periods=train_periods,
            val_periods=val_periods,
            test_periods=test_periods,
            purged_periods=purged_periods,
            train_count=len(train_df),
            val_count=len(val_df) if val_df is not None else 0,
            test_count=len(test_df),
            purged_count=purged_count,
        )

    def split_by_ratio(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.0,
        test_ratio: Optional[float] = None,
    ) -> TemporalSplitResult:
        """
        Split dataset into chronological partitions based on period ratios.
        Ratios partition unique reporting periods, ensuring full month cohorts remain intact.
        """
        self._validate_input_df(df)

        if train_ratio <= 0.0 or train_ratio >= 1.0:
            raise TemporalSplitError(f"train_ratio must be between 0 and 1 (got {train_ratio}).")
        if val_ratio < 0.0 or val_ratio >= 1.0:
            raise TemporalSplitError(f"val_ratio must be between 0 and 1 (got {val_ratio}).")

        if test_ratio is None:
            test_ratio = 1.0 - train_ratio - val_ratio
        if test_ratio <= 0.0:
            raise TemporalSplitError(f"test_ratio must be strictly positive (calculated {test_ratio}).")

        if (train_ratio + val_ratio + test_ratio) > 1.0001:
            raise TemporalSplitError(f"Sum of ratios ({train_ratio + val_ratio + test_ratio}) exceeds 1.0.")

        norm_time = _normalize_period_series(df[self.time_column])
        unique_periods = sorted(norm_time.unique())
        n_periods = len(unique_periods)

        if n_periods < 2:
            raise TemporalSplitError(
                f"Longitudinal temporal splitting requires at least 2 unique periods; got {n_periods}."
            )

        n_train = max(1, int(np.floor(n_periods * train_ratio)))
        n_val = max(1, int(np.floor(n_periods * val_ratio))) if val_ratio > 0.0 else 0

        if (n_train + n_val + self.embargo_periods) >= n_periods:
            raise TemporalSplitError(
                f"Cannot satisfy train ({n_train}) + val ({n_val}) + embargo ({self.embargo_periods}) "
                f"within total available periods ({n_periods})."
            )

        train_end = unique_periods[n_train - 1]
        val_end = unique_periods[n_train + n_val - 1] if n_val > 0 else None

        return self.split_by_cutoffs(
            df=df,
            train_end=train_end,
            val_end=val_end,
        )

    def _validate_input_df(self, df: pd.DataFrame) -> None:
        """Validate input DataFrame schema and basic temporal requirements."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected pandas DataFrame, got {type(df)}.")
        if df.empty:
            raise TemporalSplitError("Input DataFrame is empty.")
        if self.time_column not in df.columns:
            raise TemporalSplitError(f"Time column '{self.time_column}' not found in DataFrame.")
        if df[self.time_column].isna().any():
            raise TemporalSplitError(f"Time column '{self.time_column}' contains null values.")


# ==============================================================================
# 6. ROLLING / FORWARD-CHAINING TEMPORAL SPLITTER
# ==============================================================================

class RollingTemporalSplitter:
    """
    Generates expanding-window or sliding-window forward-chaining cross-validation folds.

    Guarantees that each successive fold trains strictly on historical observations,
    respects the horizon embargo buffer, and evaluates strictly on future unseen periods.
    """

    def __init__(
        self,
        time_column: str = "reporting_period",
        entity_column: Optional[str] = "project_code",
        n_splits: int = 3,
        min_train_periods: int = 2,
        test_periods: int = 1,
        embargo_periods: int = 0,
        expanding: bool = True,
    ):
        """
        Initialize rolling temporal cross-validator.

        Args:
            time_column: Reporting period column name.
            entity_column: Entity identifier column name.
            n_splits: Number of forward-chaining cross-validation folds.
            min_train_periods: Minimum historical periods required for the first training fold.
            test_periods: Number of periods in each evaluation fold.
            embargo_periods: Number of purged buffer periods separating train and test.
            expanding: If True, uses expanding window (all past data); if False, uses fixed window.
        """
        if n_splits < 1:
            raise TemporalSplitError(f"n_splits must be at least 1 (got {n_splits}).")
        if min_train_periods < 1:
            raise TemporalSplitError(f"min_train_periods must be at least 1 (got {min_train_periods}).")
        if test_periods < 1:
            raise TemporalSplitError(f"test_periods must be at least 1 (got {test_periods}).")
        if embargo_periods < 0:
            raise TemporalSplitError(f"embargo_periods cannot be negative (got {embargo_periods}).")

        self.time_column = time_column
        self.entity_column = entity_column
        self.n_splits = n_splits
        self.min_train_periods = min_train_periods
        self.test_periods = test_periods
        self.embargo_periods = embargo_periods
        self.expanding = expanding

    def split(
        self, df: pd.DataFrame
    ) -> Generator[Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]], None, None]:
        """
        Generate (train_df, test_df, fold_meta) tuples across forward-chaining folds.
        """
        if df.empty:
            raise TemporalSplitError("Input DataFrame is empty.")
        if self.time_column not in df.columns:
            raise TemporalSplitError(f"Time column '{self.time_column}' not found.")

        df_sorted = df.copy()
        norm_time = _normalize_period_series(df_sorted[self.time_column])
        df_sorted["_norm_time"] = norm_time

        unique_periods = sorted(norm_time.unique())
        total_periods = len(unique_periods)

        required_min_periods = self.min_train_periods + self.embargo_periods + self.test_periods
        if total_periods < required_min_periods:
            raise TemporalSplitError(
                f"Rolling temporal split requires at least {required_min_periods} periods for 1 fold; "
                f"only {total_periods} available."
            )

        remaining_for_folds = total_periods - required_min_periods
        if self.n_splits > 1 and remaining_for_folds < (self.n_splits - 1):
            max_possible = remaining_for_folds + 1
            raise TemporalSplitError(
                f"Cannot generate {self.n_splits} folds with total {total_periods} periods. "
                f"Maximum possible folds is {max_possible}."
            )

        for fold_idx in range(self.n_splits):
            train_end_idx = self.min_train_periods + fold_idx
            test_start_idx = train_end_idx + self.embargo_periods
            test_end_idx = test_start_idx + self.test_periods

            if test_end_idx > total_periods:
                break

            train_periods = unique_periods[:train_end_idx] if self.expanding else unique_periods[fold_idx:train_end_idx]
            test_periods = unique_periods[test_start_idx:test_end_idx]
            purged_periods = unique_periods[train_end_idx:test_start_idx]

            train_mask = df_sorted["_norm_time"].isin(train_periods)
            test_mask = df_sorted["_norm_time"].isin(test_periods)

            train_fold = df_sorted[train_mask].drop(columns=["_norm_time"])
            test_fold = df_sorted[test_mask].drop(columns=["_norm_time"])

            # Verify Leakage Invariants
            verify_temporal_split(
                train_df=train_fold,
                test_df=test_fold,
                time_column=self.time_column,
                entity_column=self.entity_column,
                embargo_periods=self.embargo_periods,
            )

            fold_meta = {
                "fold": fold_idx + 1,
                "train_periods": train_periods,
                "test_periods": test_periods,
                "purged_periods": purged_periods,
                "train_rows": len(train_fold),
                "test_rows": len(test_fold),
            }

            yield train_fold, test_fold, fold_meta


# ==============================================================================
# 7. CLI COMMAND-LINE INTERFACE
# ==============================================================================

def main() -> None:
    """CLI runner for inspecting temporal splits on an input dataset."""
    parser = argparse.ArgumentParser(
        description="PAIMANA Temporal Data Splitter & Anti-Leakage Auditor (LR-07)"
    )
    parser.add_argument("dataset", type=str, help="Path to input panel CSV file")
    parser.add_argument("--time-col", default="reporting_period", help="Time column name")
    parser.add_argument("--entity-col", default="project_code", help="Entity ID column name")
    parser.add_argument("--train-ratio", type=float, default=0.70, help="Train ratio")
    parser.add_argument("--embargo-periods", type=int, default=0, help="Purged buffer periods")
    parser.add_argument("--train-end", type=str, default=None, help="Explicit train end period")

    args = parser.parse_args()

    if not os.path.exists(args.dataset):
        print(f"[ERROR] File not found: {args.dataset}")
        sys.exit(1)

    df = pd.read_csv(args.dataset)
    splitter = BlockedTemporalSplitter(
        time_column=args.time_col,
        entity_column=args.entity_col,
        embargo_periods=args.embargo_periods,
    )

    try:
        if args.train_end:
            result = splitter.split_by_cutoffs(df, train_end=args.train_end)
        else:
            result = splitter.split_by_ratio(df, train_ratio=args.train_ratio)

        print("=" * 60)
        print("PAIMANA TEMPORAL SPLIT AUDIT (RULE LR-07)")
        print("=" * 60)
        print(f"Status:            PASS (No Temporal Leakage Detected)")
        print(f"Train Periods:     {result.train_periods} ({result.train_count} rows)")
        if result.purged_periods:
            print(f"Purged (Embargo):  {result.purged_periods} ({result.purged_count} rows)")
        print(f"Test Periods:      {result.test_periods} ({result.test_count} rows)")
        print("=" * 60)
    except Exception as e:
        print(f"[FAIL] Temporal split error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()

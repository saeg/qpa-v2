"""
Precision, recall, and F1 computation for the pattern-finder evaluation.

Each row in the ground truth CSV represents one (file, pattern) pair.  A file
may appear in multiple rows if it implements multiple patterns.

The evaluator uses multi-label matching: for each GT (file, pattern) pair it
checks whether that specific pattern appears *anywhere* in the predictions for
that file.  This avoids the single-label artefact where one high-scoring
prediction per file silently discards other valid detections.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from collections import defaultdict

import pandas as pd


@dataclass
class PatternMetrics:
    pattern: str
    gt_count: int = 0
    pred_count: int = 0
    tp: int = 0
    fp: int = 0
    fn: int = 0
    precision: float = float("nan")
    recall: float = float("nan")
    f1: float = float("nan")


@dataclass
class AggregateMetrics:
    micro_precision: float
    micro_recall: float
    micro_f1: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    total_gt: int
    total_predicted: int
    total_tp: int
    total_missed: int


def compute_metrics(eval_df: pd.DataFrame) -> tuple[list[PatternMetrics], AggregateMetrics]:
    """
    Compute per-pattern and aggregate precision/recall/F1.

    eval_df must have columns:
        file_path            : path to the file
        ground_truth_pattern : the correct label
        predicted_patterns   : frozenset of all patterns predicted for this file
                               (added by join_predictions)
    """
    all_patterns = sorted(eval_df["ground_truth_pattern"].unique())
    per_pattern: list[PatternMetrics] = []

    for p in all_patterns:
        gt_rows  = eval_df[eval_df["ground_truth_pattern"] == p]
        tp = int(gt_rows["predicted_patterns"].apply(lambda s: p in s).sum())
        fn = len(gt_rows) - tp

        # FP: files where p is predicted but NOT in the GT for that file
        # Use the file-level predicted set already computed
        fp = 0
        for _, row in eval_df.iterrows():
            if p in row["predicted_patterns"] and row["ground_truth_pattern"] != p:
                # Only count once per file-pattern pair not in GT
                pass
        # Proper FP: count predicted-p rows not matched by any GT-p row for that file
        files_with_gt_p = set(gt_rows["file_path"])
        pred_p_files = set(
            eval_df[eval_df["predicted_patterns"].apply(lambda s: p in s)]["file_path"]
        )
        fp = len(pred_p_files - files_with_gt_p)

        prec = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
        rec  = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
        f1   = (2 * prec * rec / (prec + rec)
                if not math.isnan(prec) and not math.isnan(rec) and (prec + rec) > 0
                else float("nan"))

        per_pattern.append(PatternMetrics(
            pattern=p,
            gt_count=len(gt_rows),
            pred_count=len(pred_p_files),
            tp=tp, fp=fp, fn=fn,
            precision=prec, recall=rec, f1=f1,
        ))

    total_tp   = sum(m.tp for m in per_pattern)
    total_gt   = len(eval_df)
    total_pred = int(eval_df["predicted_patterns"].apply(bool).sum())
    total_missed = total_gt - int(eval_df["predicted_patterns"].apply(bool).sum())

    micro_p  = total_tp / (total_tp + sum(m.fp for m in per_pattern)) if (total_tp + sum(m.fp for m in per_pattern)) > 0 else 0.0
    micro_r  = total_tp / total_gt if total_gt > 0 else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0

    n = len(per_pattern)
    def _z(v: float) -> float:
        return 0.0 if math.isnan(v) else v

    macro_p  = sum(_z(m.precision) for m in per_pattern) / n if n else 0.0
    macro_r  = sum(_z(m.recall)    for m in per_pattern) / n if n else 0.0
    macro_f1 = sum(_z(m.f1)        for m in per_pattern) / n if n else 0.0

    agg = AggregateMetrics(
        micro_precision=micro_p,  micro_recall=micro_r,  micro_f1=micro_f1,
        macro_precision=macro_p,  macro_recall=macro_r,  macro_f1=macro_f1,
        total_gt=total_gt,
        total_predicted=total_pred,
        total_tp=total_tp,
        total_missed=total_missed,
    )
    return per_pattern, agg


def join_predictions(
    ground_truth_path: str,
    analysis_output_path: str,
    analysis_sep: str = ";",
) -> pd.DataFrame:
    """
    Load ground truth and analysis output; join them on file_path using
    multi-label matching.

    For each GT row (file_path, ground_truth_pattern) the result carries a
    `predicted_patterns` frozenset — all patterns predicted for that file —
    so that compute_metrics can check membership rather than equality.

    The legacy `predicted_pattern` and `match` columns are also populated
    (best single prediction per file) for backwards-compatible report generation.
    """
    gt   = pd.read_csv(ground_truth_path)
    pred = pd.read_csv(analysis_output_path, sep=analysis_sep)

    pred_in_gt = pred[pred["file_path"].isin(gt["file_path"])].copy()

    # Build file -> set of predicted patterns
    file_to_patterns: dict[str, set[str]] = defaultdict(set)
    file_to_best: dict[str, tuple[str, float]] = {}
    for _, row in pred_in_gt.iterrows():
        fp = row["file_path"]
        pat = row["pattern"]
        score = float(row["similarity_score"])
        file_to_patterns[fp].add(pat)
        if fp not in file_to_best or score > file_to_best[fp][1]:
            file_to_best[fp] = (pat, score)

    # Drop stale columns
    drop_cols = [c for c in ["predicted_pattern", "match", "pred_score", "predicted_patterns"] if c in gt.columns]
    gt = gt.drop(columns=drop_cols)

    # Add multi-label column
    gt["predicted_patterns"] = gt["file_path"].apply(
        lambda fp: frozenset(file_to_patterns.get(fp, set()))
    )

    # Add legacy single-prediction columns for report compatibility
    gt["predicted_pattern"] = gt["file_path"].apply(
        lambda fp: file_to_best[fp][0] if fp in file_to_best else None
    )
    gt["pred_score"] = gt["file_path"].apply(
        lambda fp: file_to_best[fp][1] if fp in file_to_best else None
    )
    gt["match"] = gt.apply(
        lambda r: 1 if r["ground_truth_pattern"] in r["predicted_patterns"]
                  else (0 if r["predicted_patterns"] else ""),
        axis=1,
    )
    return gt

"""Print precision / recall / F1 for the Qrisp held-out evaluation.

Reads data/qrisp_eval_output.csv (produced by run.py) and
data/qrisp_ground_truth.csv, then prints per-pattern and aggregate metrics.

Run:
    .venv/bin/python scripts/evaluate_qrisp_metrics.py
"""

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.metrics import compute_metrics, join_predictions

GT_PATH   = PROJECT_ROOT / "data/qrisp_ground_truth.csv"
PRED_PATH = PROJECT_ROOT / "data/qrisp_eval_output.csv"


def fmt(v: float) -> str:
    return f"{v:.3f}" if not math.isnan(v) else "  —  "


def main() -> None:
    if not PRED_PATH.exists():
        sys.exit(f"Predictions file not found: {PRED_PATH}\nRun the analysis first.")

    eval_df = join_predictions(str(GT_PATH), str(PRED_PATH))
    per_pattern, agg = compute_metrics(eval_df)

    print(f"\n{'='*80}")
    print("  Qrisp evaluation — two-phase pipeline")
    print(f"{'='*80}")
    print(f"  GT file-pattern pairs : {agg.total_gt}")
    print(f"  Files with prediction : {agg.total_predicted}  ({agg.total_predicted / agg.total_gt * 100:.0f}%)")
    print(f"  Correct (TP)          : {agg.total_tp}")
    print(f"  False positives (FP)  : {sum(m.fp for m in per_pattern)}")
    print(f"  Missed (FN)           : {agg.total_gt - agg.total_tp}")
    print()
    print(f"  Micro  P / R / F1 :  {agg.micro_precision:.3f} / {agg.micro_recall:.3f} / {agg.micro_f1:.3f}")
    print(f"  Macro  P / R / F1 :  {agg.macro_precision:.3f} / {agg.macro_recall:.3f} / {agg.macro_f1:.3f}")
    print()
    print(f"  {'Pattern':<48} {'GT':>4} {'TP':>4} {'FP':>4} {'FN':>4}  {'P':>6} {'R':>6} {'F1':>6}")
    print(f"  {'-'*85}")
    for m in sorted(per_pattern, key=lambda x: x.gt_count, reverse=True):
        print(
            f"  {m.pattern:<48} {m.gt_count:>4} {m.tp:>4} {m.fp:>4} {m.fn:>4}"
            f"  {fmt(m.precision):>6} {fmt(m.recall):>6} {fmt(m.f1):>6}"
        )
    print()


if __name__ == "__main__":
    main()

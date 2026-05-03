"""Grid search over channel thresholds to maximise precision and F1.

Varies `name` and `title` thresholds (the two dominant channels for Qrisp
notebooks) over a dense range, and includes a secondary sweep over `summary`
and `internal_keywords`. All other channels stay at their current baseline.

The keyword veto (if enabled in analysis_config.json) is respected: the script
writes the threshold config but leaves the veto flag as-is, so you can run
the sweep both with and without the veto by flipping it once before running.

Usage:
    .venv/bin/python experiments/threshold_search.py
    .venv/bin/python experiments/threshold_search.py --top 15
    .venv/bin/python experiments/threshold_search.py --output experiments/results/threshold_search.csv

Each combination runs in ~25 s.  The default grid (36 combinations) takes
roughly 15 minutes.
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.metrics import compute_metrics, join_predictions

# ── Paths ──────────────────────────────────────────────────────────────────────
ANALYSIS_CONFIG   = PROJECT_ROOT / "data" / "analysis_config.json"
GT_PATH           = PROJECT_ROOT / "data" / "qrisp_ground_truth.csv"
PRED_PATH         = PROJECT_ROOT / "data" / "qrisp_eval_output.csv"
QRISP_NOTEBOOKS   = PROJECT_ROOT / "converted_notebooks" / "Qrisp"
VENV_PYTHON       = PROJECT_ROOT / ".venv" / "bin" / "python"

# ── Threshold grid ─────────────────────────────────────────────────────────────
# Focus on the two channels that dominate Qrisp results (title, name).
# Secondary channels (summary, internal_keywords) get two candidate values each.
# All other channels are held at their current baseline values.
GRID = {
    "name":               [0.88, 0.90, 0.92, 0.95],
    "title":              [0.70, 0.73, 0.76, 0.78, 0.80, 0.82],
    "summary":            [0.78, 0.82],
    "internal_keywords":  [0.78, 0.82],
}
# Channels whose thresholds are held fixed throughout the sweep.
FIXED = {
    "pattern_desc":      0.70,
    "defined_doc":       0.70,
    "internal_comments": 0.75,
}


def _load_config() -> dict:
    return json.loads(ANALYSIS_CONFIG.read_text())


def _write_config(cfg: dict) -> None:
    ANALYSIS_CONFIG.write_text(json.dumps(cfg, indent=2))


def _run_analysis() -> bool:
    """Run the Qrisp-only analysis. Returns True on success."""
    result = subprocess.run(
        [
            str(VENV_PYTHON), "-m", "src.analysis.run",
            "--target-dir", str(QRISP_NOTEBOOKS),
            "--output",     str(PRED_PATH),
            "--no-report",
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    return result.returncode == 0


def _compute_metrics() -> tuple[float, float, float] | None:
    """Return (micro_precision, micro_recall, micro_f1) or None on failure."""
    try:
        eval_df = join_predictions(str(GT_PATH), str(PRED_PATH))
        _, agg = compute_metrics(eval_df)
        return agg.micro_precision, agg.micro_recall, agg.micro_f1
    except Exception as e:
        print(f"    metrics error: {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=10,
                        help="Number of top combinations to display (default: 10)")
    parser.add_argument("--output", type=str, default=None,
                        help="Optional CSV path to save all results")
    args = parser.parse_args()

    # Build all threshold combinations.
    channels = sorted(GRID.keys())
    value_lists = [GRID[c] for c in channels]
    combos = list(itertools.product(*value_lists))
    total = len(combos)

    print(f"Grid search: {total} combinations")
    print(f"Varying: {', '.join(f'{c}({len(GRID[c])})' for c in channels)}")
    print(f"Fixed:   {', '.join(f'{c}={v}' for c, v in sorted(FIXED.items()))}")
    est_seconds = total * 25
    print(f"Estimated time: ~{est_seconds // 60}m {est_seconds % 60}s\n")

    # Save the original config to restore at the end.
    original_cfg = _load_config()

    results: list[dict] = []

    try:
        for i, values in enumerate(combos, 1):
            thresholds = dict(zip(channels, values))

            # Build the modified config.
            cfg = copy.deepcopy(original_cfg)
            for ch, thr in thresholds.items():
                if ch in cfg["channels"]:
                    cfg["channels"][ch]["threshold"] = thr
            for ch, thr in FIXED.items():
                if ch in cfg["channels"]:
                    cfg["channels"][ch]["threshold"] = thr
            _write_config(cfg)

            label = "  ".join(f"{c}={v:.2f}" for c, v in thresholds.items())
            print(f"[{i:3d}/{total}]  {label}", end="  ", flush=True)

            t0 = time.time()
            ok = _run_analysis()
            elapsed = time.time() - t0

            if not ok:
                print(f"FAILED ({elapsed:.1f}s)")
                continue

            metrics = _compute_metrics()
            if metrics is None:
                print(f"NO METRICS ({elapsed:.1f}s)")
                continue

            p, r, f1 = metrics
            print(f"P={p:.3f}  R={r:.3f}  F1={f1:.3f}  ({elapsed:.1f}s)")
            results.append({"precision": p, "recall": r, "f1": f1, **thresholds})

    finally:
        # Always restore the original config even if the search is interrupted.
        _write_config(original_cfg)
        print("\nOriginal analysis_config.json restored.")

    if not results:
        print("No results collected.")
        return

    # Sort by precision (primary), then F1 (secondary).
    results.sort(key=lambda x: (x["precision"], x["f1"]), reverse=True)

    # Print top N.
    top_n = min(args.top, len(results))
    print(f"\n{'='*80}")
    print(f"  Top {top_n} combinations (sorted by precision then F1)")
    print(f"{'='*80}")
    header = f"{'Rank':>4}  {'P':>6}  {'R':>6}  {'F1':>6}    " + \
             "  ".join(f"{c:>5}" for c in channels)
    print(header)
    print("-" * len(header))
    for rank, row in enumerate(results[:top_n], 1):
        vals = "  ".join(f"{row[c]:.2f}" for c in channels)
        print(f"{rank:4d}  {row['precision']:6.3f}  {row['recall']:6.3f}  {row['f1']:6.3f}    {vals}")

    # Also show the best overall F1.
    best_f1 = max(results, key=lambda x: (x["f1"], x["precision"]))
    print(f"\n  Best F1:  P={best_f1['precision']:.3f}  R={best_f1['recall']:.3f}  "
          f"F1={best_f1['f1']:.3f}  "
          + "  ".join(f"{c}={best_f1[c]:.2f}" for c in channels))

    # Save all results if requested.
    if args.output:
        import csv as _csv
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["precision", "recall", "f1"] + channels
        with open(out, "w", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(results)
        print(f"\nAll results saved to {out}")


if __name__ == "__main__":
    main()

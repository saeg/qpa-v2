"""
evaluate_qrisp.py

Primary evaluation for QPA — Qrisp framework (no KB leakage).

Qrisp is chosen as the primary GT because:
- Framework is completely outside the knowledge base (zero leakage)
- Rich tutorial coverage: BE, GQSP, HHL, Shor, QAOA variants, QPE, Arithmetic
- 24 labeled (file, pattern) entries across diverse algorithms

Outputs:
- Console summary with per-pattern and per-channel FP breakdown
- experiments/results/evaluation_qrisp.md
- experiments/results/evaluation_qrisp.json
"""

import csv
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

RESULTS_CSV = BASE / "data" / "quantum_concept_matches_with_patterns.csv"
QRISP_GT    = BASE / "experiments" / "qrisp_manual_labels.csv"
REPORT_PATH = BASE / "experiments" / "results" / "evaluation_qrisp.md"
METRICS_JSON = BASE / "experiments" / "results" / "evaluation_qrisp.json"


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_gt(path: Path) -> set[tuple[str, str]]:
    gt: set[tuple[str, str]] = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pat = row["Pattern Match"].strip()
            if pat:
                gt.add((row["File Name"].strip(), pat))
    return gt


def load_predictions(prefix: str) -> set[tuple[str, str]]:
    preds: set[tuple[str, str]] = set()
    with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if row["file_path"].startswith(prefix) and row["pattern"] != "N/A":
                preds.add((row["file_path"].strip(), row["pattern"].strip()))
    return preds


def load_predictions_with_channel(prefix: str) -> dict[tuple[str, str], set[str]]:
    preds: dict[tuple[str, str], set[str]] = {}
    with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if row["file_path"].startswith(prefix) and row["pattern"] != "N/A":
                key = (row["file_path"].strip(), row["pattern"].strip())
                preds.setdefault(key, set()).add(row.get("match_type", "unknown").strip())
    return preds


def metrics(gt: set, pred: set) -> dict:
    tp = len(gt & pred)
    fp = len(pred - gt)
    fn = len(gt - pred)
    p  = tp / (tp + fp) if (tp + fp) else 0.0
    r  = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def per_pattern(gt: set, pred: set) -> dict:
    patterns = {p for _, p in gt} | {p for _, p in pred}
    return {
        pat: metrics(
            {x for x in gt   if x[1] == pat},
            {x for x in pred if x[1] == pat},
        )
        for pat in sorted(patterns)
    }


def channel_breakdown(fp_pairs: set, channel_map: dict) -> Counter:
    counts: Counter = Counter()
    for pair in fp_pairs:
        for ch in channel_map.get(pair, {"unknown"}):
            counts[ch] += 1
    return counts


def fmt(v: float) -> str:
    return f"{v:.3f}"


# ── Main ───────────────────────────────────────────────────────────────────────

def evaluate() -> dict:
    gt   = load_gt(QRISP_GT)
    pred = load_predictions("Qrisp")
    ch   = load_predictions_with_channel("Qrisp")
    fp   = pred - gt
    fn   = gt - pred
    tp   = gt & pred

    return {
        "overall":       metrics(gt, pred),
        "per_pattern":   per_pattern(gt, pred),
        "gt_size":       len(gt),
        "pred_size":     len(pred),
        "tp_pairs":      sorted(tp),
        "fp_pairs":      sorted(fp),
        "fn_pairs":      sorted(fn),
        "fp_by_channel": dict(channel_breakdown(fp, ch)),
        "channel_map":   {str(k): list(v) for k, v in ch.items()},
    }


def write_report(r: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    m = r["overall"]

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# QPA Evaluation — Qrisp (Primary GT)\n\n")
        f.write("> Qrisp is used as the primary evaluation framework: it is completely outside the KB,\n")
        f.write("> ensuring zero leakage between training data and evaluation target.\n\n")

        f.write("## Overall\n\n")
        f.write(f"| GT | Pred | TP | FP | FN | Precision | Recall | F1 |\n")
        f.write(f"| --- | --- | --- | --- | --- | --- | --- | --- |\n")
        f.write(f"| {r['gt_size']} | {r['pred_size']} | {m['tp']} | {m['fp']} | {m['fn']} | "
                f"{fmt(m['precision'])} | {fmt(m['recall'])} | {fmt(m['f1'])} |\n\n")

        # FP by channel
        f.write("## FP Breakdown by Matching Channel\n\n")
        f.write("| Channel | FP count |\n| --- | --- |\n")
        ALL_CHANNELS = ["name", "keyword_name", "keyword_comment", "caller", "title", "summary", "pattern_desc"]
        fbc = r["fp_by_channel"]
        for ch in ALL_CHANNELS:
            n = fbc.get(ch, 0)
            if n:
                f.write(f"| {ch} | {n} |\n")
        f.write("\n")

        # Per-pattern table
        f.write("## Per-Pattern Results\n\n")
        f.write("| Pattern | GT | Pred | TP | Precision | Recall | F1 |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        gt_patterns = {p for _, p in load_gt(QRISP_GT)}
        for pat, pm in sorted(r["per_pattern"].items(), key=lambda x: -x[1]["f1"]):
            if pat in gt_patterns or pm["tp"] > 0:
                gt_n = pm["tp"] + pm["fn"]
                pr_n = pm["tp"] + pm["fp"]
                f.write(f"| {pat} | {gt_n} | {pr_n} | {pm['tp']} | "
                        f"{fmt(pm['precision'])} | {fmt(pm['recall'])} | {fmt(pm['f1'])} |\n")
        f.write("\n")

        # TP / FP / FN detail
        f.write("## True Positives\n\n")
        for fp_path, pat in r["tp_pairs"]:
            f.write(f"- `{Path(fp_path).name}` → {pat}\n")

        f.write("\n## False Positives (predicted, not in GT)\n\n")
        for fp_path, pat in r["fp_pairs"]:
            channels = r["channel_map"].get(str((fp_path, pat)), [])
            f.write(f"- `{Path(fp_path).name}` → {pat}  _{', '.join(channels)}_\n")

        f.write("\n## False Negatives (GT has, tool missed)\n\n")
        for fn_path, pat in r["fn_pairs"]:
            f.write(f"- `{Path(fn_path).name}` → {pat}\n")

    print(f"Report saved to {REPORT_PATH}")


def main() -> None:
    r = evaluate()
    m = r["overall"]

    print("=== Qrisp Evaluation (primary GT, zero leakage) ===\n")
    print(f"GT={r['gt_size']}  Pred={r['pred_size']}  TP={m['tp']}  FP={m['fp']}  FN={m['fn']}")
    print(f"Precision={m['precision']:.3f}  Recall={m['recall']:.3f}  F1={m['f1']:.3f}\n")

    print("FP by channel:")
    for ch, n in sorted(r["fp_by_channel"].items(), key=lambda x: -x[1]):
        print(f"  {ch}: {n}")

    print("\nPer-pattern:")
    gt_patterns = {p for _, p in load_gt(QRISP_GT)}
    for pat, pm in sorted(r["per_pattern"].items(), key=lambda x: -x[1]["f1"]):
        if pat in gt_patterns or pm["tp"] > 0:
            print(f"  {pat:<45} GT={pm['tp']+pm['fn']}  P={pm['precision']:.3f}  R={pm['recall']:.3f}  F1={pm['f1']:.3f}")

    # Save JSON
    METRICS_JSON.parent.mkdir(parents=True, exist_ok=True)
    safe = {k: v for k, v in r.items() if k not in ("tp_pairs", "fp_pairs", "fn_pairs", "channel_map")}
    with open(METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(safe, f, indent=2)

    write_report(r)


if __name__ == "__main__":
    main()

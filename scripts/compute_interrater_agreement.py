"""Compute inter-rater agreement statistics from kappa_validation_final.xlsx.

Covers three evaluation sheets:
  - Qiskit Algorithms  (single-label, 39 concepts)
  - Qiskit ML          (single-label, 31 concepts)
  - Qrisp GT           (multi-label, 22 notebooks)

For single-label sheets the script computes:
  - Pairwise Cohen's kappa between every pair of raters
  - Light's kappa  (mean of pairwise kappas)
  - Fleiss' kappa  (multi-rater)
  - Exact full-agreement count

For the multi-label Qrisp GT sheet the script computes:
  - Per-pattern binary Cohen's kappa (one binary classifier per pattern)
  - Mean per-label Light's kappa
  - Exact set-match rates for each rater pair

Run:
    .venv/bin/python scripts/compute_interrater_agreement.py
    .venv/bin/python scripts/compute_interrater_agreement.py --file data/kappa_validation_final.xlsx
"""

from __future__ import annotations

import argparse
import math
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE  = PROJECT_ROOT / "data/kappa_validation_final.xlsx"

SINGLE_LABEL_SHEETS = ["Qiskit Algorithms", "Qiskit ML"]
MULTI_LABEL_SHEET   = "Qrisp GT"


# ── Kappa helpers ──────────────────────────────────────────────────────────────

def _cohen_kappa(a: list, b: list) -> float:
    """Pairwise Cohen's kappa, suppressing sklearn single-class warnings."""
    from sklearn.metrics import cohen_kappa_score
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if not pairs:
        return float("nan")
    xs, ys = zip(*pairs)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            return cohen_kappa_score(xs, ys)
        except Exception:
            return float("nan")


def _fleiss_kappa(rating_matrix: list[list]) -> float:
    """Fleiss' kappa for an (n_subjects x n_raters) matrix of category labels."""
    cats = sorted({v for row in rating_matrix for v in row if v is not None})
    if not cats:
        return float("nan")
    cat_idx = {c: i for i, c in enumerate(cats)}
    n_cats = len(cats)
    n_mat = np.zeros((len(rating_matrix), n_cats))
    for i, row in enumerate(rating_matrix):
        for v in row:
            if v is not None and v in cat_idx:
                n_mat[i, cat_idx[v]] += 1
    valid = n_mat.sum(axis=1) > 1
    n_mat = n_mat[valid]
    if n_mat.size == 0:
        return float("nan")
    n_i   = n_mat.sum(axis=1)
    N     = n_mat.sum()
    p_j   = n_mat.sum(axis=0) / N
    P_e   = (p_j ** 2).sum()
    if P_e == 1:
        return float("nan")
    P_o = ((n_mat * (n_mat - 1)).sum(axis=1) / (n_i * (n_i - 1))).mean()
    return (P_o - P_e) / (1 - P_e)


def _nanmean(vals: list[float]) -> float:
    clean = [v for v in vals if not math.isnan(v)]
    return sum(clean) / len(clean) if clean else float("nan")


def _fmt(v: float) -> str:
    return f"{v:.4f}" if not math.isnan(v) else "  —  "


# ── Single-label analysis ──────────────────────────────────────────────────────

def analyse_single_label(df: pd.DataFrame, sheet: str) -> None:
    r_cols  = ["Current Pattern", "Rater 1", "Rater 2"]
    r_names = ["Proposer", "Rater 1", "Rater 2"]
    raters  = [[str(v).strip() if pd.notna(v) else None for v in df[c]] for c in r_cols]
    n = len(df)

    print(f"\n{'=' * 70}")
    print(f"  {sheet}  (n={n}, single-label)")
    print(f"{'=' * 70}")

    # Pairwise Cohen's kappa
    pairwise: dict[str, float] = {}
    for (i, ni), (j, nj) in combinations(enumerate(r_names), 2):
        k = _cohen_kappa(raters[i], raters[j])
        pairwise[f"{ni} vs {nj}"] = k
        print(f"    Cohen κ  {ni} vs {nj:<30} = {_fmt(k)}")

    lights_k = _nanmean(list(pairwise.values()))
    fleiss_k = _fleiss_kappa([list(row) for row in zip(*raters)])
    full_agree = sum(
        1 for a, b, c in zip(*raters) if a is not None and a == b == c
    )

    print(f"    Light's κ (avg pairwise)              = {_fmt(lights_k)}")
    print(f"    Fleiss'  κ (multi-rater)              = {_fmt(fleiss_k)}")
    print(f"    Full agreement (all 3 raters)         = {full_agree}/{n}  ({100*full_agree/n:.1f}%)")

    # Disagreements
    disagree = [
        (i, r0, r1, r2)
        for i, (r0, r1, r2) in enumerate(zip(*raters))
        if not (r0 == r1 == r2)
    ]
    if disagree:
        print(f"\n  Disagreements ({len(disagree)}):")
        for idx, r0, r1, r2 in disagree:
            name = str(df.iloc[idx].get("Concept Name", df.iloc[idx].get("File Path", "")))[:60]
            print(f"    #{idx+1:<3} {name}")
            print(f"         Proposer: {r0}  |  R1: {r1}  |  R2: {r2}")


# ── Multi-label analysis (Qrisp GT) ───────────────────────────────────────────

def _parse_patterns(val) -> set[str]:
    if pd.isna(val) or str(val).strip() in ("", "---", "NaN", "nan"):
        return set()
    return {p.strip().lower() for p in str(val).replace(";", ",").split(",") if p.strip()}


def analyse_multi_label(df: pd.DataFrame) -> None:
    r1_col = next(c for c in df.columns if "Rater 1" in str(c))
    r2_col = next(c for c in df.columns if "Rater 2" in str(c))

    proposer = [_parse_patterns(v) for v in df["Current Patterns"]]
    rater1   = [_parse_patterns(v) for v in df[r1_col]]
    rater2   = [_parse_patterns(v) for v in df[r2_col]]
    n = len(df)

    all_labels = sorted({p for s in proposer + rater1 + rater2 for p in s})

    print(f"\n{'=' * 70}")
    print(f"  Qrisp GT  (n={n}, multi-label — per-label binary κ)")
    print(f"{'=' * 70}")
    print(f"\n  {'Label':<50} {'CP_R1':>7} {'CP_R2':>7} {'R1_R2':>7}")
    print(f"  {'-' * 67}")

    cp_r1_vals, cp_r2_vals, r1_r2_vals = [], [], []
    for label in all_labels:
        cp  = [1 if label in s else 0 for s in proposer]
        r1  = [1 if label in s else 0 for s in rater1]
        r2  = [1 if label in s else 0 for s in rater2]
        k_cp_r1 = _cohen_kappa(cp, r1)
        k_cp_r2 = _cohen_kappa(cp, r2)
        k_r1_r2 = _cohen_kappa(r1, r2)
        cp_r1_vals.append(k_cp_r1)
        cp_r2_vals.append(k_cp_r2)
        r1_r2_vals.append(k_r1_r2)
        print(f"  {label:<50} {_fmt(k_cp_r1):>7} {_fmt(k_cp_r2):>7} {_fmt(k_r1_r2):>7}")

    m_cp_r1 = _nanmean(cp_r1_vals)
    m_cp_r2 = _nanmean(cp_r2_vals)
    m_r1_r2 = _nanmean(r1_r2_vals)
    lights_k = _nanmean([m_cp_r1, m_cp_r2, m_r1_r2])

    print(f"\n  {'MEAN':<50} {_fmt(m_cp_r1):>7} {_fmt(m_cp_r2):>7} {_fmt(m_r1_r2):>7}")
    print(f"\n  Light's κ (mean across all pairwise per-label): {_fmt(lights_k)}")

    # Exact set-match rates
    exact_all = sum(1 for p, r1, r2 in zip(proposer, rater1, rater2) if p == r1 == r2)
    exact_pr1 = sum(1 for p, r1 in zip(proposer, rater1) if p == r1)
    exact_pr2 = sum(1 for p, r2 in zip(proposer, rater2) if p == r2)
    exact_r12 = sum(1 for r1, r2 in zip(rater1, rater2) if r1 == r2)
    print(f"\n  Exact set match — all 3 agree:   {exact_all}/{n} ({100*exact_all/n:.1f}%)")
    print(f"  Exact set match — Proposer vs R1: {exact_pr1}/{n} ({100*exact_pr1/n:.1f}%)")
    print(f"  Exact set match — Proposer vs R2: {exact_pr2}/{n} ({100*exact_pr2/n:.1f}%)")
    print(f"  Exact set match — R1 vs R2:       {exact_r12}/{n} ({100*exact_r12/n:.1f}%)")

    # Item-by-item detail
    print(f"\n  Item-by-item comparison:")
    print(f"  {'#':<4} {'Proposer':<45} {'R1':<35} {'R2':<35} Status")
    print(f"  {'-' * 130}")
    for i, (fp, p, r1, r2) in enumerate(zip(df.get("File Path", df.index), proposer, rater1, rater2), 1):
        fname = Path(str(fp)).name[:40] if pd.notna(fp) else f"#{i}"
        status = "ALL" if p == r1 == r2 else ("R1=R2" if r1 == r2 else ("CP=R1" if p == r1 else ("CP=R2" if p == r2 else "DISAGREE")))
        pp = ", ".join(sorted(p))[:43] or "(none)"
        rr1 = ", ".join(sorted(r1))[:33] or "(none)"
        rr2 = ", ".join(sorted(r2))[:33] or "(none)"
        print(f"  {i:<4} {pp:<45} {rr1:<35} {rr2:<35} {status}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", type=Path, default=DEFAULT_FILE,
                   help="Path to the kappa validation Excel file.")
    args = p.parse_args()

    if not args.file.exists():
        raise SystemExit(f"File not found: {args.file}")

    print(f"Reading: {args.file}")
    xl = pd.ExcelFile(args.file)

    for sheet in SINGLE_LABEL_SHEETS:
        if sheet in xl.sheet_names:
            analyse_single_label(xl.parse(sheet), sheet)
        else:
            print(f"\n  [SKIP] Sheet '{sheet}' not found.")

    if MULTI_LABEL_SHEET in xl.sheet_names:
        analyse_multi_label(xl.parse(MULTI_LABEL_SHEET))
    else:
        print(f"\n  [SKIP] Sheet '{MULTI_LABEL_SHEET}' not found.")

    print()


if __name__ == "__main__":
    main()

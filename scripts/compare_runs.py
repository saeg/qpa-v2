"""
Compare two archived analysis runs.

Each run is stored under ``data/runs/<run_id>/`` by ``run_analysis.py`` and
contains:
  - ``matches.csv``        — full output CSV
  - ``summary.json``       — counts, pattern frequencies, channel breakdown
  - ``channel_config.json``— active channel toggles + thresholds

This script prints a structured diff of two runs: pattern frequency changes,
channel-mix changes, files added/removed, and the channel-config diff.

Usage:
    # Compare the latest run against the run before it
    uv run python scripts/compare_runs.py

    # Compare two specific runs (full IDs or any unique prefix)
    uv run python scripts/compare_runs.py 20260426_063500_a1b2c3 20260426_071000_d4e5f6

    # Compare 'latest' against another
    uv run python scripts/compare_runs.py latest 20260426_063500_a1b2c3

    # List available runs and exit
    uv run python scripts/compare_runs.py --list
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "data" / "runs"


def _list_runs() -> list[Path]:
    if not RUNS_DIR.exists():
        return []
    return sorted(
        [p for p in RUNS_DIR.iterdir() if p.is_dir() and not p.is_symlink()],
        key=lambda p: p.name,
    )


def _resolve_run_id(token: str) -> Path:
    """Resolve a token (full id, prefix, 'latest', or relative index like '-1') to a run dir."""
    runs = _list_runs()
    if not runs:
        raise SystemExit(f"No runs found in {RUNS_DIR}.  Run 'just run_main' first.")

    if token in ("latest", "current"):
        return runs[-1]
    if token in ("previous", "prev"):
        if len(runs) < 2:
            raise SystemExit("Only one run archived — cannot resolve 'previous'.")
        return runs[-2]
    if token.startswith("-") and token[1:].isdigit():
        idx = int(token)
        if abs(idx) > len(runs):
            raise SystemExit(f"Index {token} out of range (have {len(runs)} runs).")
        return runs[idx]

    matches = [r for r in runs if r.name.startswith(token)]
    if len(matches) == 0:
        raise SystemExit(f"No run matches '{token}'.  Use --list to see available IDs.")
    if len(matches) > 1:
        raise SystemExit(
            f"Ambiguous prefix '{token}' matches: {[m.name for m in matches]}"
        )
    return matches[0]


def _load_summary(run_dir: Path) -> dict:
    summary_file = run_dir / "summary.json"
    if not summary_file.exists():
        raise SystemExit(f"Missing summary.json in {run_dir}")
    with open(summary_file, encoding="utf-8") as f:
        return json.load(f)


def _load_pairs(run_dir: Path) -> set[tuple[str, str]]:
    pairs = set()
    csv_file = run_dir / "matches.csv"
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            pairs.add((row["file_path"], row["pattern"]))
    return pairs


def _diff_dict(old: dict, new: dict) -> list[tuple]:
    """Return [(key, old_val, new_val)] for keys that differ.  Missing → None."""
    keys = sorted(set(old) | set(new))
    out = []
    for k in keys:
        if old.get(k) != new.get(k):
            out.append((k, old.get(k), new.get(k)))
    return out


def _print_section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def compare(old_run: Path, new_run: Path) -> None:
    old_summary = _load_summary(old_run)
    new_summary = _load_summary(new_run)

    print(f"Comparing")
    print(f"  OLD: {old_run.name}    ({old_summary.get('timestamp', '')})")
    print(f"  NEW: {new_run.name}    ({new_summary.get('timestamp', '')})")

    # ── Top-level counts ──────────────────────────────────────────────────────
    _print_section("Counts")
    fields = [
        ("files_scanned", "Files scanned"),
        ("files_matched", "Files with matches"),
        ("projects_matched", "Projects matched"),
        ("unique_file_pattern_pairs", "Unique file-pattern pairs"),
        ("raw_rows", "Raw rows (incl. multiple channels per pair)"),
    ]
    print(f"{'Field':45s} {'OLD':>10s} {'NEW':>10s} {'Δ':>10s}")
    for k, label in fields:
        o = old_summary.get(k, 0) or 0
        n = new_summary.get(k, 0) or 0
        delta = n - o
        sign = f"{delta:+d}" if delta else "0"
        print(f"  {label:43s} {o:>10d} {n:>10d} {sign:>10s}")

    # ── Pattern frequency diff ────────────────────────────────────────────────
    _print_section("Pattern frequency changes")
    old_p = old_summary.get("pattern_counts", {})
    new_p = new_summary.get("pattern_counts", {})
    all_pats = sorted(set(old_p) | set(new_p), key=lambda p: -max(old_p.get(p, 0), new_p.get(p, 0)))
    print(f"{'Pattern':52s} {'OLD':>6s} {'NEW':>6s} {'Δ':>7s}")
    any_change = False
    for p in all_pats:
        o = old_p.get(p, 0)
        n = new_p.get(p, 0)
        delta = n - o
        marker = "" if delta == 0 else ("**" if abs(delta) >= 5 else "")
        sign = f"{delta:+d}" if delta else "0"
        print(f"  {p[:50]:50s} {o:>6d} {n:>6d} {sign:>7s} {marker}")
        if delta != 0:
            any_change = True
    if not any_change:
        print("  (no changes)")

    # ── Channel breakdown diff ────────────────────────────────────────────────
    _print_section("Channel breakdown (raw row counts)")
    old_c = old_summary.get("channel_counts", {})
    new_c = new_summary.get("channel_counts", {})
    for c in sorted(set(old_c) | set(new_c)):
        o = old_c.get(c, 0)
        n = new_c.get(c, 0)
        delta = n - o
        sign = f"{delta:+d}" if delta else "0"
        print(f"  {c:18s} {o:>6d} → {n:>6d}  ({sign})")

    # ── File-pattern set diff (sample only) ───────────────────────────────────
    _print_section("File-pattern pair set diff")
    old_pairs = _load_pairs(old_run)
    new_pairs = _load_pairs(new_run)
    added = new_pairs - old_pairs
    removed = old_pairs - new_pairs
    print(f"  Pairs added (in NEW only):   {len(added)}")
    print(f"  Pairs removed (in OLD only): {len(removed)}")

    def _sample(pairs: set, label: str, n: int = 10) -> None:
        if not pairs:
            return
        print(f"\n  Sample {label} (up to {n}):")
        for fp, pat in sorted(pairs)[:n]:
            print(f"    [{pat[:35]:35s}] {fp[:80]}")

    _sample(removed, "REMOVED pairs")
    _sample(added, "ADDED pairs")

    # ── Channel config diff ───────────────────────────────────────────────────
    _print_section("Channel config diff")
    old_cfg = old_summary.get("channel_config", {})
    new_cfg = new_summary.get("channel_config", {})
    cfg_diffs = []
    for ch in sorted(set(old_cfg) | set(new_cfg)):
        o = old_cfg.get(ch, {})
        n = new_cfg.get(ch, {})
        # Skip non-channel scalar keys (e.g. labels)
        if not isinstance(o, dict) or not isinstance(n, dict):
            if o != n:
                cfg_diffs.append((ch, "(value)", o, n))
            continue
        for k, ov, nv in _diff_dict(o, n):
            cfg_diffs.append((ch, k, ov, nv))
    if not cfg_diffs:
        print("  (no config differences)")
    for ch, k, ov, nv in cfg_diffs:
        print(f"  {ch}.{k}: {ov!r} → {nv!r}")

    # ── Git SHA ───────────────────────────────────────────────────────────────
    _print_section("Code version")
    print(f"  OLD git SHA: {old_summary.get('git_sha')}")
    print(f"  NEW git SHA: {new_summary.get('git_sha')}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("old", nargs="?", default="previous",
                        help="Old run id, prefix, 'previous', 'latest', or '-N' (default: previous)")
    parser.add_argument("new", nargs="?", default="latest",
                        help="New run id, prefix, 'latest', or '-N' (default: latest)")
    parser.add_argument("--list", action="store_true",
                        help="List available run ids and exit.")
    args = parser.parse_args()

    if args.list:
        runs = _list_runs()
        if not runs:
            print(f"No runs found in {RUNS_DIR}")
            return
        print(f"Available runs in {RUNS_DIR}:")
        for r in runs:
            try:
                s = json.loads((r / "summary.json").read_text())
                pairs = s.get("unique_file_pattern_pairs", "?")
                files = s.get("files_matched", "?")
                disabled = [
                    c for c, v in s.get("channel_config", {}).items()
                    if isinstance(v, dict) and not v.get("enabled")
                ]
                disabled_str = f" disabled={disabled}" if disabled else ""
                print(f"  {r.name}   pairs={pairs}  files={files}{disabled_str}")
            except Exception:
                print(f"  {r.name}   (no readable summary)")
        return

    old_run = _resolve_run_id(args.old)
    new_run = _resolve_run_id(args.new)
    if old_run == new_run:
        raise SystemExit(f"OLD and NEW resolve to the same run: {old_run.name}")
    compare(old_run, new_run)


if __name__ == "__main__":
    main()

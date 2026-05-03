"""
qrisp_execution_trace.py

Downloads 5 Qrisp tutorial notebooks from GitHub, executes them in an
isolated environment, and records the sequence of Qrisp API calls related to
quantum concepts or patterns.

Each notebook runs via `uv run --with qrisp`, so no manual venv setup is
needed.  uv caches the qrisp install, so repeated runs skip the download.
Notebooks are executed in parallel using a thread pool.

Output: experiments/results/qrisp_trace/  (one JSON + one text per notebook)

Usage:
    python experiments/qrisp_execution_trace.py [--workers N]
    just trace-qrisp
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import textwrap
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# ── Configuration ──────────────────────────────────────────────────────────────

BASE = Path(__file__).resolve().parent.parent

# Five tutorial notebooks covering diverse patterns.
# (name, github_raw_url, expected_patterns)
NOTEBOOKS = [
    (
        "BE_vol1",
        "https://raw.githubusercontent.com/eclipse-qrisp/Qrisp/main/"
        "documentation/source/general/tutorial/BE_tutorial/BE_vol1.ipynb",
        ["Linear Combination of Unitaries"],
    ),
    (
        "MaxCut",
        "https://raw.githubusercontent.com/eclipse-qrisp/Qrisp/main/"
        "documentation/source/general/tutorial/QAOAtutorial/MaxCut.ipynb",
        ["Quantum Approximate Optimization Algorithm (QAOA)"],
    ),
    (
        "HHL",
        "https://raw.githubusercontent.com/eclipse-qrisp/Qrisp/main/"
        "documentation/source/general/tutorial/HHL.ipynb",
        ["Linear Combination of Unitaries"],
    ),
    (
        "Shor",
        "https://raw.githubusercontent.com/eclipse-qrisp/Qrisp/main/"
        "documentation/source/general/tutorial/Shor.ipynb",
        ["Quantum Phase Estimation (QPE)", "Quantum Arithmetic"],
    ),
    (
        "GQSP_filtering",
        "https://raw.githubusercontent.com/eclipse-qrisp/Qrisp/main/"
        "documentation/source/general/tutorial/GQSP_filtering.ipynb",
        ["Linear Combination of Unitaries"],
    ),
]

RESULTS_DIR = BASE / "experiments" / "results" / "qrisp_trace"
GT_CSV = BASE / "data" / "qrisp_ground_truth_full.csv"

# uv command that provides an isolated qrisp environment.
# uv caches the install, so the first run downloads qrisp and subsequent
# runs reuse the cached layer.
UV_RUN = ["uv", "run", "--with", "qrisp"]

# Per-notebook execution timeout in seconds.
CELL_TIMEOUT = 60

# Qrisp sub-module fragments that indicate quantum operations.
QUANTUM_MODULE_FRAGMENTS = [
    "alg_primitives",
    "algorithms",
    "circuit.standard_operations",
    "circuit.library",
    "qtypes",
    "environments",
    "grover",
    "qaoa",
    "vqe",
    "hhl",
    "shor",
    "qft",
    "qpe",
    "amplitude",
]

# Function names that are always excluded (noise).
EXCLUDED_NAMES = {
    "__init__", "__new__", "__repr__", "__str__", "__eq__", "__hash__",
    "__len__", "__iter__", "__next__", "__getitem__", "__setitem__",
    "__contains__", "__class_getitem__", "__init_subclass__",
    "copy", "deepcopy",
}

# Lock used to prevent interleaved console output from parallel workers.
_print_lock = threading.Lock()


def _progress(name: str, msg: str) -> None:
    """Prints a single prefixed progress line immediately, safe for concurrent use."""
    with _print_lock:
        print(f"  [{name}] {msg}", flush=True)


# ── Quantum concept set from ground truth ─────────────────────────────────────

def load_quantum_concepts() -> set[str]:
    """Returns the set of known quantum function/class names from the GT CSV."""
    concepts: set[str] = set()
    if not GT_CSV.exists():
        return concepts
    with GT_CSV.open(encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                concepts.add(parts[1].strip())
    return concepts


QUANTUM_CONCEPTS: set[str] = load_quantum_concepts()


# ── Notebook download ──────────────────────────────────────────────────────────

def download_notebook(url: str) -> dict[str, Any]:
    """Downloads a .ipynb file and returns the parsed JSON."""
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ── Script assembly ────────────────────────────────────────────────────────────

TRACER_HEADER = textwrap.dedent("""\
    import sys as _trace_sys
    import json as _trace_json

    _call_log = []          # [(cell_idx, module_func)]
    _current_cell = [0]

    def _qrisp_tracer(frame, event, arg):
        if event != 'call':
            return _qrisp_tracer
        mod = frame.f_globals.get('__name__', '') or ''
        if not mod.startswith('qrisp'):
            return _qrisp_tracer
        fn = frame.f_code.co_name
        if fn.startswith('_'):
            return _qrisp_tracer
        _call_log.append((_current_cell[0], f"{mod}.{fn}"))
        return _qrisp_tracer

    _trace_sys.settrace(_qrisp_tracer)

    # ── notebook cells below ──────────────────────────────────────────────────
""")

TRACER_FOOTER = textwrap.dedent("""\
    # ── end of notebook cells ─────────────────────────────────────────────────
    _trace_sys.settrace(None)
    with open(_TRACE_OUTPUT, 'w', encoding='utf-8') as _f:
        _trace_json.dump(_call_log, _f)
""")

CELL_MARKER = "\n_current_cell[0] += 1\n"


def build_tracer_script(nb: dict[str, Any], trace_path: Path) -> str:
    """Assembles notebook code cells into a single traced Python script."""
    cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]

    cell_blocks: list[str] = []
    for cell in cells:
        src = "".join(cell.get("source", []))
        lines = [ln for ln in src.splitlines() if not ln.strip().startswith(("%", "!", "?"))]
        if not lines:
            continue
        cell_blocks.append("\n".join(lines))

    body = CELL_MARKER.join(cell_blocks)
    return (
        f'_TRACE_OUTPUT = {repr(str(trace_path))}\n'
        + TRACER_HEADER
        + body
        + TRACER_FOOTER
    )


# ── Execution ──────────────────────────────────────────────────────────────────

def run_notebook(
    name: str, script: str, trace_path: Path
) -> tuple[list[tuple[int, str]] | None, int, list[str]]:
    """
    Writes the script to the results dir and runs it via uv run --with qrisp.
    Returns (raw_call_log, returncode, stderr_tail).
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    script_path = RESULTS_DIR / f"{name}_script.py"
    script_path.write_text(script, encoding="utf-8")

    result = subprocess.run(
        [*UV_RUN, "python", str(script_path)],
        capture_output=True,
        text=True,
        timeout=CELL_TIMEOUT * 20,
        cwd=str(BASE),
    )

    stderr_tail = result.stderr.strip().splitlines()[-6:] if result.returncode != 0 else []

    raw = None
    if trace_path.exists():
        with trace_path.open(encoding="utf-8") as f:
            raw = json.load(f)

    return raw, result.returncode, stderr_tail


# ── Filtering ──────────────────────────────────────────────────────────────────

def is_quantum_call(module: str, func: str) -> bool:
    """Returns True if the call is quantum-related."""
    if func in EXCLUDED_NAMES:
        return False
    if func in QUANTUM_CONCEPTS:
        return True
    for fragment in QUANTUM_MODULE_FRAGMENTS:
        if fragment in module:
            return True
    return False


def filter_and_deduplicate(
    raw: list[tuple[int, str]]
) -> list[tuple[int, str, str]]:
    """
    Filters to quantum calls and removes consecutive duplicates.
    Returns list of (cell_idx, module, func_name).
    """
    filtered: list[tuple[int, str, str]] = []
    prev_key: str | None = None

    for cell_idx, entry in raw:
        parts = entry.rsplit(".", 1)
        if len(parts) != 2:
            continue
        mod, func = parts
        if not is_quantum_call(mod, func):
            continue
        if entry == prev_key:
            continue
        filtered.append((cell_idx, mod, func))
        prev_key = entry

    return filtered


# ── Per-notebook task ──────────────────────────────────────────────────────────

def process_notebook(
    name: str, url: str, expected_patterns: list[str]
) -> list[str]:
    """
    Full pipeline for one notebook.  Progress lines are printed immediately
    via _progress().  The detailed sequence is returned as lines so main()
    can flush the final summaries in order once all notebooks finish.
    """
    _progress(name, "downloading...")
    try:
        nb = download_notebook(url)
    except Exception as exc:
        _progress(name, f"ERROR — download failed: {exc}")
        write_results(name, url, expected_patterns, None, 0)
        return [f"\n  {name}  [ERROR]\n  Download failed: {exc}"]

    trace_path = RESULTS_DIR / f"{name}_raw_calls.json"
    script = build_tracer_script(nb, trace_path)
    n_cells = sum(1 for c in nb.get("cells", []) if c.get("cell_type") == "code")

    _progress(name, f"running ({n_cells} cells)…")
    raw: list[tuple[int, str]] | None = None
    try:
        raw, returncode, stderr_tail = run_notebook(name, script, trace_path)
        if returncode != 0:
            _progress(name, f"WARN — exited {returncode}")
    except subprocess.TimeoutExpired:
        _progress(name, "WARN — timed out")
    except Exception as exc:
        _progress(name, f"ERROR — {exc}")

    raw_count = len(raw) if raw else 0
    filtered = filter_and_deduplicate(raw) if raw else None
    q_count = len(filtered) if filtered else 0
    status = "OK" if filtered else "no quantum calls"
    _progress(name, f"done — {raw_count} raw calls, {q_count} quantum  [{status}]")

    write_results(name, url, expected_patterns, filtered, raw_count)

    # Build the detailed summary block returned for end-of-run printing.
    sep = "=" * 60
    out: list[str] = [f"\n{sep}", f"  {name}  [{status}]",
                      f"  Expected:  {', '.join(expected_patterns)}",
                      f"  Raw qrisp calls: {raw_count}   Quantum (filtered): {q_count}"]
    if filtered:
        out.append("  Execution sequence:")
        prev_cell = -1
        for i, (cell, mod, fn) in enumerate(filtered, 1):
            if cell != prev_cell:
                out.append(f"    ── Cell {cell} ──")
                prev_cell = cell
            out.append(f"    {i:3d}.  {fn:<40}  {mod.replace('qrisp.', '')}")
    else:
        out.append("  (no quantum calls captured)")
    return out


# ── Reporting ──────────────────────────────────────────────────────────────────

def write_results(
    name: str,
    url: str,
    expected_patterns: list[str],
    filtered: list[tuple[int, str, str]] | None,
    raw_count: int,
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "notebook": name,
        "url": url,
        "expected_patterns": expected_patterns,
        "raw_call_count": raw_count,
        "quantum_call_count": len(filtered) if filtered else 0,
        "sequence": [
            {"cell": cell, "module": mod, "function": fn}
            for cell, mod, fn in (filtered or [])
        ],
    }

    with (RESULTS_DIR / f"{name}.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with (RESULTS_DIR / f"{name}.txt").open("w", encoding="utf-8") as f:
        f.write(f"Notebook: {name}\n")
        f.write(f"URL:      {url}\n")
        f.write(f"Expected patterns: {', '.join(expected_patterns)}\n")
        f.write(f"Raw qrisp calls:   {raw_count}\n")
        f.write(f"Quantum calls:     {len(filtered) if filtered else 0}\n")
        f.write("\nExecution sequence (quantum-related calls only):\n")
        f.write("-" * 60 + "\n")
        if not filtered:
            f.write("  (no quantum calls captured)\n")
        else:
            prev_cell = -1
            for i, (cell, mod, fn) in enumerate(filtered, 1):
                if cell != prev_cell:
                    f.write(f"\n  [Cell {cell}]\n")
                    prev_cell = cell
                f.write(f"  {i:3d}.  {fn}  ({mod.replace('qrisp.', '')})\n")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Trace Qrisp notebook execution.")
    parser.add_argument(
        "--workers", type=int, default=len(NOTEBOOKS),
        help=f"Number of parallel workers (default: {len(NOTEBOOKS)}, one per notebook).",
    )
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Qrisp Execution Trace ===")
    print(f"Quantum concepts loaded: {len(QUANTUM_CONCEPTS)} names from ground truth")
    print(f"Runner:  {' '.join(UV_RUN)} python <script>")
    print(f"Workers: {args.workers}  Notebooks: {len(NOTEBOOKS)}\n")

    # Map future → (name, url, expected_patterns) to preserve submission order.
    ordered: list[tuple[str, str, list[str]]] = list(NOTEBOOKS)
    future_to_idx: dict[Any, int] = {}
    results: dict[int, list[str]] = {}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, (name, url, expected_patterns) in enumerate(ordered):
            future = pool.submit(process_notebook, name, url, expected_patterns)
            future_to_idx[future] = i

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                name = ordered[idx][0]
                results[idx] = [f"\n  {name}  [unexpected error: {exc}]"]

    # Print detailed summaries in original notebook order.
    print("\n" + "=" * 60)
    print("  SUMMARIES")
    for i in range(len(ordered)):
        with _print_lock:
            sys.stdout.write("\n".join(results[i]) + "\n")
            sys.stdout.flush()

    print(f"\nResults saved to {RESULTS_DIR}")


if __name__ == "__main__":
    main()

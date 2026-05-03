"""Build a minimal Qrisp KB from function/class names in the algorithm directories.

Two sources of names:
1. High-confidence name-channel matches from a prior source-code analysis run
   (qrisp_source_matches.csv, score >= MIN_SCORE). These were validated by
   the embedding model.
2. Targeted directory scan: key Qrisp algorithm dirs are mapped to patterns
   by their directory structure (which is authoritative). This captures names
   like grovers_alg, QAE, LCU that the embedding may score < MIN_SCORE.

Output:
    data/qrisp_quantum_concepts.json
    data/knowledge_base/enriched_qrisp_quantum_patterns.csv

Run:
    .venv/bin/python scripts/build_qrisp_name_kb.py
"""

from __future__ import annotations

import ast
import csv
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QRISP_SRC    = PROJECT_ROOT / "target_github_projects/Qrisp/src/qrisp"
MATCHES_CSV  = PROJECT_ROOT / "data/qrisp_source_matches.csv"
OUT_JSON     = PROJECT_ROOT / "data/dynamic_kb/Qrisp/concepts.json"
OUT_CSV      = PROJECT_ROOT / "data/dynamic_kb/Qrisp/patterns.csv"

# Minimum score for names taken from the prior analysis run.
MIN_SCORE = 0.90

# Patterns outside the 22-pattern evaluation set that may appear in source
# matches; these are filtered out so they don't add noise to the KB.
KNOWN_PATTERNS = {
    "Amplitude Amplification",
    "Basis Change",
    "Circuit Construction Utility",
    "Creating Entanglement",
    "Data Encoding",
    "Domain Specific Application",
    "Dynamic Circuit",
    "Function Table",
    "Grover",
    "Hamiltonian Simulation",
    "Initialization",
    "Linear Combination of Unitaries",
    "Oracle",
    "Quantum Amplitude Estimation",
    "Quantum Approximate Optimization Algorithm (QAOA)",
    "Quantum Arithmetic",
    "Quantum Logical Operators",
    "Quantum Neural Network (QNN)",
    "Quantum Phase Estimation (QPE)",
    "SWAP Test",
    "Variational Quantum Algorithm (VQA)",
    "Variational Quantum Eigensolver (VQE)",
}

# Directory-based pattern assignments for targeted extraction.
# Map: (relative_path_glob, pattern).  Paths are relative to QRISP_SRC.
# Only top-level public names (no leading underscore) are promoted.
DIR_PATTERN_MAP: list[tuple[str, str]] = [
    # Core algorithm implementations
    ("alg_primitives/amplitude_amplification.py", "Amplitude Amplification"),
    ("alg_primitives/reflection.py",              "Amplitude Amplification"),
    ("alg_primitives/qft.py",                     "Basis Change"),
    ("alg_primitives/qpe.py",                     "Quantum Phase Estimation (QPE)"),
    ("alg_primitives/iterative_qpe.py",            "Quantum Phase Estimation (QPE)"),
    ("alg_primitives/qae.py",                     "Quantum Amplitude Estimation"),
    ("alg_primitives/iterative_qae.py",            "Quantum Amplitude Estimation"),
    ("alg_primitives/lcu.py",                     "Linear Combination of Unitaries"),
    ("alg_primitives/state_preparation/*.py",     "Initialization"),
    ("alg_primitives/dicke_state_prep.py",        "Initialization"),
    ("algorithms/grover/grover_tools.py",          "Grover"),
    ("algorithms/qaoa/qaoa_problem.py",            "Quantum Approximate Optimization Algorithm (QAOA)"),
    ("algorithms/qaoa/problems/*.py",              "Quantum Approximate Optimization Algorithm (QAOA)"),
    ("algorithms/vqe/vqe_problem.py",              "Variational Quantum Eigensolver (VQE)"),
    ("algorithms/gqsp/hamiltonian_simulation.py",  "Hamiltonian Simulation"),
]

# Utility / internal names to exclude from the KB even if they appear in the
# directories above.  These are too generic and would fire on unrelated code.
EXCLUDED_NAMES = {
    "main", "test", "run", "helper", "util", "utils",
    "prepare_qiskit",  # wraps Qiskit state prep, not Qrisp-native
}


def is_public(name: str) -> bool:
    return bool(name) and not name.startswith("_") and name not in EXCLUDED_NAMES


def extract_top_level_names(py_path: Path) -> list[str]:
    """Return public top-level function and class names from a Python file."""
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, OSError):
        return []
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and is_public(node.name)
    ]


def names_from_dir_map() -> dict[str, str]:
    """Return {name: pattern} from the directory-based mapping."""
    name_pattern: dict[str, str] = {}
    for glob_path, pattern in DIR_PATTERN_MAP:
        for py in QRISP_SRC.glob(glob_path):
            for name in extract_top_level_names(py):
                if name not in name_pattern:
                    name_pattern[name] = pattern
    return name_pattern


def names_from_source_matches(min_score: float) -> dict[str, str]:
    """Return {name: pattern} from high-confidence embedding matches."""
    if not MATCHES_CSV.exists():
        print(f"  WARN: {MATCHES_CSV} not found — skipping embedding matches.")
        return {}
    name_pattern: dict[str, str] = {}
    with open(MATCHES_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if row["match_type"] != "name":
                continue
            score = float(row["similarity_score"])
            if score < min_score:
                continue
            pattern = row["pattern"]
            if pattern not in KNOWN_PATTERNS:
                continue
            name = row["matched_text"].strip()
            if not name or not is_public(name):
                continue
            if name not in name_pattern:
                name_pattern[name] = pattern
    return name_pattern


def build_kb(combined: dict[str, str]) -> tuple[list[dict], list[dict]]:
    """Produce JSON entries and CSV rows from {name: pattern}."""
    json_entries: list[dict] = []
    csv_rows: list[dict] = []
    for name, pattern in sorted(combined.items()):
        # Use the standard /dynamic/{project}/{fn} path format so per-project
        # KB scoping in run.py correctly limits Qrisp KB to Qrisp files only.
        full_path = f"/dynamic/Qrisp/{name}"
        json_entries.append({
            "name": full_path,
            "summary": f"{name}: Qrisp implementation of the {pattern} pattern.",
            "docstring": "",
            "type": "Function",
            "is_target_subclass": False,
            "base_classes": [],
            "internal_keywords": "",
            "internal_comments": "",
        })
        csv_rows.append({
            "name": full_path.lstrip("/"),
            "summary": f"{name}: Qrisp implementation of the {pattern} pattern.",
            "pattern": pattern,
        })
    return json_entries, csv_rows


def main() -> None:
    print("Source 1: directory-based mapping...")
    dir_names = names_from_dir_map()
    print(f"  Found {len(dir_names)} names from {len(DIR_PATTERN_MAP)} directory entries.")

    print("Source 2: embedding matches from source analysis (>= {:.2f})...".format(MIN_SCORE))
    emb_names = names_from_source_matches(MIN_SCORE)
    print(f"  Found {len(emb_names)} high-confidence names.")

    # Merge: dir-map takes precedence (more authoritative), embedding fills gaps.
    combined = {**emb_names, **dir_names}
    print(f"\nCombined unique names: {len(combined)}")

    by_pattern: dict[str, list[str]] = {}
    for name, pattern in sorted(combined.items()):
        by_pattern.setdefault(pattern, []).append(name)
    for pattern, names in sorted(by_pattern.items()):
        print(f"  {pattern}: {', '.join(sorted(names))}")

    json_entries, csv_rows = build_kb(combined)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(json_entries, f, indent=2)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "summary", "pattern"])
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\nWrote: {OUT_JSON}  ({len(json_entries)} entries)")
    print(f"Wrote: {OUT_CSV}")


if __name__ == "__main__":
    main()

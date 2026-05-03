"""
extract_qpanda.py

Extract quantum concepts from QPanda-2 and build KB entries.

Sources:
  1. pybind11 C++ binding files (pyQPandaCpp/) — regex-parsed m.def / py::class_
  2. Python algorithm files (pyQPanda/pyqpanda/Algorithm/) — AST-parsed

Outputs:
  data/qpanda_quantum_concepts.json
  data/knowledge_base/enriched_qpanda_quantum_patterns.csv
"""

import ast
import csv
import json
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

REPO_ROOT = Path(__file__).resolve().parents[3] / "target_github_projects" / "QPanda-2"
OUT_DIR = Path(__file__).resolve().parents[3] / "data"

JSON_OUT = OUT_DIR / "qpanda_quantum_concepts.json"
CSV_OUT  = OUT_DIR / "knowledge_base" / "enriched_qpanda_quantum_patterns.csv"

# ── Pybind11 binding files to parse ──────────────────────────────────────────

BINDING_FILES = [
    "pyQPandaCpp/pyQPanda.Core/pyQPanda.qalg.cpp",
    "pyQPandaCpp/pyQPanda.Core/pyqpanda.hamiltoniansimulation.cpp",
    "pyQPandaCpp/pyQPanda.Core/pyqpanda.variational.cpp",
]

# ── Python algorithm source files to parse ───────────────────────────────────

PYTHON_DIRS = [
    "pyQPanda/pyqpanda/Algorithm",
    "pyQPanda/pyqpanda/Variational",
]

# ── Pattern assignment: keyword → pattern (checked against name + docstring) ─

_PATTERN_RULES: list[tuple[list[str], str]] = [
    (["grover", "grover_search", "quantumwalkgrover"],                        "Grover"),
    (["amplitude_amplif", "diffusion_operator"],                              "Amplitude Amplification"),
    (["quantum_walk_alg", "quantum_walk_search"],                             "Grover"),
    (["shor_factorization", "shor factoring"],                                "Grover"),
    (["qft", "quantum fourier transform", "quantum_fourier"],                 "Basis Change"),
    (["qpe", "quantum_phase_estimation", "phase estimation", "quantumphase"], "Quantum Phase Estimation (QPE)"),
    (["iterative_amplitude_estimation", "iqae", "amplitude estimation"],      "Quantum Amplitude Estimation"),
    (["amplitude_encode", "bind_data", "bind_nonneg", "data encoding",
      "amplitude encoding"],                                                   "Data Encoding"),
    (["variational quantum eigensolver", "vqe", "eigensolver"],               "Variational Quantum Eigensolver (VQE)"),
    (["qaoa", "quantum_approximate_optimization",
      "quantum approximate optimization", "ising_model", "qaoa_in_list"],     "Quantum Approximate Optimization Algorithm (QAOA)"),
    (["variational quantum algorithm", "variational quantum", "ansatz",
      "vqg_", "variationalquantumgate"],                                      "Variational Quantum Algorithm (VQA)"),
    (["hamiltonian simulation", "simulate_hamiltonian", "simulate_z_term",
      "simulate_one_term", "simulate_pauliz", "adiabatic_simulation",
      "expmat", "qoperator", "time evolution", "trotterization",
      "qite", "imaginary time"],                                               "Hamiltonian Simulation"),
    (["oracle", "two_qubit_oracle"],                                           "Oracle"),
    (["quantum circuit learning", "quantum neural"],                           "Quantum Neural Network (QNN)"),
]

# ── Pattern matching ──────────────────────────────────────────────────────────

def assign_pattern(name: str, doc: str) -> str | None:
    text = (name + " " + doc).lower()
    for keywords, pattern in _PATTERN_RULES:
        if any(kw in text for kw in keywords):
            return pattern
    return None


# ── pybind11 C++ binding parser ───────────────────────────────────────────────

# Match a complete m.def(...) block (balanced parentheses assumed within one block)
_MDEF_BLOCK_RE = re.compile(r'm\.def\((.+?)\);', re.DOTALL)
# Match a complete py::class_<...>(...) block
_CLASS_BLOCK_RE = re.compile(r'py::class_<[^>]+>\s*\((.+?)\);', re.DOTALL)
# Extract all quoted string literals from a block
_QUOTED_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _extract_name_and_doc(block: str) -> tuple[str, str] | None:
    """From a pybind11 m.def or py::class_ argument block, return (name, docstring).

    The name is always the very first quoted string in the block.
    The docstring is the first long (>= 12 chars) string after the name that
    is not a py::arg value and not an error/raises marker.
    """
    all_strings = _QUOTED_RE.findall(block)
    if not all_strings:
        return None
    name = all_strings[0]  # always the function/class name — no length filter
    # Docstring: first candidate that looks like prose
    for s in all_strings[1:]:
        if (len(s) >= 12
                and "run_fail" not in s
                and "%" not in s
                and not s.startswith("    ")   # indented arg description
                and "\\" not in s[:4]):        # skip "\n" openers
            return name, re.sub(r'\s+', ' ', s).strip()
    return name, ""


def parse_binding_file(path: Path) -> list[dict]:
    """Extract (name, doc) pairs from a pybind11 .cpp file."""
    src = path.read_text(encoding="utf-8", errors="ignore")
    entries: list[dict] = []

    for m in _MDEF_BLOCK_RE.finditer(src):
        result = _extract_name_and_doc(m.group(1))
        if not result:
            continue
        name, doc = result
        pattern = assign_pattern(name, doc)
        if pattern:
            entries.append({"name": f"/qpanda/{name}", "summary": doc or name, "pattern": pattern})

    for m in _CLASS_BLOCK_RE.finditer(src):
        result = _extract_name_and_doc(m.group(1))
        if not result:
            continue
        name, doc = result
        pattern = assign_pattern(name, doc)
        if pattern:
            entries.append({"name": f"/qpanda/{name}", "summary": doc or name, "pattern": pattern})

    return entries


# ── Python AST parser ─────────────────────────────────────────────────────────

def _get_docstring(node: ast.AST) -> str:
    """Return the first string literal in a function/class body as the docstring."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return ""
    if not node.body:
        return ""
    first = node.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        return first.value.value.strip()
    return ""


def parse_python_file(path: Path) -> list[dict]:
    """Extract quantum concepts from a Python source file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []

    entries: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            continue
        name = node.name
        doc = _get_docstring(node)
        pattern = assign_pattern(name, doc)
        if pattern:
            rel = str(path.relative_to(REPO_ROOT))
            qualified = f"/qpanda/{rel.replace('/', '.').rstrip('.py')}.{name}"
            entries.append({"name": qualified, "summary": doc or name, "pattern": pattern})
    return entries


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    all_entries: list[dict] = []
    seen: set[str] = set()

    def add(entries: list[dict]) -> None:
        for e in entries:
            if e["name"] not in seen:
                seen.add(e["name"])
                all_entries.append(e)

    # 1. pybind11 binding files
    for rel in BINDING_FILES:
        path = REPO_ROOT / rel
        if not path.exists():
            logging.warning(f"Binding file not found: {path}")
            continue
        entries = parse_binding_file(path)
        logging.info(f"{rel}: {len(entries)} entries")
        add(entries)

    # 2. Python algorithm files
    for rel_dir in PYTHON_DIRS:
        dir_path = REPO_ROOT / rel_dir
        if not dir_path.exists():
            logging.warning(f"Python dir not found: {dir_path}")
            continue
        for py in sorted(dir_path.rglob("*.py")):
            if py.name == "__init__.py":
                continue
            entries = parse_python_file(py)
            if entries:
                logging.info(f"{py.relative_to(REPO_ROOT)}: {len(entries)} entries")
            add(entries)

    logging.info(f"Total: {len(all_entries)} unique entries")

    # Report pattern breakdown
    from collections import Counter
    counts = Counter(e["pattern"] for e in all_entries)
    for pat, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {n:3d}  {pat}")

    # Save JSON (concepts file — name + summary only)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    concepts = [{"name": e["name"], "summary": e["summary"]} for e in all_entries]
    JSON_OUT.write_text(json.dumps(concepts, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info(f"Saved {JSON_OUT}")

    # Save enriched CSV (name + summary + pattern)
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "summary", "pattern"])
        writer.writeheader()
        for e in all_entries:
            writer.writerow({"name": e["name"], "summary": e["summary"], "pattern": e["pattern"]})
    logging.info(f"Saved {CSV_OUT}")


if __name__ == "__main__":
    main()

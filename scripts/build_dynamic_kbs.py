"""Build a dynamic KB for every non-seed project in target_github_projects/.

Strategy — docstring-to-summary matching:
  For each public function/class in the project's source code that has a
  docstring, embed the docstring and compare it against KB concept summaries.
  When similarity >= MIN_SCORE the function/class NAME is added to the dynamic
  KB under the matched pattern.  This works for any well-documented library
  without requiring directory-structure knowledge or manual labels, making it
  fully generalizable to new frameworks.

  Threshold default: 0.65  (docstrings vs summaries carry enough semantic
  content to reliably assign patterns at this level; short acronym names alone
  required >= 0.90 but misclassified e.g. QAE as QAOA).

For each project the script:
1. Fingerprints all .py source files (skipping noise dirs).
2. Compares against the stored fingerprint in data/dynamic_kb/<project>/meta.json.
3. If unchanged: skips (persisted KB is still valid).
4. If changed (or new): scans source files, matches docstrings against KB
   concept summaries, and writes:
       data/dynamic_kb/<project>/concepts.json
       data/dynamic_kb/<project>/patterns.csv
       data/dynamic_kb/<project>/meta.json

The embedding model and seed KB are loaded once and reused across all projects.

Run:
    .venv/bin/python scripts/build_dynamic_kbs.py
    .venv/bin/python scripts/build_dynamic_kbs.py --min-score 0.70
    .venv/bin/python scripts/build_dynamic_kbs.py --force
    .venv/bin/python scripts/build_dynamic_kbs.py --project Qrisp --force
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import torch
from scipy.spatial.distance import cdist
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.conf import config
from src.analysis.run import (
    CONCEPT_FILES,
    PATTERN_FILES,
    normalize_identifier,
    load_patterns_map,
    load_quantum_concepts,
    load_kb_embeddings,
)

# ── Constants ──────────────────────────────────────────────────────────────────

MIN_SCORE_DEFAULT = 0.70
# Generic words that appear in many pattern names but carry no discriminating
# signal when present alone in a function/class identifier.
_PATTERN_STOP_TOKENS: frozenset[str] = frozenset({
    "quantum", "algorithm", "algorithms", "circuit", "circuits",
    "gate", "gates", "operator", "operators", "problem", "method",
    "model", "state", "states", "based", "using", "function", "test",
})

_ABBREVIATION_RE = re.compile(r'\(([A-Z]{2,})\)')

# Seed-KB project names — phase 1 is redundant for these because their
# function names are already in the seed KB.
SEED_KB_PROJECTS = {
    "classiq-library",
    "pennylane",
    "qiskit",
    "qiskit-algorithms",
    "qiskit-machine-learning",
}

# Directories to skip when collecting source .py files.
SKIP_DIRS = set(config.SKIP_DIRS_COMMON) | {
    "documentation",      # Qrisp tutorial notebooks live here
    "notebooks", "notebook",
    "tutorials", "tutorial",
    "jupyter_execute",
    ".ipynb_checkpoints",
}

PATTERNS_FILE = config.RESULTS_DIR / "pattern_descriptions.json"

# Section headers that mark the end of the conceptual description in a docstring.
# Everything from the first occurrence onward is parameter/return noise.
_SECTION_HEADERS = re.compile(
    r'^\s*(Parameters|Args|Arguments|Returns|Return|Raises|Attributes|'
    r'Notes|Note|Examples|Example|References|See Also|Todo)\s*[-:—]?\s*$',
    re.IGNORECASE | re.MULTILINE,
)


_RST_NOISE = re.compile(
    r':(?:ref|class|func|meth|attr|mod|data|const|exc|obj|type)`[^`]*`'  # :ref:`...`
    r'|`[^`]+`_?'         # `backtick` references
    r'|\.{2}\s+\S+\s*::?' # .. directive::
    r'|\.\. \w+::'        # .. note::
    r'|\|[^|]+\|'         # |substitution|
    r'|\\(?:math|text)\{[^}]*\}',  # latex \math{...}
    re.VERBOSE,
)


def _trim_docstring(doc: str, max_chars: int = 300) -> str:
    """Return the conceptual portion of a docstring, cleaned of markup.

    Steps:
    1. Cut at the first recognised parameter/return section header so that
       only the description paragraph is kept.
    2. Strip RST / Sphinx inline markup (backticks, :ref: links, math) that
       adds no semantic signal but occupies token budget.
    3. Cap at max_chars.
    """
    text = doc.strip()
    # Cut at first section header
    m = _SECTION_HEADERS.search(text)
    if m:
        text = text[: m.start()].strip()
    # Strip RST inline markup
    text = _RST_NOISE.sub(' ', text)
    # Collapse extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_chars] if text else doc[:max_chars]

# Gate-name stopwords: single-gate and common gate class names whose docstrings
# describe gate mechanics, not algorithm-level patterns. A name is excluded if
# any token in it (after splitting CamelCase / snake_case) is in this set.
GATE_STOPWORDS = {
    # Single-qubit gates
    "x", "y", "z", "h", "s", "t", "i",
    "rx", "ry", "rz", "r", "p", "u", "u1", "u2", "u3",
    "sx", "sxdg", "sdg", "tdg", "v", "vdg",
    # Two-qubit gates
    "cx", "cy", "cz", "ch", "cnot", "swap", "iswap", "cswap",
    "crx", "cry", "crz", "cp", "cu", "cu1", "cu3",
    "ccx", "toffoli", "rxx", "ryy", "rzz", "rzx", "ecr", "dcx",
    # Generic gate vocabulary
    "gate", "gateop", "gateset", "gatedefinition",
    # Pauli words
    "pauli", "paulix", "pauliy", "pauliz", "paulii",
    "xgate", "ygate", "zgate", "hgate", "sgate", "tgate",
    "cxgate", "cygate", "czgate", "swapgate", "ccxgate",
    # Generic circuit / quantum infrastructure — not algorithm-level concepts.
    # A name is excluded only when ALL its tokens appear here (so
    # "HamiltonianSimulation" still passes because "hamiltonian" is absent).
    "circuit", "circuits", "quantum", "classical", "device", "backend",
    "provider", "job", "result", "results", "measurement", "measurements",
    "unitary", "identity", "operator", "operation", "instruction",
    "register", "qubit", "qubits", "bit", "bits", "clbit", "ancilla",
    "sampler", "estimator", "simulator",
    # Generic programming / ML methods
    "execute", "run", "fit", "predict", "transform", "score", "train",
    "evaluate", "compute", "calculate", "apply", "build", "create",
    "load", "save", "reset", "clear", "copy", "update", "initialize",
    "compile", "transpile", "convert", "encode", "decode", "simulate",
    # Generic math / utility
    "isclose", "allclose", "norm", "trace", "dot", "add", "sub",
    "mul", "div", "exp", "log", "sqrt", "split",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def source_fingerprint(project_dir: Path) -> str:
    """SHA-256 of all non-skipped .py file paths + sizes + mtimes."""
    h = hashlib.sha256()
    for p in sorted(project_dir.rglob("*.py")):
        rel = p.relative_to(project_dir)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        try:
            stat = p.stat()
            h.update(f"{rel}:{stat.st_size}:{stat.st_mtime}".encode())
        except OSError:
            pass
    return h.hexdigest()


def collect_source_files(project_dir: Path) -> list[Path]:
    """Return .py files in the project, excluding skip dirs."""
    files = []
    for p in sorted(project_dir.rglob("*.py")):
        rel = p.relative_to(project_dir)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        files.append(p)
    return files


def extract_defined_with_docstrings(py_path: Path) -> list[tuple[str, str]]:
    """Return (name, docstring) for every public function/class defined in the file.

    Only top-level and class-level definitions with a non-trivial docstring
    (>= 20 chars) are included. Private names (leading underscore) and very
    short names (<= 3 chars, e.g. single-letter gate names x/h/cx) are skipped
    since they are too generic to identify a meaningful pattern.
    """
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    results: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if node.name.startswith("_"):
            continue
        # Skip names whose tokens are all gate-level vocabulary.
        name_lower = node.name.lower()
        # Split on underscores and camelCase boundaries.
        import re as _re
        tokens = [t.lower() for t in _re.split(r'[_\s]+', _re.sub(r'([a-z])([A-Z])', r'\1 \2', node.name)) if t]
        if all(t in GATE_STOPWORDS or len(t) <= 2 for t in tokens):
            continue
        doc = ast.get_docstring(node)
        if doc and len(doc.strip()) >= 20:
            results.append((node.name, _trim_docstring(doc)))
    return results


def build_dynamic_kb(
    project_name: str,
    project_dir: Path,
    quantum_concepts: list[dict],
    concept_summary_embeddings: torch.Tensor,
    model: SentenceTransformer,
    min_score: float,
) -> dict[str, str]:
    """Return {name: pattern} by matching function/class docstrings against KB summaries.

    Docstrings carry enough semantic content to reliably assign patterns at
    threshold 0.65, whereas short names alone required >= 0.90 and still
    misclassified acronyms (e.g. QAE matched QAOA instead of Quantum Amplitude
    Estimation). Any given name keeps only its highest-scoring pattern assignment.
    """
    name_score_pattern: dict[str, tuple[float, str]] = {}

    for py_path in collect_source_files(project_dir):
        defs = extract_defined_with_docstrings(py_path)
        if not defs:
            continue
        names = [name for name, _ in defs]
        docs  = [doc  for _, doc  in defs]
        try:
            emb = model.encode(docs, convert_to_tensor=True)
        except Exception:
            continue
        sims = 1 - cdist(emb.cpu(), concept_summary_embeddings.cpu(), "cosine")
        for def_idx, name in enumerate(names):
            best_score = float(sims[def_idx].max())
            if best_score < min_score:
                continue
            best_concept = quantum_concepts[int(sims[def_idx].argmax())]
            if best_concept["pattern"] == "N/A":
                continue
            # Keep highest-scoring assignment per name to handle duplicates.
            prev = name_score_pattern.get(name)
            if prev is None or best_score > prev[0]:
                name_score_pattern[name] = (best_score, best_concept["pattern"])

    return {name: pat for name, (_, pat) in name_score_pattern.items()}


_CAMEL_SPLIT = re.compile(r'([a-z])([A-Z])')


def _normalize_identifier(name: str) -> str:
    """Split CamelCase / snake_case into lowercase space-separated tokens.

    'QAOAProblem'            → 'qaoa problem'
    'grovers_alg'            → 'grovers alg'
    'hamiltonian_simulation' → 'hamiltonian simulation'
    'QFT'                    → 'qft'
    """
    # Split all-caps acronym from following CamelCase word: 'QAOAProblem' → 'QAOA Problem'
    spaced = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', name)
    # Split standard camelCase boundary: 'groverAlg' → 'grover Alg'
    spaced = _CAMEL_SPLIT.sub(r'\1 \2', spaced)
    return re.sub(r'[\s_]+', ' ', spaced).strip().lower()


def collect_public_names(project_dir: Path) -> list[str]:
    """Return all public, non-trivial function/class names in the project.

    Same gate-stopword and private-name filtering as extract_defined_with_docstrings,
    but no docstring requirement — used for name-based pattern matching.
    """
    names: list[str] = []
    for py_path in collect_source_files(project_dir):
        try:
            tree = ast.parse(py_path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if node.name.startswith("_") or len(node.name) <= 2:
                continue
            tokens = [
                t.lower()
                for t in re.split(r'[_\s]+', re.sub(r'([a-z])([A-Z])', r'\1 \2', node.name))
                if t
            ]
            if all(t in GATE_STOPWORDS or len(t) <= 2 for t in tokens):
                continue
            names.append(node.name)
    return names


PatternSig = tuple[frozenset[str], frozenset[str]]  # (abbrevs, keywords)


def _pattern_signature(pattern_name: str) -> PatternSig:
    """Extract discriminating tokens from a pattern name.

    Returns a 2-tuple:
    - abbrevs  : tokens from parenthetical notation — exact-match, any one sufficient.
    - keywords : remaining distinctive words — prefix-match, ALL must be present.

    Examples:
      'Grover'                                            → (set(), {'grover'})
      'Quantum Approximate Optimization Algorithm (QAOA)' → ({'qaoa'}, {'approximate', 'optimization'})
      'Hamiltonian Simulation'                            → (set(), {'hamiltonian', 'simulation'})
      'Quantum Phase Estimation (QPE)'                    → ({'qpe'}, {'phase', 'estimation'})
    """
    abbrevs: set[str] = set()
    for m in _ABBREVIATION_RE.finditer(pattern_name):
        abbrevs.add(m.group(1).lower())
    main = _ABBREVIATION_RE.sub('', pattern_name).strip()
    keywords: set[str] = set()
    for word in re.sub(r'[^a-z ]', '', main.lower()).split():
        if word not in _PATTERN_STOP_TOKENS and len(word) >= 5:
            keywords.add(word)
    return frozenset(abbrevs), frozenset(keywords)


def build_dynamic_kb_by_name(
    project_dir: Path,
    pattern_signatures: dict[str, frozenset[str]],
) -> dict[str, str]:
    """Return {identifier: pattern} by token overlap between normalized identifier
    names and pattern signature tokens.

    Complements build_dynamic_kb (docstring→summary): catches functions/classes
    that are named after an algorithm (e.g. grovers_alg → Grover, QAOAProblem →
    QAOA, hamiltonian_simulation → Hamiltonian Simulation) even when their
    docstrings score below the docstring threshold or are absent entirely.

    Matching rules:
    - Abbreviation tokens (≤4 chars, e.g. 'qaoa', 'qpe'): any single exact match
      is sufficient — abbreviations are short but highly discriminating.
    - Keyword tokens (≥5 chars, e.g. 'grover', 'hamiltonian'): ALL keywords must
      match via prefix check (name_tok.startswith(sig_tok)). Requiring all keywords
      prevents single generic tokens like 'simulation' from firing on every file.
    """
    all_names = collect_public_names(project_dir)
    if not all_names:
        return {}

    result: dict[str, str] = {}
    for raw_name in dict.fromkeys(all_names):  # dedup, preserve order
        name_tokens = _normalize_identifier(raw_name).split()
        if not name_tokens or max(len(t) for t in name_tokens) < 3:
            continue
        for pattern, (abbrevs, keywords) in pattern_signatures.items():
            # Abbreviation tokens (from parenthetical notation): any exact match suffices.
            abbrev_match = any(nt == at for at in abbrevs for nt in name_tokens)
            # Keyword tokens: every keyword must prefix-match at least one name token.
            kw_match = bool(keywords) and all(
                any(nt.startswith(kt) for nt in name_tokens)
                for kt in keywords
            )
            if abbrev_match or kw_match:
                result[raw_name] = pattern
                break
    return result


def write_dynamic_kb(out_dir: Path, project_name: str, name_pattern: dict[str, str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    concepts = []
    patterns = []
    for name, pattern in sorted(name_pattern.items()):
        # Path encodes the project so the report can attribute matches to the
        # correct source project rather than a generic "dynamic" label.
        # extract_short_name in run.py does split("/")[-1].split(".")[-1],
        # so the function name is still used correctly for name-channel matching.
        full_path = f"/dynamic/{project_name}/{name}"
        summary = f"{name}: implementation of the {pattern} pattern."
        concepts.append({
            "name": full_path,
            "summary": summary,
            "docstring": "",
            "type": "Function",
            "is_target_subclass": False,
            "base_classes": [],
            "internal_keywords": "",
            "internal_comments": "",
        })
        patterns.append({"name": full_path.lstrip("/"), "summary": summary, "pattern": pattern})

    with open(out_dir / "concepts.json", "w", encoding="utf-8") as f:
        json.dump(concepts, f, indent=2)
    with open(out_dir / "patterns.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "summary", "pattern"])
        w.writeheader()
        w.writerows(patterns)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--min-score", type=float, default=MIN_SCORE_DEFAULT)
    p.add_argument("--force", action="store_true",
                   help="Ignore fingerprints and rebuild all dynamic KBs.")
    p.add_argument("--project", type=str, default=None,
                   help="Process only this project name (for testing).")
    args = p.parse_args()

    src_base = config.TARGET_PROJECTS_BASE_PATH
    dyn_base = config.DYNAMIC_KB_DIR
    dyn_base.mkdir(parents=True, exist_ok=True)

    # Collect projects: skip seed KB frameworks
    projects = [
        d for d in sorted(src_base.iterdir())
        if d.is_dir() and d.name not in SEED_KB_PROJECTS
    ]
    if args.project:
        projects = [d for d in projects if d.name == args.project]
        if not projects:
            sys.exit(f"Project '{args.project}' not found in {src_base}.")

    # Filter: only projects with at least a few .py source files
    eligible = []
    for proj_dir in projects:
        files = collect_source_files(proj_dir)
        if len(files) >= 5:
            eligible.append((proj_dir, files))

    print(f"Found {len(eligible)} projects with >= 5 source .py files "
          f"(skipping {len(projects) - len(eligible)} with fewer).")

    # ── Load seed KB and model once ───────────────────────────────────────────
    # Use only seed KB concept files (not dynamic ones) so there is no
    # circular dependency when building project X's dynamic KB.
    seed_concept_files = [
        config.RESULTS_DIR / "classiq_quantum_concepts.json",
        config.RESULTS_DIR / "pennylane_quantum_concepts.json",
        config.RESULTS_DIR / "qiskit_quantum_concepts.json",
        config.RESULTS_DIR / "qiskit_algorithms_quantum_concepts.json",
        config.RESULTS_DIR / "qiskit_machine_learning_quantum_concepts.json",
    ]
    seed_pattern_files = [
        config.RESULTS_DIR / "knowledge_base/enriched_classiq_quantum_patterns.csv",
        config.RESULTS_DIR / "knowledge_base/enriched_pennylane_quantum_patterns.csv",
        config.RESULTS_DIR / "knowledge_base/enriched_qiskit_quantum_patterns.csv",
        config.RESULTS_DIR / "knowledge_base/enriched_qiskit_algorithms_quantum_patterns.csv",
        config.RESULTS_DIR / "knowledge_base/enriched_qiskit_machine_learning_quantum_patterns.csv",
    ]
    print("Loading seed KB…")
    pattern_map = load_patterns_map(seed_pattern_files)
    quantum_concepts = load_quantum_concepts(seed_concept_files, pattern_map)
    quantum_concepts = [c for c in quantum_concepts if c["pattern"] != "N/A"]
    print(f"  {len(quantum_concepts)} concepts with a valid pattern assignment.")

    print(f"Loading embedding model '{config.EMBEDDING_MODEL_NAME}'…")
    model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    concept_short_names = [c["short_name"] for c in quantum_concepts]
    concept_summaries   = [c["summary"]     for c in quantum_concepts]
    pd_texts = []  # pattern desc not needed here
    (_, concept_summary_embeddings, _, _, _, _, _) = load_kb_embeddings(
        model, concept_short_names, concept_summaries, pd_texts,
        seed_pattern_files, seed_concept_files,
    )
    print("  Model and KB embeddings ready.")

    # Pre-compute token signatures for the name-based matching signal.
    unique_pattern_names = sorted(set(pattern_map.values()) - {"N/A"})
    pattern_signatures: dict[str, PatternSig] = {
        p: _pattern_signature(p) for p in unique_pattern_names
    }
    print(f"  {len(unique_pattern_names)} pattern signatures built for name-based matching.")

    # ── Process each project ──────────────────────────────────────────────────
    skipped = rebuilt = empty = 0
    for proj_dir, _ in eligible:
        name = proj_dir.name
        out_dir = dyn_base / name
        meta_path = out_dir / "meta.json"

        fp = source_fingerprint(proj_dir)
        if meta_path.exists():
            stored = json.loads(meta_path.read_text())
            # Never overwrite manually curated KBs.
            if stored.get("source") == "manual":
                skipped += 1
                continue
            # Skip if source is unchanged and threshold is the same.
            if (not args.force
                    and stored.get("fingerprint") == fp
                    and stored.get("min_score") == args.min_score):
                skipped += 1
                continue

        print(f"\n  [{name}] scanning source…", end=" ", flush=True)
        # Signal 1: docstring → KB concept summary
        name_pattern = build_dynamic_kb(
            name, proj_dir, quantum_concepts, concept_summary_embeddings,
            model, args.min_score,
        )
        # Signal 2: normalized identifier name → pattern token signature
        # Merge — docstring signal wins on conflict (typically higher confidence).
        name_by_name = build_dynamic_kb_by_name(proj_dir, pattern_signatures)
        for ident, pat in name_by_name.items():
            if ident not in name_pattern:
                name_pattern[ident] = pat

        if not name_pattern:
            empty += 1
            # Write empty KB so fingerprint is still recorded (avoids re-scan)
            out_dir.mkdir(parents=True, exist_ok=True)
            with open(out_dir / "concepts.json", "w") as f: json.dump([], f)
            with open(out_dir / "patterns.csv",  "w", newline="") as f:
                csv.DictWriter(f, fieldnames=["name","summary","pattern"]).writeheader()
        else:
            write_dynamic_kb(out_dir, name, name_pattern)
            from collections import Counter
            by_pat = Counter(name_pattern.values())
            print(f"{len(name_pattern)} names — " +
                  ", ".join(f"{k}:{v}" for k, v in by_pat.most_common(3)))
            rebuilt += 1

        # The KB changed — delete the embedding cache so run_faster.py
        # re-encodes on the next run instead of serving stale embeddings.
        # (The cache fingerprint includes all dynamic KB files; because
        # build_dynamic_kbs.py calls load_kb_embeddings with only the seed KB,
        # it overwrites the cache with a fingerprint that still matches what
        # run_faster.py expects, causing run_faster to skip re-encoding.)
        kb_cache = config.RESULTS_DIR / "kb_embeddings_cache.pt"
        if kb_cache.exists():
            kb_cache.unlink()
            print("  KB cache cleared (will re-encode on next run_faster call).")

        meta_path.write_text(json.dumps({
            "project": name,
            "fingerprint": fp,
            "min_score": args.min_score,
            "names_found": len(name_pattern),
        }, indent=2))

    print(f"\nDone. Rebuilt: {rebuilt}  |  Empty: {empty}  |  Skipped (unchanged): {skipped}")
    print(f"Dynamic KBs stored in: {dyn_base}")


if __name__ == "__main__":
    main()

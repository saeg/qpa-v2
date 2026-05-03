"""Enrich each framework's quantum_concepts.json with two new fields:

  - internal_keywords: parameter names, return-type annotation, local
    variable names from method bodies. Filtered through a stopword list and
    a "composed only" rule (snake_case / CamelCase / length >= 8) so that
    generic tokens (`self`, `qubit`, `result`, `i`) do not pollute the
    embedding.
  - internal_comments: inline ``#`` comments inside the method/class body
    (NOT the class or function docstring). These typically describe the
    "how" of the implementation, complementing the docstring's "what".

Concepts that cannot be located in source (Classiq's QMOD library, missing
files, syntax errors) are left unchanged. Run is idempotent: re-running
overwrites the two fields. Originals get a one-time backup to ``*.bak.json``.

Run:
    .venv/bin/python scripts/enrich_kb_with_internals.py
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import shutil
import sys
import tokenize
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Map JSON-file-prefix → framework source root. Concepts whose name starts
# with /<prefix>/ are looked up under the corresponding source root.
FRAMEWORK_SOURCES = {
    "qiskit":                  PROJECT_ROOT / "target_github_projects/qiskit",
    "pennylane":               PROJECT_ROOT / "target_github_projects/pennylane",
    "qiskit-algorithms":       PROJECT_ROOT / "target_github_projects/qiskit-algorithms",
    "qiskit_machine_learning": PROJECT_ROOT / "target_github_projects/qiskit-machine-learning",
}

CONCEPT_JSONS = [
    PROJECT_ROOT / "data/qiskit_quantum_concepts.json",
    PROJECT_ROOT / "data/pennylane_quantum_concepts.json",
    PROJECT_ROOT / "data/qiskit_algorithms_quantum_concepts.json",
    PROJECT_ROOT / "data/qiskit_machine_learning_quantum_concepts.json",
    PROJECT_ROOT / "data/classiq_quantum_concepts.json",  # kept for completeness; QMOD source not parseable
]

# ---------------------------------------------------------------------------
# Stopwords — generic tokens that do not discriminate between patterns.
# Lowered before lookup; applied to BOTH internal_keywords and any token-level
# keyword filtering. Curated to cover Python-builtin, generic ML/quantum, and
# single-letter loop vars.
# ---------------------------------------------------------------------------
STOPWORDS: set[str] = {
    # Python-builtin / structural
    "self", "cls", "args", "kwargs", "arg", "kwarg", "value", "values", "key",
    "keys", "item", "items", "result", "results", "output", "outputs", "input",
    "inputs", "param", "params", "parameter", "parameters", "name", "names",
    "data", "index", "indices", "length", "size", "number", "count", "total",
    "sum", "max", "min", "list", "dict", "tuple", "set", "frozenset", "string",
    "str", "int", "float", "bool", "object", "type", "callable", "function",
    "method", "class", "instance", "iterable", "iterator", "generator",
    "sequence", "array", "matrix", "vector", "optional", "union", "any", "all",
    "none", "true", "false", "return", "yield", "raise", "except", "try",
    "finally", "pass", "options", "option", "config", "default", "defaults",
    "kwarg", "callback", "validator", "validation", "check", "checks",
    "msg", "message", "error", "errors", "warning", "warnings", "info",
    "debug", "logger", "log", "logs", "verbose", "context",
    "new", "old", "next", "prev", "first", "last", "current", "previous",
    "like", "kind", "mode", "modes", "level", "levels", "step", "steps",
    "iteration", "iterations", "iter", "iters", "epoch", "epochs",
    "num", "nbr", "no", "ratio", "rate", "scale", "factor", "factors",
    "shape", "shapes", "dim", "dims", "dimension", "dimensions", "axis", "axes",
    "true_value", "false_value", "raw", "ref", "refs", "id", "ids",
    "manager", "managers", "handler", "handlers", "wrapper", "wrappers",
    "prefix", "suffix", "label", "labels", "tag", "tags", "flag", "flags",
    "metadata", "meta", "definition", "definitions", "resource", "resources",
    "annotation", "annotations", "annotated",
    # Generic quantum vocabulary that appears in nearly every concept
    "circuit", "circuits", "qubit", "qubits", "gate", "gates", "state", "states",
    "register", "registers", "wire", "wires", "operator", "operators",
    "operation", "operations", "measurement", "measurements", "quantum",
    "classical", "qreg", "creg", "op", "ops", "clbit", "clbits",
    "base", "bases", "gradient", "grad",
    "transpiler", "compiler", "compile", "simulator", "backend", "device", "provider",
    "estimator", "estimators", "sampler", "samplers", "primitive", "primitives",
    "hamiltonian", "observable", "observables",
    # Short / single-letter variable names
    *list("abcdefghijklmnopqrstuvwxyz"),
    "tmp", "temp", "val", "res", "out", "idx", "fn", "func", "cb", "ctx", "var",
    "vars", "obj", "dst", "src", "lhs", "rhs", "row", "col", "rows", "cols",
    # Qiskit/PennyLane specific noise (commonly reused, low signal)
    "params_", "param_", "gate_", "qiskit", "pennylane", "qml", "np", "pd",
    "v1", "v2", "v3",
}

# Tokens that appear in more than this fraction of concepts are dropped
# globally as a post-processing step (e.g. ``QuantumCircuit`` ends up here
# because nearly every Qiskit method touches it).
DOC_FREQ_CAP_FRACTION = 0.05

# Tokens shorter than MIN_TOKEN_LEN are dropped before stopword check.
MIN_TOKEN_LEN = 4


def is_composed(token: str) -> bool:
    """Discriminative-keyword filter.

    Keep tokens that have snake_case, CamelCase, or that are >= 8 chars and
    fully alphabetic. Reject pure numeric, single-word generic 4-7 char
    tokens, and noise like ``__init__``.
    """
    if not token or not isinstance(token, str):
        return False
    if token.startswith("__") and token.endswith("__"):
        return False
    if len(token) < MIN_TOKEN_LEN:
        return False
    has_underscore = "_" in token.strip("_")
    has_camel = bool(re.search(r"[a-z][A-Z]", token))
    if has_underscore or has_camel:
        return True
    if len(token) >= 8 and token.isalpha():
        return True
    return False


def _split_tokens(token: str) -> list[str]:
    """Split a snake_case / CamelCase identifier into lowercase parts."""
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", token)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    parts = re.split(r"[_\s]+", s)
    return [p.lower() for p in parts if p]


def keep_keyword(token: str) -> bool:
    """Apply stopword + composed + decompose-and-stopword filters."""
    if not token:
        return False
    tl = token.lower()
    if tl in STOPWORDS:
        return False
    if not is_composed(token):
        return False
    # Decompose-and-stopword: if every sub-token is a stopword, drop. This
    # catches `num_qubits`, `QuantumCircuit`, `BaseOperator`, etc. without
    # needing to enumerate every compound form.
    parts = _split_tokens(token)
    if parts and all(p in STOPWORDS for p in parts):
        return False
    return True


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _collect_assign_targets(target: ast.AST, out: set[str]) -> None:
    """Walk an Assign target (Name | Tuple | Attribute | Subscript) and record names."""
    if isinstance(target, ast.Name):
        out.add(target.id)
    elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
        for elt in target.elts:
            _collect_assign_targets(elt, out)
    elif isinstance(target, ast.Attribute):
        out.add(target.attr)
    elif isinstance(target, ast.Starred):
        _collect_assign_targets(target.value, out)


def _scope_of(node: ast.AST) -> list[ast.AST]:
    """Return the list of function/method scopes inside this concept node.

    For a class concept we want every method defined directly on the class
    (not nested classes). For a function concept it's just the function.
    """
    if isinstance(node, ast.ClassDef):
        return [
            n for n in node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return [node]
    return []


def extract_internal_keywords(node: ast.AST) -> list[str]:
    """Parameter names, return annotations, local variable names — discriminative only."""
    raw: set[str] = set()
    for scope in _scope_of(node):
        # Parameters
        for arg in (
            scope.args.args
            + scope.args.posonlyargs
            + scope.args.kwonlyargs
        ):
            raw.add(arg.arg)
            if arg.annotation:
                try:
                    raw.add(ast.unparse(arg.annotation))
                except Exception:
                    pass
        if scope.args.vararg:
            raw.add(scope.args.vararg.arg)
        if scope.args.kwarg:
            raw.add(scope.args.kwarg.arg)
        # Return annotation
        if scope.returns:
            try:
                raw.add(ast.unparse(scope.returns))
            except Exception:
                pass
        # Body: assignments + annotated assignments
        for sub in ast.walk(scope):
            if isinstance(sub, ast.Assign):
                for tgt in sub.targets:
                    _collect_assign_targets(tgt, raw)
            elif isinstance(sub, ast.AnnAssign):
                _collect_assign_targets(sub.target, raw)
                if sub.annotation:
                    try:
                        raw.add(ast.unparse(sub.annotation))
                    except Exception:
                        pass
    # Class-level annotations / assignments are also useful (typed attrs)
    if isinstance(node, ast.ClassDef):
        for sub in node.body:
            if isinstance(sub, ast.Assign):
                for tgt in sub.targets:
                    _collect_assign_targets(tgt, raw)
            elif isinstance(sub, ast.AnnAssign):
                _collect_assign_targets(sub.target, raw)

    # Annotation strings often look like "Optional[QuantumCircuit]" — split on
    # punctuation to expose ``QuantumCircuit`` as a separate token.
    expanded: set[str] = set()
    for tok in raw:
        for piece in re.split(r"[\[\]\(\),\s|]+", tok):
            if piece:
                expanded.add(piece)

    return sorted(t for t in expanded if keep_keyword(t))


def extract_internal_comments(node: ast.AST, source_text: str) -> list[str]:
    """Inline ``#`` comments inside the node's body, excluding the docstring."""
    if not (hasattr(node, "lineno") and hasattr(node, "end_lineno") and node.end_lineno):
        return []
    lines = source_text.splitlines()
    body_text = "\n".join(lines[node.lineno - 1: node.end_lineno])
    comments: list[str] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(body_text).readline):
            if tok.type != tokenize.COMMENT:
                continue
            txt = tok.string.lstrip("#").strip()
            if not txt or txt.startswith("!"):  # skip shebang
                continue
            # Filter very short or boilerplate comments
            if len(txt) < 6:
                continue
            comments.append(txt)
    except (tokenize.TokenizeError, IndentationError, SyntaxError):
        pass
    return comments


# ---------------------------------------------------------------------------
# Source index
# ---------------------------------------------------------------------------

def build_source_index(source_root: Path) -> dict[str, tuple[Path, ast.AST, str]]:
    """Walk source_root and index every top-level class/function by qualified name.

    Key example: ``qiskit.circuit.library.qft.QFT``. Module path uses dots;
    the trailing segment is the class/function name. ``__init__.py`` files
    map to the package qualname (no trailing ``.__init__``).
    """
    index: dict[str, tuple[Path, ast.AST, str]] = {}
    for py in source_root.rglob("*.py"):
        rel = py.relative_to(source_root)
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        module_qual = ".".join(parts)
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(text)
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qual = f"{module_qual}.{node.name}" if module_qual else node.name
                # First write wins — duplicate qualnames across files are rare.
                index.setdefault(qual, (py, node, text))
    return index


# ---------------------------------------------------------------------------
# Lookup against concept name
# ---------------------------------------------------------------------------

def concept_qualname(name: str) -> tuple[str, str]:
    """Return (framework_prefix, qualified_name).

    Handles the JSON ``name`` format ``"/<framework>/<dotted.qual.name>"``.
    """
    s = name.lstrip("/")
    parts = s.split("/", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "", parts[0]


def lookup_concept(
    concept_name: str, indices: dict[str, dict[str, tuple[Path, ast.AST, str]]]
) -> tuple[Path, ast.AST, str] | None:
    """Try to find the source AST node for a concept across framework indices."""
    fw_prefix, qual = concept_qualname(concept_name)
    candidates = []
    if fw_prefix in indices:
        candidates.append(indices[fw_prefix])
    # Also try all indices in case the prefix mapping differs
    for k, idx in indices.items():
        if k != fw_prefix:
            candidates.append(idx)
    short = qual.rsplit(".", 1)[-1]
    for idx in candidates:
        # Exact qualname
        if qual in idx:
            return idx[qual]
        # Suffix match: any indexed qual ends with our qual
        for k, v in idx.items():
            if k.endswith("." + qual):
                return v
        # Fallback: short-name match (last segment only)
        for k, v in idx.items():
            if k.rsplit(".", 1)[-1] == short:
                return v
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true", help="Skip writing JSON files (preview only).")
    args = p.parse_args()

    print("Building source indices...")
    indices: dict[str, dict] = {}
    for fw, root in FRAMEWORK_SOURCES.items():
        if not root.exists():
            print(f"  WARN: source root missing for {fw} — skipping ({root})")
            continue
        idx = build_source_index(root)
        indices[fw] = idx
        print(f"  {fw}: indexed {len(idx)} top-level defs from {root}")

    # ---------------------------------------------------------------------
    # Phase 1 — per-file extraction (held in memory).
    # ---------------------------------------------------------------------
    print("\nPhase 1: extracting internal keywords + comments per concept...")
    file_payloads: list[tuple[Path, list[dict], list[set[str]], list[list[str]]]] = []
    for jpath in CONCEPT_JSONS:
        if not jpath.exists():
            print(f"  SKIP: {jpath} not found")
            continue
        if not (jpath.with_suffix(".bak.json")).exists():
            shutil.copy2(jpath, jpath.with_suffix(".bak.json"))
        with open(jpath, encoding="utf-8") as f:
            data = json.load(f)
        per_concept_kws: list[set[str]] = []
        per_concept_cmts: list[list[str]] = []
        for entry in data:
            hit = lookup_concept(entry.get("name", ""), indices)
            if hit is None:
                per_concept_kws.append(set())
                per_concept_cmts.append([])
                continue
            _, node, source_text = hit
            kws = set(extract_internal_keywords(node))
            cmts = extract_internal_comments(node, source_text)
            per_concept_kws.append(kws)
            per_concept_cmts.append(cmts)
        file_payloads.append((jpath, data, per_concept_kws, per_concept_cmts))

    # ---------------------------------------------------------------------
    # Phase 2 — global document-frequency pass over keywords. Tokens that
    # appear in too many concepts are framework-internal (QuantumCircuit,
    # _input_params, etc.) and add noise rather than signal.
    # ---------------------------------------------------------------------
    from collections import Counter
    total_concepts = sum(len(data) for _, data, _, _ in file_payloads)
    cap_count = max(2, int(total_concepts * DOC_FREQ_CAP_FRACTION))
    doc_freq: Counter = Counter()
    for _, _, per_kws, _ in file_payloads:
        for kws in per_kws:
            for tok in kws:
                doc_freq[tok] += 1
    too_common = {tok for tok, n in doc_freq.items() if n > cap_count}
    print(
        f"\nPhase 2: doc-freq cap = {cap_count} concepts ({DOC_FREQ_CAP_FRACTION:.0%} of {total_concepts}). "
        f"Dropping {len(too_common)} too-common tokens (e.g.: "
        f"{', '.join(sorted(too_common, key=lambda t: -doc_freq[t])[:8])})."
    )

    # ---------------------------------------------------------------------
    # Phase 3 — apply cap and write final JSONs.
    # ---------------------------------------------------------------------
    print("\nPhase 3: applying cap and writing JSONs...")
    if args.dry_run:
        print("[dry-run] No files will be written.")
        return

    for jpath, data, per_kws, per_cmts in file_payloads:
        matched = total_kw = total_cmt = 0
        for entry, kws, cmts in zip(data, per_kws, per_cmts):
            kept = sorted(t for t in kws if t not in too_common)
            entry["internal_keywords"] = " ".join(kept)
            entry["internal_comments"] = " ".join(cmts)
            if kept or cmts:
                matched += 1
            total_kw += len(kept)
            total_cmt += len(cmts)
        with open(jpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(
            f"  {jpath.name}: matched {matched}/{len(data)} entries; "
            f"{total_kw} keywords (post-cap), {total_cmt} comments"
        )

    print("\nDone. Backup originals at <name>.bak.json.")
    print("New fields per entry: internal_keywords (str), internal_comments (str).")


if __name__ == "__main__":
    sys.exit(main())

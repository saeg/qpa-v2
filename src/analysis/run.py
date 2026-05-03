import argparse
import ast
import csv
import hashlib
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import torch
from scipy.spatial.distance import cdist
from sentence_transformers import SentenceTransformer

from src.conf import config
from src.analysis.pattern_keywords import (
    load_pattern_descriptions,
    build_pattern_description_texts,
)

KB_CACHE_FILE = config.RESULTS_DIR / "kb_embeddings_cache.pt"
PATTERN_DESCRIPTIONS_FILE = config.RESULTS_DIR / "pattern_descriptions.json"
PATTERN_EXCLUSIVE_KEYWORDS_FILE = config.RESULTS_DIR / "pattern_keywords_exclusive.json"
ANALYSIS_CONFIG_FILE = config.RESULTS_DIR / "analysis_config.json"
RUNS_DIR = config.RESULTS_DIR / "runs"

DEFAULT_CHANNEL_CONFIG = {
    "name":              {"enabled": True, "threshold": 0.90},
    "summary":           {"enabled": True, "threshold": 0.75},
    "title":             {"enabled": True, "threshold": 0.75},
    "pattern_desc":      {"enabled": True, "threshold": 0.75},
    "defined_doc":       {"enabled": True, "threshold": 0.70},
    # New complementary channels (built from KB-internal source: variable names,
    # return annotations, and inline `#` comments inside method bodies). High
    # thresholds because the signal is narrow; concepts without these fields
    # are skipped entirely (no penalty for KB entries that lack them).
    "internal_keywords": {"enabled": True, "threshold": 0.80},
    "internal_comments": {"enabled": True, "threshold": 0.75},
}


def load_channel_config() -> dict:
    """Load the channel toggle config from analysis_config.json, or use defaults.

    Missing channels in the file fall back to defaults.
    """
    cfg = {k: dict(v) for k, v in DEFAULT_CHANNEL_CONFIG.items()}
    if ANALYSIS_CONFIG_FILE.exists():
        try:
            with open(ANALYSIS_CONFIG_FILE, encoding="utf-8") as f:
                user_cfg = json.load(f)
            for ch, settings in user_cfg.get("channels", {}).items():
                if ch in cfg and isinstance(settings, dict):
                    cfg[ch].update({k: v for k, v in settings.items() if k != "description"})
        except Exception as exc:
            print(f"  WARNING: failed to read {ANALYSIS_CONFIG_FILE}: {exc}. Using defaults.")
    return cfg


def _print_channel_config(cfg: dict) -> None:
    print("Active matching channels:")
    for ch, settings in cfg.items():
        flag = "ON " if settings.get("enabled") else "off"
        extra = []
        if "threshold" in settings:
            extra.append(f"thr={settings['threshold']}")
        print(f"  [{flag}] {ch:18s} {' '.join(extra)}")


def _kb_fingerprint(pattern_files: list[Path], concept_files: list[Path]) -> str:
    """SHA-256 of all KB file mtimes+sizes — changes when any KB file is updated."""
    h = hashlib.sha256()
    extra = [PATTERN_DESCRIPTIONS_FILE]
    for p in sorted(pattern_files + concept_files + extra):
        if p.exists():
            stat = p.stat()
            h.update(f"{p}:{stat.st_mtime}:{stat.st_size}".encode())
    return h.hexdigest()


def load_kb_embeddings(
    model: SentenceTransformer,
    concept_short_names: list[str],
    concept_summaries: list[str],
    pattern_desc_texts: list[str],
    pattern_files: list[Path],
    concept_files: list[Path],
    concept_internal_keywords: list[str] | None = None,
    concept_internal_comments: list[str] | None = None,
):
    """Return KB embeddings, loading from cache when KB is unchanged.

    Returns
    -------
    name_emb, summary_emb, pattern_desc_emb
        Standard channels — one row per concept (or per pattern, for desc).
    intkw_emb, intkw_concept_idx
        Internal-keyword embeddings, with index list mapping each row back to
        its source concept. Only concepts with non-empty internal_keywords
        contribute; missing concepts are skipped.
    intcmt_emb, intcmt_concept_idx
        Same for internal_comments. ``None`` when the channel has no entries.
    """
    fingerprint = _kb_fingerprint(pattern_files, concept_files)
    intkw_texts = concept_internal_keywords or []
    intcmt_texts = concept_internal_comments or []
    intkw_idx = [i for i, t in enumerate(intkw_texts) if t and t.strip()]
    intcmt_idx = [i for i, t in enumerate(intcmt_texts) if t and t.strip()]
    intkw_payload = [intkw_texts[i] for i in intkw_idx]
    intcmt_payload = [intcmt_texts[i] for i in intcmt_idx]

    if KB_CACHE_FILE.exists():
        try:
            cached = torch.load(KB_CACHE_FILE, weights_only=False)
            if cached.get("fingerprint") == fingerprint:
                print("  KB embeddings loaded from cache.")
                return (
                    cached["name_emb"],
                    cached["summary_emb"],
                    cached["pattern_desc_emb"],
                    cached.get("intkw_emb"),
                    cached.get("intkw_idx", []),
                    cached.get("intcmt_emb"),
                    cached.get("intcmt_idx", []),
                )
        except Exception:
            pass

    print("  Encoding KB entries (first run or KB changed)…")
    name_emb = model.encode(
        [normalize_identifier(n) for n in concept_short_names], convert_to_tensor=True
    )
    summary_emb = model.encode(concept_summaries, convert_to_tensor=True)
    pattern_desc_emb = model.encode(pattern_desc_texts, convert_to_tensor=True)
    intkw_emb = model.encode(intkw_payload, convert_to_tensor=True) if intkw_payload else None
    intcmt_emb = model.encode(intcmt_payload, convert_to_tensor=True) if intcmt_payload else None
    print(f"  Internal-keyword vectors: {len(intkw_idx)} concepts; internal-comment vectors: {len(intcmt_idx)} concepts.")

    KB_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "fingerprint": fingerprint,
            "name_emb": name_emb,
            "summary_emb": summary_emb,
            "pattern_desc_emb": pattern_desc_emb,
            "intkw_emb": intkw_emb,
            "intkw_idx": intkw_idx,
            "intcmt_emb": intcmt_emb,
            "intcmt_idx": intcmt_idx,
        },
        KB_CACHE_FILE,
    )
    print(f"  KB embeddings cached to {KB_CACHE_FILE.name}")
    return name_emb, summary_emb, pattern_desc_emb, intkw_emb, intkw_idx, intcmt_emb, intcmt_idx

NOTEBOOKS_ROOT_DIR = config.PROJECT_ROOT / "converted_notebooks"
OUTPUT_CSV_FILE = config.RESULTS_DIR / "quantum_concept_matches_with_patterns.csv"
UNCLASSIFIED_CONCEPTS_FILE = config.RESULTS_DIR / "unclassified_concepts.csv"

SIMILARITY_THRESHOLDS = {
    "name": 0.85,
    "summary": 0.72,
    "pattern_desc": 0.65,   # comment block vs full pattern description embedding
    "keyword_name": 0.78,   # normalised method name vs keyword embedding
    "title": 0.72,
}

# Seed KB: the five manually curated frameworks. Never modified by the pipeline.
CONCEPT_FILES = [
    config.RESULTS_DIR / "classiq_quantum_concepts.json",
    config.RESULTS_DIR / "pennylane_quantum_concepts.json",
    config.RESULTS_DIR / "qiskit_quantum_concepts.json",
    config.RESULTS_DIR / "qiskit_algorithms_quantum_concepts.json",
    config.RESULTS_DIR / "qiskit_machine_learning_quantum_concepts.json",
]

PATTERN_FILES = [
    config.RESULTS_DIR / "knowledge_base/enriched_classiq_quantum_patterns.csv",
    config.RESULTS_DIR / "knowledge_base/enriched_pennylane_quantum_patterns.csv",
    config.RESULTS_DIR / "knowledge_base/enriched_qiskit_quantum_patterns.csv",
    config.RESULTS_DIR / "knowledge_base/enriched_qiskit_algorithms_quantum_patterns.csv",
    config.RESULTS_DIR / "knowledge_base/enriched_qiskit_machine_learning_quantum_patterns.csv",
]

# Dynamic KB: auto-discovered from data/dynamic_kb/<project>/.
# Each entry is built by scripts/build_dynamic_kbs.py from high-confidence
# name-channel matches found in the project's source code. New projects are
# picked up automatically on the next run — no manual registration needed.
#
# VALIDATION_PROJECTS: held-out frameworks whose notebooks are excluded from
# the main analysis dataset. Their dynamic KBs are still loaded and used when
# the dedicated evaluation recipe explicitly targets them (--target-dir).
# Add new validation frameworks here as they are introduced.
_DYN = config.DYNAMIC_KB_DIR
VALIDATION_PROJECTS: set[str] = {"Qrisp"}
if _DYN.exists():
    for _cf in sorted(_DYN.glob("*/concepts.json")):
        CONCEPT_FILES.append(_cf)
    for _pf in sorted(_DYN.glob("*/patterns.csv")):
        PATTERN_FILES.append(_pf)


# Frameworks with manually-curated ground truth, used by --evaluate-all.
# For each: scan ``target_dir`` and join predictions against ``gt_path`` to
# compute precision/recall/F1 scoped to patterns that appear in the GT
# (frameworks that don't cover all 22 patterns are not penalised for
# patterns they don't target). The KB is built from a different set of
# frameworks (Classiq, PennyLane, Qiskit, qiskit-algorithms, qiskit-ML,
# Qrisp), so these targets are out-of-distribution.
EVAL_TARGETS = [
    {
        "name":        "qiskit-finance",
        "target_dir":  "target_github_projects/qiskit-finance",
        "gt_path":     "data/qiskit_finance_ground_truth.csv",
        "output_path": "data/qiskit_finance_eval_output.csv",
    },
    {
        "name":        "qiskit-machine-learning",
        "target_dir":  "converted_notebooks/qiskit-machine-learning/docs/tutorials",
        "gt_path":     "data/qiskit_machine_learning_ground_truth.csv",
        "output_path": "data/qiskit_ml_eval_output.csv",
    },
    {
        "name":        "Qrisp",
        "target_dir":  "converted_notebooks/Qrisp",
        "gt_path":     "data/qrisp_ground_truth.csv",
        "output_path": "data/qrisp_eval_output.csv",
    },
    {
        "name":        "Qualtran",
        "target_dir":  "converted_notebooks/Qualtran",
        "gt_path":     "data/qualtran_ground_truth.csv",
        "output_path": "data/qualtran_eval_output.csv",
    },
    {
        "name":        "amazon-braket-algorithm-library",
        "target_dir":  "converted_notebooks/amazon-braket-algorithm-library/notebooks/textbook",
        "gt_path":     "data/braket_algorithm_library_ground_truth.csv",
        "output_path": "data/braket_eval_output.csv",
    },
]


def normalize_identifier(name: str) -> str:
    """Normalise a code identifier for embedding.

    Splits snake_case and CamelCase into space-separated lowercase tokens so
    that e.g. ``ApplyQuantumFourierTransform`` and ``apply_qft`` land close to
    ``QFT`` in embedding space.  Applied only to the strings passed to
    ``model.encode()``; original names are preserved in the output CSV.
    """
    # snake_case → tokens
    name = name.replace("_", " ")
    # CamelCase / PascalCase → tokens (insert space before each uppercase run)
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", name)
    return name.lower().strip()


class CodeElementVisitor(ast.NodeVisitor):
    def __init__(self):
        self.found_elements = set()

    def visit_Call(self, node):
        func = node.func
        if isinstance(func, ast.Name):
            self.found_elements.add(func.id)
        elif isinstance(func, ast.Attribute):
            self.found_elements.add(func.attr)
        self.generic_visit(node)


def get_code_elements_from_script(script_content: str) -> list[str]:
    try:
        tree = ast.parse(script_content)
        visitor = CodeElementVisitor()
        visitor.visit(tree)
        return list(visitor.found_elements)
    except SyntaxError:
        return[]


def extract_comments_from_script(file_path: Path) -> str:
    """Concatenate all ``#``-comment lines in the script into a single string.

    Used for whole-file summary matching: the resulting text is embedded once
    and compared against all KB concept summaries.
    """
    comments =[]
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line.startswith("#"):
                    comment_text = stripped_line.lstrip("# ").strip()
                    if comment_text:
                        comments.append(comment_text)
    except Exception as e:
        print(f"Error reading {file_path} for comments: {e}")
    return " ".join(comments)


_BOILERPLATE_RE = re.compile(
    r'^(!|coding[:=]|In\s*\[|#\s*$)', re.IGNORECASE
)


_HEADING_RE = re.compile(r'^#\s+#{1,2}(?!#)\s')


def extract_file_title(file_path: Path) -> str:
    """Return the first ~300 chars of meaningful comments, skipping boilerplate.

    Converted Jupyter notebooks begin with ``#!/usr/bin/env python``,
    ``# coding: utf-8``, then the notebook title as a markdown heading comment
    (``# # Title``).  A heading-first pass scans for the first markdown heading
    (``# # ...`` or ``# ## ...``) and returns it directly, avoiding budget
    exhaustion by preceding license/copyright blocks.  Falls back to the
    general first-comment approach for non-notebook files.
    """
    # Heading-first pass: find the first h1/h2 markdown heading and include the
    # immediately following paragraph lines (up to 300 chars total).
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            found_heading = False
            parts: list[str] =[]
            char_count = 0
            for raw_line in f:
                stripped = raw_line.strip()
                if not found_heading:
                    if _HEADING_RE.match(stripped):
                        text = stripped.lstrip("# ").strip()
                        if text:
                            found_heading = True
                            parts.append(text)
                            char_count += len(text)
                else:
                    if not stripped or stripped == "#":
                        continue
                    if not stripped.startswith("#"):
                        break
                    text = stripped.lstrip("# ").strip()
                    if not text:
                        continue
                    if _BOILERPLATE_RE.match(text) or "<" in text:
                        break
                    parts.append(text)
                    char_count += len(text)
                    if char_count >= 300:
                        break
            if parts:
                return " ".join(parts)[:300]
    except Exception:
        pass

    # Fallback: first ~300 chars of meaningful non-boilerplate comment lines
    lines: list[str] =[]
    char_count = 0
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                stripped = raw_line.strip()
                if not stripped.startswith("#"):
                    if stripped:
                        break
                    continue
                text = stripped.lstrip("# ").strip()
                if not text or _BOILERPLATE_RE.match(text):
                    continue
                lines.append(text)
                char_count += len(text)
                if char_count >= 300:
                    break
    except Exception:
        pass
    return " ".join(lines)[:300]


_DOC_SECTION_HEADERS = re.compile(
    r'^\s*(Parameters|Args|Arguments|Returns|Return|Raises|Attributes|'
    r'Notes|Note|Examples|Example|References|See Also|Todo)\s*[-:—]?\s*$',
    re.IGNORECASE | re.MULTILINE,
)


def _trim_doc(doc: str) -> str:
    """Strip parameter/return/attribute sections. Preserves paragraph breaks."""
    m = _DOC_SECTION_HEADERS.search(doc)
    text = doc[:m.start()].strip() if m else doc.strip()
    # Collapse only intra-line whitespace so paragraph splits still work downstream.
    return re.sub(r'[ \t]+', ' ', text)


def _doc_snippets(name: str, trimmed: str) -> list[str]:
    """Return up to 3 progressively longer views of a trimmed docstring.

    Points: summary line, first paragraph, full trimmed text.
    Duplicates are skipped so a one-liner only produces one snippet.
    """
    seen: set[str] = set()
    result: list[str] = []
    for candidate in [
        trimmed.split('\n')[0].strip(),
        trimmed.split('\n\n')[0].strip(),
        trimmed.strip(),
    ]:
        candidate = re.sub(r'\s+', ' ', candidate)
        labeled = f"{name}: {candidate}" if name else candidate
        if len(candidate) >= 15 and labeled not in seen:
            seen.add(labeled)
            result.append(labeled)
    return result


def extract_defined_docstrings(tree: ast.AST | None, max_chars: int = 3000) -> str:
    """Concatenate trimmed docstrings of every class/function defined in the file.

    Parameter/return/attribute sections are stripped before concatenation so that
    only the conceptual description is embedded. Class docstrings come first.
    """
    if tree is None:
        return ""
    classes: list[tuple[str, str]] = []
    functions: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        doc = ast.get_docstring(node)
        if not doc:
            continue
        trimmed = _trim_doc(doc)
        if len(trimmed) < 20:
            continue
        entry = (node.name, trimmed)
        if isinstance(node, ast.ClassDef):
            classes.append(entry)
        else:
            functions.append(entry)
    if not classes and not functions:
        return ""
    parts: list[str] = []
    char_count = 0
    for name, trimmed in classes + functions:
        flat = re.sub(r'\s+', ' ', trimmed)
        chunk = f"{normalize_identifier(name)}: {flat}"
        parts.append(chunk)
        char_count += len(chunk)
        if char_count >= max_chars:
            break
    return " ".join(parts)[:max_chars]


def extract_defined_docstring_snippets(
    tree: ast.AST | None, max_snippets: int = 12
) -> list[str]:
    """Return multi-point snippets for all defined classes/functions (classes first).

    For each docstring, up to 3 truncation points are generated: summary line,
    first paragraph, and full trimmed text. The defined_doc channel takes the
    max similarity across all snippets instead of embedding one long string.
    """
    if tree is None:
        return []
    classes: list[tuple[str, str]] = []
    functions: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        doc = ast.get_docstring(node)
        if not doc:
            continue
        trimmed = _trim_doc(doc)
        if len(trimmed) < 20:
            continue
        entry = (normalize_identifier(node.name), trimmed)
        if isinstance(node, ast.ClassDef):
            classes.append(entry)
        else:
            functions.append(entry)
    snippets: list[str] = []
    for name, trimmed in classes + functions:
        for s in _doc_snippets(name, trimmed):
            snippets.append(s)
            if len(snippets) >= max_snippets:
                return snippets
    return snippets


def extract_short_name(full_name: str) -> str:
    if not full_name:
        return ""
    return full_name.split("/")[-1].split(".")[-1]


def load_patterns_map(file_paths: list[Path]) -> dict[str, str]:
    pattern_map = {}
    for path in file_paths:
        if not path.exists():
            print(f"Warning: Pattern file not found: {path}")
            continue
        try:
            with open(path, encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=",")
                next(reader)
                for row in reader:
                    if len(row) >= 3:
                        concept_name = row[0].strip()
                        pattern = row[2].strip()
                        if concept_name and pattern:
                            pattern_map[concept_name] = pattern
        except Exception as e:
            print(f"Error loading patterns from {path}: {e}")
    return pattern_map


def load_quantum_concepts(
    file_paths: list[Path], pattern_map: dict[str, str]
) -> list[dict]:
    concepts =[]
    pattern_map_by_short_name = {
        extract_short_name(k): v for k, v in pattern_map.items()
    }

    for path in file_paths:
        if not path.exists():
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if "name" in item and "summary" in item:
                        full_name = item["name"]
                        short_name = extract_short_name(full_name)
                        found_pattern = "N/A"

                        if full_name in pattern_map:
                            found_pattern = pattern_map[full_name]
                        elif short_name in pattern_map_by_short_name:
                            found_pattern = pattern_map_by_short_name[short_name]
                        else:
                            for csv_key, pattern_value in pattern_map.items():
                                if full_name.endswith(csv_key):
                                    found_pattern = pattern_value
                                    break

                        # Determine the source project for per-project KB scoping.
                        # Seed KB paths: /pennylane/..., /qiskit/...
                        # Dynamic KB paths: /dynamic/{project}/{fn}  (new format)
                        #                   /dynamic.{fn}            (legacy)
                        name_parts = full_name.strip("/").split("/")
                        if name_parts[0] == "dynamic" and len(name_parts) >= 2:
                            source_project = name_parts[1]
                        elif name_parts[0].startswith("dynamic."):
                            source_project = "_dynamic_legacy"
                        else:
                            source_project = "_seed"

                        concepts.append(
                            {
                                "name": full_name,
                                "summary": item["summary"],
                                "short_name": short_name,
                                "pattern": found_pattern,
                                "internal_keywords": (item.get("internal_keywords") or "").strip(),
                                "internal_comments": (item.get("internal_comments") or "").strip(),
                                "_source": source_project,
                            }
                        )
        except Exception as e:
            print(f"Error loading {path}: {e}")
    return concepts


def _save_unclassified_concepts(concepts: list[dict], output_path: Path):
    unclassified =[
        {"name": c["name"], "summary": c["summary"]}
        for c in concepts
        if c["pattern"] == "N/A"
    ]

    if not unclassified:
        if output_path.exists():
            output_path.unlink()
        print("All concepts are classified. No 'unclassified_concepts.csv' needed.")
        return

    print(
        f"\nWARNING: Found {len(unclassified)} unclassified concepts. Saving to-do list to '{output_path}'..."
    )
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "summary"])
            writer.writeheader()
            writer.writerows(unclassified)
    except OSError as e:
        print(f"  - Error writing unclassified concepts file: {e}")


def extract_and_save_unique_patterns(input_files: list[Path], output_file: Path):
    unique_patterns = set()
    for path in input_files:
        if not path.exists():
            print(
                f"Warning: Pattern file not found, skipping for unique pattern extraction: {path}"
            )
            continue
        try:
            with open(path, encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=",")
                next(reader)
                for row in reader:
                    if len(row) >= 3:
                        pattern = row[2].strip()
                        if pattern:
                            unique_patterns.add(pattern)
        except Exception as e:
            print(f"Error reading patterns from {path}: {e}")

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["PatternName"])
            for pattern in sorted(list(unique_patterns)):
                writer.writerow([pattern])
        print(f"Saved {len(unique_patterns)} unique patterns to '{output_file}'")
    except Exception as e:
        print(f"Error saving unique patterns to {output_file}: {e}")


def main(
    target_dir: Path | None = None,
    output_file: Path | None = None,
    no_report: bool = False,
):
    scan_dir = target_dir if target_dir else NOTEBOOKS_ROOT_DIR
    out_csv = output_file if output_file else OUTPUT_CSV_FILE
    _is_eval_run = target_dir is not None

    OUTPUT_PATTERN_FILE = config.RESULTS_DIR / "patterns_used_in_categorization.csv"
    extract_and_save_unique_patterns(PATTERN_FILES, OUTPUT_PATTERN_FILE)

    print(f"\nLoading patterns from {len(PATTERN_FILES)} CSV files...")
    pattern_map = load_patterns_map(PATTERN_FILES)
    print(f"Loaded a total of {len(pattern_map)} concept-to-pattern mappings.")

    quantum_concepts = load_quantum_concepts(CONCEPT_FILES, pattern_map)
    if not quantum_concepts:
        print("No quantum concepts loaded. Exiting.")
        return
    print(
        f"Loaded {len(quantum_concepts)} concepts defined across {len(CONCEPT_FILES)} files."
    )

    _save_unclassified_concepts(quantum_concepts, UNCLASSIFIED_CONCEPTS_FILE)

    found_patterns_count = sum(1 for c in quantum_concepts if c["pattern"] != "N/A")
    print("\n--- MAPPING SUMMARY ---")
    print(
        f"Successfully matched {found_patterns_count} / {len(quantum_concepts)} concepts with a pattern."
    )
    print("-----------------------\n")

    print(f"Scanning directory: '{scan_dir}'")
    print(f"Output file: '{out_csv}'")

    channel_cfg = load_channel_config()
    _print_channel_config(channel_cfg)

    # ── Pattern descriptions for pattern_desc channel ─────────────────────────
    pattern_descriptions = []
    if PATTERN_DESCRIPTIONS_FILE.exists():
        pattern_descriptions = load_pattern_descriptions(PATTERN_DESCRIPTIONS_FILE)
        print(f"Loaded {len(pattern_descriptions)} pattern descriptions.")
    else:
        print(f"WARNING: {PATTERN_DESCRIPTIONS_FILE} not found — pattern_desc channel disabled.")

    # Exclusive keywords for post-match veto — auto-generated from KB text by
    # scripts/extract_pattern_keywords.py; not manually curated.
    exclusive_keyword_index: dict[str, frozenset[str]] = {}
    if PATTERN_EXCLUSIVE_KEYWORDS_FILE.exists():
        raw = json.loads(PATTERN_EXCLUSIVE_KEYWORDS_FILE.read_text())
        exclusive_keyword_index = {
            pat: frozenset(words) for pat, words in raw.items() if words
        }
        print(f"Loaded exclusive keyword sets for {len(exclusive_keyword_index)} patterns.")

    pd_pairs = build_pattern_description_texts(pattern_descriptions)   # [(name, text), ...]
    pattern_names_ordered = [name for name, _ in pd_pairs]
    pattern_desc_texts = [text for _, text in pd_pairs]

    print(f"Loading embedding model '{config.EMBEDDING_MODEL_NAME}'...")
    model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)

    concept_short_names = [c["short_name"] for c in quantum_concepts]
    concept_summaries = [c["summary"] for c in quantum_concepts]
    concept_internal_keywords = [c.get("internal_keywords", "") for c in quantum_concepts]
    concept_internal_comments = [c.get("internal_comments", "") for c in quantum_concepts]
    (
        concept_name_embeddings,
        concept_summary_embeddings,
        pattern_desc_embeddings,
        intkw_embeddings,
        intkw_concept_idx,
        intcmt_embeddings,
        intcmt_concept_idx,
    ) = load_kb_embeddings(
        model, concept_short_names, concept_summaries, pattern_desc_texts,
        PATTERN_FILES, CONCEPT_FILES,
        concept_internal_keywords=concept_internal_keywords,
        concept_internal_comments=concept_internal_comments,
    )

    # Python only for now; future work can add Q#, Julia, C++ by extending
    # this list and adding language-specific AST parsers.
    SCAN_EXTENSIONS = ["*.py"]
    # Exclude validation-holdout project directories from the main scan.
    # These projects (e.g. Qrisp) are handled exclusively by their dedicated
    # evaluation recipes and must not appear in the main dataset.
    script_files = [
        f for ext in SCAN_EXTENSIONS for f in scan_dir.rglob(ext)
        if _is_eval_run or f.relative_to(scan_dir).parts[0] not in VALIDATION_PROJECTS
    ]
    total_files = len(script_files)
    if not _is_eval_run and VALIDATION_PROJECTS:
        print(f"Excluding validation projects from main scan: {sorted(VALIDATION_PROJECTS)}")
    print(f"Found {total_files} Python files to analyze.")

    import numpy as _np

    # === MULTITHREADING SETUP ===
    # Force PyTorch to use 1 thread per worker to prevent CPU thrashing on your 4-core i5
    torch.set_num_threads(1)

    best_matches: dict[tuple[str, str], dict] = {}

    # Define the worker function inside main() so it inherits all your variables
    def process_file_worker(file_path: Path):
        local_matches = {}
        try:
            script_content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Could not read file {file_path}: {e}")
            return local_matches

        relative_path = str(file_path.relative_to(scan_dir))

        # All dynamic KB concepts are eligible for every file — seed + the full
        # extended KB built across all projects. This ensures the main analysis
        # and evaluation use the same KB, which is required for consistency.
        _eligible = _np.arange(len(quantum_concepts), dtype=_np.int64)
        _eligible_set = set(_eligible.tolist())

        # ── Name-based matching ──
        try:
            tree = ast.parse(script_content)
        except SyntaxError:
            tree = None

        located_elements: list[tuple[str, int]] =[]
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    name = None
                    if isinstance(func, ast.Name):
                        name = func.id
                    elif isinstance(func, ast.Attribute):
                        name = func.attr
                    if name:
                        located_elements.append((name, getattr(node, 'lineno', 0)))

        # Compute element-name embeddings once if any name-side channel needs them.
        code_element_embeddings = None
        intkw_active = (
            channel_cfg["internal_keywords"]["enabled"]
            and intkw_embeddings is not None
            and len(intkw_concept_idx) > 0
        )
        if located_elements and (channel_cfg["name"]["enabled"] or intkw_active):
            element_names = [e[0] for e in located_elements]
            code_element_embeddings = model.encode(
                [normalize_identifier(n) for n in element_names], convert_to_tensor=True
            )

        if located_elements and channel_cfg["name"]["enabled"] and code_element_embeddings is not None:
            _name_emb = concept_name_embeddings[_eligible]
            cosine_sim_names = 1 - cdist(
                code_element_embeddings.cpu(), _name_emb.cpu(), "cosine"
            )
            for elem_idx, (element, lineno) in enumerate(located_elements):
                for local_idx, concept_idx in enumerate(_eligible):
                    score = float(cosine_sim_names[elem_idx, local_idx])
                    if score >= channel_cfg["name"]["threshold"]:
                        concept = quantum_concepts[concept_idx]
                        key = (relative_path, concept["name"])
                        if key not in local_matches or score > local_matches[key]["score"]:
                            local_matches[key] = {
                                "file_path": relative_path, "concept_name": concept["name"],
                                "pattern": concept["pattern"], "match_type": "name",
                                "matched_text": element, "score": score, "first_line": lineno,
                            }

        # ── Internal-keywords channel (per concept's variable/return-type tokens) ──
        # For each AST call-site name, compare its embedding against the
        # internal_keywords vector of every concept that has one. This rewards
        # framework-specific tokens (BaseEstimatorV2, _input_params...) that
        # never reach the high-level `name` channel.
        if intkw_active and code_element_embeddings is not None:
            _intkw_cols = [i for i, cidx in enumerate(intkw_concept_idx) if cidx in _eligible_set]
            if _intkw_cols:
                _intkw_emb = intkw_embeddings[_intkw_cols]
                cosine_sim_intkw = 1 - cdist(
                    code_element_embeddings.cpu(), _intkw_emb.cpu(), "cosine"
                )
                thr = channel_cfg["internal_keywords"]["threshold"]
                for elem_idx, (element, lineno) in enumerate(located_elements):
                    for local_col, col_idx in enumerate(_intkw_cols):
                        score = float(cosine_sim_intkw[elem_idx, local_col])
                        if score >= thr:
                            concept = quantum_concepts[intkw_concept_idx[col_idx]]
                            key = (relative_path, concept["name"])
                            if key not in local_matches or score > local_matches[key]["score"]:
                                local_matches[key] = {
                                    "file_path": relative_path,
                                    "concept_name": concept["name"],
                                    "pattern": concept["pattern"],
                                    "match_type": "internal_keywords",
                                    "matched_text": element[:80],
                                    "score": score,
                                    "first_line": lineno,
                                }

        # ── Summary-based matching ──
        comment_block = extract_comments_from_script(file_path)
        comment_embedding = None
        needs_comment_emb = channel_cfg["summary"]["enabled"] or channel_cfg["pattern_desc"]["enabled"]
        truncated_comment = ""
        
        if comment_block and needs_comment_emb:
            comment_embedding = model.encode([comment_block], convert_to_tensor=True)
            truncated_comment = (comment_block[:150] + "...") if len(comment_block) > 150 else comment_block
            
        if comment_block and channel_cfg["summary"]["enabled"] and comment_embedding is not None:
            _sum_emb = concept_summary_embeddings[_eligible]
            cosine_sim_summaries = 1 - cdist(comment_embedding.cpu(), _sum_emb.cpu(), "cosine")
            for local_idx, concept_idx in enumerate(_eligible):
                score = float(cosine_sim_summaries[0, local_idx])
                if score >= channel_cfg["summary"]["threshold"]:
                    concept = quantum_concepts[concept_idx]
                    key = (relative_path, concept["name"])
                    if key not in local_matches or score > local_matches[key]["score"]:
                        local_matches[key] = {
                            "file_path": relative_path, "concept_name": concept["name"],
                            "pattern": concept["pattern"], "match_type": "summary",
                            "matched_text": truncated_comment.replace(";", ","), "score": score, "first_line": 0,
                        }

        # ── Internal-comments channel (target file's comments vs per-concept inline comments) ──
        if (
            comment_block
            and comment_embedding is not None
            and channel_cfg["internal_comments"]["enabled"]
            and intcmt_embeddings is not None
            and len(intcmt_concept_idx) > 0
        ):
            _intcmt_cols = [i for i, cidx in enumerate(intcmt_concept_idx) if cidx in _eligible_set]
            if _intcmt_cols:
                _intcmt_emb = intcmt_embeddings[_intcmt_cols]
                cosine_sim_intcmt = 1 - cdist(
                    comment_embedding.cpu(), _intcmt_emb.cpu(), "cosine"
                )
                thr = channel_cfg["internal_comments"]["threshold"]
                for local_col, col_idx in enumerate(_intcmt_cols):
                    score = float(cosine_sim_intcmt[0, local_col])
                    if score >= thr:
                        concept = quantum_concepts[intcmt_concept_idx[col_idx]]
                        key = (relative_path, concept["name"])
                        if key not in local_matches or score > local_matches[key]["score"]:
                            local_matches[key] = {
                                "file_path": relative_path,
                                "concept_name": concept["name"],
                                "pattern": concept["pattern"],
                                "match_type": "internal_comments",
                                "matched_text": truncated_comment.replace(";", ","),
                                "score": score,
                                "first_line": 0,
                            }

        # ── Title-based matching ──
        file_title = extract_file_title(file_path) if channel_cfg["title"]["enabled"] else ""
        if file_title:
            title_embedding = model.encode([file_title], convert_to_tensor=True)
            _sum_emb_t = concept_summary_embeddings[_eligible]
            cosine_sim_title = 1 - cdist(title_embedding.cpu(), _sum_emb_t.cpu(), "cosine")
            truncated_title = (file_title[:150] + "...") if len(file_title) > 150 else file_title
            for local_idx, concept_idx in enumerate(_eligible):
                score = float(cosine_sim_title[0, local_idx])
                if score >= channel_cfg["title"]["threshold"]:
                    concept = quantum_concepts[concept_idx]
                    key = (relative_path, concept["name"])
                    if key not in local_matches or score > local_matches[key]["score"]:
                        local_matches[key] = {
                            "file_path": relative_path, "concept_name": concept["name"],
                            "pattern": concept["pattern"], "match_type": "title",
                            "matched_text": truncated_title.replace(";", ","), "score": score, "first_line": 0,
                        }

        # ── Defined-class/function docstring matching ──
        if channel_cfg["defined_doc"]["enabled"]:
            snippets = extract_defined_docstring_snippets(tree)
            if snippets:
                snippet_embeddings = model.encode(snippets, convert_to_tensor=True)
                _sum_emb_d = concept_summary_embeddings[_eligible]
                cosine_sims = 1 - cdist(snippet_embeddings.cpu(), _sum_emb_d.cpu(), "cosine")
                best_scores = cosine_sims.max(axis=0)  # max over snippets per eligible concept
                truncated_defined = (snippets[0][:150] + "...") if len(snippets[0]) > 150 else snippets[0]
                for local_idx, concept_idx in enumerate(_eligible):
                    score = float(best_scores[local_idx])
                    if score >= channel_cfg["defined_doc"]["threshold"]:
                        concept = quantum_concepts[concept_idx]
                        key = (relative_path, concept["name"])
                        if key not in local_matches or score > local_matches[key]["score"]:
                            local_matches[key] = {
                                "file_path": relative_path, "concept_name": concept["name"],
                                "pattern": concept["pattern"], "match_type": "defined_doc",
                                "matched_text": truncated_defined.replace(";", ","), "score": score, "first_line": 0,
                            }

        # ── Pattern-description matching ──
        if (channel_cfg["pattern_desc"]["enabled"] and comment_block and comment_embedding is not None 
            and pattern_desc_embeddings is not None and len(pattern_desc_texts) > 0):
            cosine_sim_pd = 1 - cdist(comment_embedding.cpu(), pattern_desc_embeddings.cpu(), "cosine")
            for pd_idx, pd_name in enumerate(pattern_names_ordered):
                score = float(cosine_sim_pd[0, pd_idx])
                if score >= channel_cfg["pattern_desc"]["threshold"]:
                    key = (relative_path, f"pattern:{pd_name}")
                    if key not in local_matches or score > local_matches[key]["score"]:
                        local_matches[key] = {
                            "file_path": relative_path, "concept_name": f"pattern:{pd_name}",
                            "pattern": pd_name, "match_type": "pattern_desc",
                            "matched_text": truncated_comment.replace(";", ",") if comment_block else "",
                            "score": score, "first_line": 0,
                        }

        # ── Keyword veto ──────────────────────────────────────────────────────
        # Drops matches from broad semantic text channels (summary, title,
        # defined_doc, pattern_desc) when no exclusive keyword for the matched
        # pattern appears anywhere in the file text.  Exclusive keywords are
        # auto-generated from KB concept text by extract_pattern_keywords.py
        # (words that appear in ≤2 patterns — discriminating, not generic).
        # Name and internal-signal channels are already high-precision and exempt.
        veto_cfg = channel_cfg.get("keyword_veto", {})
        if veto_cfg.get("enabled", False) and exclusive_keyword_index:
            veto_channels = {"summary", "title", "defined_doc", "pattern_desc"}
            file_text_lower = script_content.lower()
            vetoed_keys = []
            for key, match in local_matches.items():
                if match["match_type"] not in veto_channels:
                    continue
                pattern = match["pattern"]
                excl = exclusive_keyword_index.get(pattern)
                if not excl:
                    continue  # no exclusive keywords defined → cannot veto
                if not any(kw in file_text_lower for kw in excl):
                    vetoed_keys.append(key)
            for key in vetoed_keys:
                del local_matches[key]

        return local_matches

    # === EXECUTE POOL ===
    print("Starting thread pool processing...")
    # max_workers=4 matches your physical core count perfectly
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_file_worker, fp): fp for fp in script_files}
        
        for i, future in enumerate(as_completed(futures)):
            if (i + 1) % 100 == 0 or (i + 1) == total_files:
                print(f"Processing {i + 1}/{total_files}...")
            
            try:
                # Merge the worker's results into the global dict
                local_results = future.result()
                for key, match in local_results.items():
                    if key not in best_matches or match["score"] > best_matches[key]["score"]:
                        best_matches[key] = match
            except Exception as e:
                print(f"Error processing file: {e}")

    # Sort by file then by position within the file so that the CSV naturally
    # reflects the order in which concepts appear — ready for sequence analysis.
    sorted_rows = sorted(
        best_matches.values(), key=lambda r: (r["file_path"], r["first_line"])
    )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
                "file_path",
                "concept_name",
                "pattern",
                "match_type",
                "matched_text",
                "similarity_score",
                "first_line",
            ]
        )
        for row in sorted_rows:
            writer.writerow(
                [
                    row["file_path"],
                    row["concept_name"],
                    row["pattern"],
                    row["match_type"],
                    row["matched_text"],
                    f"{row['score']:.4f}",
                    row["first_line"],
                ]
            )

    print(
        f"Analysis complete. Results saved to '{out_csv}' "
        f"({len(best_matches)} unique file–concept pairs across {total_files} files)."
    )

    if not no_report:
        _generate_final_report()

    if no_report:
        return

    archive_run(
        out_csv=out_csv,
        scan_dir=scan_dir,
        channel_cfg=channel_cfg,
        n_files_scanned=total_files,
        n_pairs=len(best_matches),
    )


def _generate_final_report() -> None:
    """Run generate_report.main() so the txt/md outputs stay in sync with the CSV."""
    print("\n>>> Generating final pattern report...")
    try:
        from src.analysis.generate_report import main as _gen_main
        _gen_main()
    except Exception as exc:
        print(f"  WARNING: report generation failed: {exc}")


def archive_run(
    out_csv: Path,
    scan_dir: Path,
    channel_cfg: dict,
    n_files_scanned: int,
    n_pairs: int,
) -> None:
    """Snapshot every run to data/runs/<run_id>/ for traceability.

    A run_id is the run timestamp + a short hash of the active channel config,
    so two configs run at different times are guaranteed distinct, and two
    identical configs run at the same minute (rare) still differ by seconds.
    Stored: the output CSV, the active config (channels + KB SHA), and a
    summary JSON with file/pattern counts.
    """
    import datetime
    import shutil
    import subprocess

    if not out_csv.exists():
        return
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    cfg_hash = hashlib.sha1(
        json.dumps(channel_cfg, sort_keys=True, default=str).encode()
    ).hexdigest()[:6]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{timestamp}_{cfg_hash}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Copy the output CSV
    shutil.copy2(out_csv, run_dir / "matches.csv")

    # Copy the report files if they exist (they're generated just before archive)
    report_txt = config.RESULTS_DIR / "final_pattern_report.txt"
    report_md = config.DOCS_DIR / "final_pattern_report.md" if hasattr(config, "DOCS_DIR") else None
    if report_txt.exists():
        shutil.copy2(report_txt, run_dir / "final_pattern_report.txt")
    if report_md is not None and report_md.exists():
        shutil.copy2(report_md, run_dir / "final_pattern_report.md")
    report_csv_dir = config.RESULTS_DIR / "report"
    if report_csv_dir.exists() and report_csv_dir.is_dir():
        dest = run_dir / "report_tables"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(report_csv_dir, dest)

    # Capture git SHA (if available) for full reproducibility
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=False,
        ).stdout.strip() or None
    except Exception:
        sha = None

    # Compute summary stats from the CSV
    pattern_counts: dict[str, int] = {}
    channel_counts: dict[str, int] = {}
    files = set()
    projects = set()
    seen_pairs = set()
    with open(out_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            files.add(row["file_path"])
            projects.add(row["file_path"].split("/", 1)[0])
            channel_counts[row["match_type"]] = channel_counts.get(row["match_type"], 0) + 1
            pair = (row["file_path"], row["pattern"])
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                pattern_counts[row["pattern"]] = pattern_counts.get(row["pattern"], 0) + 1

    summary = {
        "run_id": run_id,
        "timestamp": timestamp,
        "git_sha": sha,
        "scan_dir": str(scan_dir),
        "files_scanned": n_files_scanned,
        "files_matched": len(files),
        "projects_matched": len(projects),
        "unique_file_pattern_pairs": len(seen_pairs),
        "raw_rows": sum(channel_counts.values()),
        "pattern_counts": dict(sorted(pattern_counts.items(), key=lambda x: -x[1])),
        "channel_counts": dict(sorted(channel_counts.items(), key=lambda x: -x[1])),
        "channel_config": channel_cfg,
    }
    with open(run_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    with open(run_dir / "channel_config.json", "w", encoding="utf-8") as f:
        json.dump(channel_cfg, f, indent=2, default=str)

    # Update / create a "latest" pointer for convenience
    latest_link = RUNS_DIR / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    try:
        latest_link.symlink_to(run_id)
    except OSError:
        # Fallback: write a text file with the run_id (Windows / restricted FS)
        (RUNS_DIR / "latest.txt").write_text(run_id, encoding="utf-8")

    print(f"Run archived to: {run_dir}")
    print(f"  → matches.csv, summary.json, channel_config.json")


def _print_framework_summary(name: str, agg, per_pattern) -> None:
    """Per-framework summary table — only patterns present in the GT."""
    import math

    def _f(v: float) -> str:
        return f"{v:.3f}" if not math.isnan(v) else "  — "

    cov_pct = (agg.total_predicted / agg.total_gt * 100) if agg.total_gt else 0.0
    print(f"\n{'=' * 80}")
    print(f"  Evaluation: {name}")
    print(f"{'=' * 80}")
    print(f"  GT files:          {agg.total_gt}")
    print(f"  Predicted:         {agg.total_predicted} ({cov_pct:.0f} %)")
    print(f"  Missed:            {agg.total_missed}")
    print(f"  Correct (TP):      {agg.total_tp}")
    print(f"  Micro  P/R/F1:     {agg.micro_precision:.3f} / {agg.micro_recall:.3f} / {agg.micro_f1:.3f}")
    print(f"  Macro  P/R/F1:     {agg.macro_precision:.3f} / {agg.macro_recall:.3f} / {agg.macro_f1:.3f}")
    print()
    print(f"  {'Pattern':<48} {'GT':>4} {'Pred':>5} {'TP':>4} {'FP':>4} {'FN':>4} {'Prec':>6} {'Rec':>6} {'F1':>6}")
    print(f"  {'-' * 100}")
    for m in sorted(per_pattern, key=lambda x: x.gt_count, reverse=True):
        print(
            f"  {m.pattern:<48} {m.gt_count:>4} {m.pred_count:>5} {m.tp:>4} {m.fp:>4} {m.fn:>4}"
            f" {_f(m.precision):>6} {_f(m.recall):>6} {_f(m.f1):>6}"
        )


def _print_cross_framework_summary(results: list) -> None:
    """Aggregate table across all evaluated frameworks."""
    if not results:
        print("\nNo frameworks evaluated.")
        return
    print(f"\n{'=' * 100}")
    print("  CROSS-FRAMEWORK COMPARISON  (precision/recall scoped to patterns in each GT)")
    print(f"{'=' * 100}")
    print(
        f"  {'Framework':<35} {'GT':>4} {'Pred':>5} {'TP':>4}"
        f"  {'Micro-P':>8} {'Micro-R':>8} {'Micro-F1':>9}"
        f"  {'Macro-P':>8} {'Macro-R':>8} {'Macro-F1':>9}"
    )
    print(f"  {'-' * 110}")
    weighted_tp = weighted_gt = weighted_pred_files = 0
    for name, agg, _ in results:
        print(
            f"  {name:<35} {agg.total_gt:>4} {agg.total_predicted:>5} {agg.total_tp:>4}"
            f"  {agg.micro_precision:>8.3f} {agg.micro_recall:>8.3f} {agg.micro_f1:>9.3f}"
            f"  {agg.macro_precision:>8.3f} {agg.macro_recall:>8.3f} {agg.macro_f1:>9.3f}"
        )
        weighted_tp += agg.total_tp
        weighted_gt += agg.total_gt
        weighted_pred_files += agg.total_predicted
    if weighted_gt > 0:
        # GT-weighted aggregate: each (file,pattern) pair contributes equally.
        # FP-aware micro requires per-pattern data; we approximate by averaging
        # the per-framework micro values weighted by GT count for context.
        wp = sum(agg.micro_precision * agg.total_gt for _, agg, _ in results) / weighted_gt
        wr = weighted_tp / weighted_gt
        wf = (2 * wp * wr / (wp + wr)) if (wp + wr) > 0 else 0.0
        print(f"  {'-' * 110}")
        print(
            f"  {'WEIGHTED AVG (by GT count)':<35} {weighted_gt:>4} {weighted_pred_files:>5} {weighted_tp:>4}"
            f"  {wp:>8.3f} {wr:>8.3f} {wf:>9.3f}"
        )
    print()


def run_all_frameworks(skip_analysis: bool = False) -> None:
    """Run analysis on every framework in EVAL_TARGETS and print metrics.

    Precision/recall/F1 are computed by ``src.evaluation.metrics.compute_metrics``,
    which already restricts the pattern universe to those present in each GT
    file. So a framework like Qiskit Finance (no QML patterns) is never
    penalised for not predicting QNN.
    """
    from src.evaluation.metrics import compute_metrics, join_predictions

    results: list[tuple[str, "AggregateMetrics", list]] = []

    for tgt in EVAL_TARGETS:
        name = tgt["name"]
        target_dir = (config.PROJECT_ROOT / tgt["target_dir"]).resolve()
        gt_path = (config.PROJECT_ROOT / tgt["gt_path"]).resolve()
        output_path = (config.PROJECT_ROOT / tgt["output_path"]).resolve()

        if not gt_path.exists():
            print(f"\n[SKIP] {name}: GT not found — {gt_path}")
            continue
        if not target_dir.exists():
            print(f"\n[SKIP] {name}: target dir not found — {target_dir}")
            continue

        if skip_analysis:
            if not output_path.exists():
                print(f"\n[SKIP] {name}: --skip-analysis set but {output_path} not found.")
                continue
            print(f"\n>>> Reusing existing predictions for {name}: {output_path.name}")
        else:
            print(f"\n{'#' * 80}")
            print(f"# Analyzing {name}")
            print(f"#   target: {target_dir}")
            print(f"#   output: {output_path}")
            print(f"{'#' * 80}")
            main(target_dir=target_dir, output_file=output_path)

        eval_df = join_predictions(str(gt_path), str(output_path))
        per_pattern, agg = compute_metrics(eval_df)
        _print_framework_summary(name, agg, per_pattern)
        results.append((name, agg, per_pattern))

    _print_cross_framework_summary(results)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run quantum concept semantic analysis on Python files."
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        default=None,
        help=(
            "Path to the directory of Python files to analyze. "
            "Defaults to 'converted_notebooks/' if not specified."
        ),
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        default=False,
        help="Skip final report generation and run archiving (useful for batch experiments).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Path for the output CSV file. "
            "Defaults to 'data/quantum_concept_matches_with_patterns.csv'."
        ),
    )
    parser.add_argument(
        "--evaluate-all",
        action="store_true",
        help=(
            "Iterate over every framework in EVAL_TARGETS, run analysis, "
            "and print per-framework + cross-framework precision/recall/F1 "
            "scoped to patterns present in each ground truth."
        ),
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="With --evaluate-all, reuse existing eval CSVs instead of re-running analysis.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    import time
    from datetime import timedelta

    start_time = time.time()

    args = _parse_args()
    if args.evaluate_all:
        run_all_frameworks(skip_analysis=args.skip_analysis)
    else:
        target = Path(args.target_dir).resolve() if args.target_dir else None
        output = Path(args.output).resolve() if args.output else None
        main(target_dir=target, output_file=output, no_report=args.no_report)

    elapsed = time.time() - start_time
    print(f"\nTotal execution time: {timedelta(seconds=int(elapsed))} ({elapsed:.2f} seconds)")
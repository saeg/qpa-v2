"""Extract and rank the most frequent keywords per quantum pattern.

For every concept in the knowledge base, collects all available text
(summary, docstring, internal_keywords, internal_comments) and tokenizes it.
Tokens are filtered against Python language keywords, common builtins, and
English stop words. The surviving tokens are counted per pattern across all
its associated concepts. The final output lists each pattern with its most
frequent non-repeating keywords.

Usage:
    .venv/bin/python scripts/extract_pattern_keywords.py
    .venv/bin/python scripts/extract_pattern_keywords.py --top 20 --output data/pattern_keywords.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.conf import config
from src.analysis.run import load_patterns_map, load_quantum_concepts, CONCEPT_FILES, PATTERN_FILES

# ── Stop-word lists ────────────────────────────────────────────────────────────

PYTHON_KEYWORDS: frozenset[str] = frozenset({
    "false", "none", "true", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield",
})

PYTHON_BUILTINS: frozenset[str] = frozenset({
    "self", "cls", "str", "int", "float", "bool", "list", "dict", "tuple",
    "set", "type", "object", "super", "print", "len", "range", "isinstance",
    "hasattr", "getattr", "setattr", "property", "staticmethod", "classmethod",
    "init", "repr", "call", "getitem", "setitem", "iter", "next", "new",
    "value", "values", "items", "keys", "append", "extend", "copy", "get",
    "none", "true", "false", "optional", "union", "any", "callable",
    "abstractmethod", "overload", "final",
})

ENGLISH_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "can", "this", "that",
    "these", "those", "which", "who", "what", "when", "where", "how", "why",
    "all", "each", "both", "few", "more", "most", "other", "some", "such",
    "no", "not", "only", "same", "so", "than", "too", "very", "just",
    "its", "it", "if", "then", "into", "over", "after", "also", "about",
    "any", "given", "used", "use", "using", "based", "well", "see", "also",
    "note", "via", "i", "e", "g", "etc", "ie", "eg", "ref", "fig",
    "following", "according", "whether", "between", "however", "thus",
    "therefore", "hence", "whereas", "while", "where", "can", "one", "two",
    "three", "each", "up", "out", "as", "at", "be", "do", "go", "he",
    "her", "him", "his", "me", "my", "our", "she", "their", "them", "they",
    "us", "we", "you", "your", "new", "set", "get", "run", "add", "per",
    "number", "numbers", "array", "arrays", "result", "results",
    "input", "output", "return", "returns", "method", "methods", "function",
    "functions", "class", "classes", "object", "objects",
    # Noise from dynamic KB summary template ("X: implementation of the Y pattern.")
    "implementation", "implements", "pattern", "patterns",
    # Generic quantum/computing terms that appear in every pattern
    "quantum", "circuit", "algorithm", "algorithms", "applies", "apply",
    # URL / code-comment artifacts
    "https", "http", "www", "org", "wiki", "wikipedia", "arxiv",
    "pylint", "disable", "com", "html", "doi",
})

ALL_STOP_WORDS: frozenset[str] = PYTHON_KEYWORDS | PYTHON_BUILTINS | ENGLISH_STOP_WORDS

# Tokens shorter than this are always dropped.
MIN_TOKEN_LEN = 3

# Regex that splits text into alphanumeric tokens (handles camelCase too).
_SPLIT_RE = re.compile(r'[^a-zA-Z0-9]+')
_CAMEL_RE = re.compile(r'([a-z])([A-Z])')


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase tokens, decomposing camelCase and snake_case."""
    if not text:
        return []
    # Decompose camelCase before splitting on non-alpha chars.
    expanded = _CAMEL_RE.sub(r'\1 \2', text)
    raw = _SPLIT_RE.split(expanded.lower())
    return [t for t in raw if len(t) >= MIN_TOKEN_LEN and t not in ALL_STOP_WORDS]


def _concept_text(concept: dict) -> str:
    """Concatenate all available text fields of a concept."""
    return " ".join(filter(None, [
        concept.get("summary", ""),
        concept.get("docstring", ""),
        concept.get("internal_keywords", ""),
        concept.get("internal_comments", ""),
    ]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=30,
                        help="Number of top keywords to show per pattern (default: 30)")
    parser.add_argument("--output", type=str, default=None,
                        help="Optional path to save results as JSON")
    parser.add_argument("--min-count", type=int, default=2,
                        help="Minimum token count to include in output (default: 2)")
    args = parser.parse_args()

    # ── Load KB ────────────────────────────────────────────────────────────────
    print("Loading knowledge base…")
    pattern_map = load_patterns_map(PATTERN_FILES)
    concepts = load_quantum_concepts(CONCEPT_FILES, pattern_map)
    concepts = [c for c in concepts if c.get("pattern") not in (None, "N/A", "")]
    print(f"  {len(concepts)} concepts with a valid pattern assignment.")

    patterns_found = sorted(set(c["pattern"] for c in concepts))
    print(f"  {len(patterns_found)} distinct patterns.")

    # ── Count tokens per pattern ───────────────────────────────────────────────
    token_counts: dict[str, Counter] = defaultdict(Counter)
    concept_counts: dict[str, int] = Counter()

    for concept in concepts:
        pattern = concept["pattern"]
        text = _concept_text(concept)
        tokens = _tokenize(text)
        token_counts[pattern].update(tokens)
        concept_counts[pattern] += 1

    # ── Build output ───────────────────────────────────────────────────────────
    results: dict[str, list[dict]] = {}
    for pattern in sorted(patterns_found):
        counter = token_counts[pattern]
        top_tokens = [
            {"word": word, "count": count}
            for word, count in counter.most_common()
            if count >= args.min_count
        ][: args.top]
        results[pattern] = top_tokens

    # ── Print ──────────────────────────────────────────────────────────────────
    print()
    print(f"{'='*80}")
    print(f"  Top {args.top} keywords per pattern  (min_count={args.min_count})")
    print(f"{'='*80}")
    for pattern, tokens in results.items():
        n_concepts = concept_counts[pattern]
        words = ", ".join(f"{t['word']}({t['count']})" for t in tokens)
        print(f"\n[{pattern}]  ({n_concepts} concepts)")
        print(f"  {words}")

    # ── Compute cross-pattern exclusivity ─────────────────────────────────────
    # For each word, record which patterns it appears in (across the top-N list).
    word_to_patterns: dict[str, set[str]] = defaultdict(set)
    for pattern, tokens in results.items():
        for t in tokens:
            word_to_patterns[t["word"]].add(pattern)

    # Exclusive = appears in at most MAX_SHARED_PATTERNS patterns.
    MAX_SHARED_PATTERNS = 2
    exclusive: dict[str, list[str]] = {
        pat: [
            t["word"] for t in tokens
            if len(word_to_patterns[t["word"]]) <= MAX_SHARED_PATTERNS
        ]
        for pat, tokens in results.items()
    }

    print()
    print(f"{'='*80}")
    print(f"  Exclusive keywords per pattern  (appear in ≤{MAX_SHARED_PATTERNS} patterns)")
    print(f"{'='*80}")
    for pattern, words in exclusive.items():
        print(f"\n[{pattern}]  ({len(words)} exclusive keywords)")
        print(f"  {', '.join(words[:15])}")

    # ── Save ───────────────────────────────────────────────────────────────────
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        simple = {pat: [t["word"] for t in tokens] for pat, tokens in results.items()}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(simple, f, indent=2)
        print(f"\nSaved to {out_path}")

        # Always write the exclusive-keyword companion file next to the main output.
        excl_path = out_path.parent / (out_path.stem + "_exclusive" + out_path.suffix)
        with open(excl_path, "w", encoding="utf-8") as f:
            json.dump(exclusive, f, indent=2)
        print(f"Saved exclusive keywords to {excl_path}")


if __name__ == "__main__":
    main()

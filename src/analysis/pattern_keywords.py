"""
Utilities for loading pattern descriptions for the pattern_desc channel.

Provides:
  - load_pattern_descriptions()      — load pattern_descriptions.json
  - build_pattern_description_texts() — list of (name, text) for embedding
"""

import json
import re
from pathlib import Path

# ── Stopword list ─────────────────────────────────────────────────────────────

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "it", "its", "this",
    "that", "these", "those", "not", "no", "nor", "so", "yet", "both",
    "either", "each", "any", "all", "both", "few", "more", "most", "other",
    "such", "than", "too", "very", "just", "also", "well", "more", "about",
    "above", "after", "before", "between", "into", "through", "during",
    "while", "when", "where", "which", "who", "whom", "how", "what", "if",
    "then", "up", "down", "out", "over", "under", "again", "further",
    "once", "only", "same", "because", "until", "though", "although",
    "using", "used", "use", "uses", "applied", "apply", "given", "via",
    "e.g", "i.e", "etc", "vs", "per",
}


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_pattern_descriptions(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_pattern_description_texts(descriptions: list[dict]) -> list[tuple[str, str]]:
    """Return list of (pattern_name, combined_text) for embedding.

    Combines intent + context + solution — the most semantically rich fields.
    """
    results = []
    for d in descriptions:
        parts = [
            d.get("intent", ""),
            d.get("context", ""),
            d.get("solution", ""),
            d.get("results", ""),
        ]
        text = " ".join(p for p in parts if p).strip()
        results.append((d["name"], text))
    return results


# ── Keyword extraction (used by scripts outside run.py) ───────────────────────

def extract_keywords_from_text(text: str, n: int = 10) -> list[str]:
    """Tokenise text, remove stopwords, return the top-n most frequent tokens."""
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]*", text.lower())
    filtered = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    freq: dict[str, int] = {}
    for t in filtered:
        freq[t] = freq.get(t, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])][:n]

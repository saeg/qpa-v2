# qpa - Quantum Patterns Analyzer

qpa is an open-source Python tool that mines quantum computing pattern usage from open-source projects. It builds a knowledge base from major quantum frameworks, discovers and clones relevant GitHub repositories, and uses semantic search to detect pattern implementations in Jupyter Notebooks.

The full pipeline runs end-to-end with a single command:

```bash
just all
```

## How it works

The tool operates in three stages:

**Stage 1 - Data collection.** The GitHub API is queried to find Python-based quantum repositories (filtered by stars, contributors, and activity). Repositories are cloned locally and the PlanQK Pattern Atlas is downloaded.

**Stage 2 - Knowledge base construction.** Core quantum concepts are extracted from five seed frameworks (Qiskit, PennyLane, Classiq, Qiskit Algorithms, Qiskit Machine Learning) and classified against the pattern catalog. A *dynamic KB* is then built automatically: for each target project, qpa scans its library source code and promotes public functions whose docstrings semantically match a seed KB concept into a project-specific extension of the KB.

**Stage 3 - Pattern detection.** Jupyter Notebooks are converted to Python scripts and scanned across seven semantic channels. Results are aggregated into a structured report.

### Matching channels

| Channel | Threshold | What is matched |
|---|---|---|
| `name` | 0.88 | AST-extracted function call names vs. KB concept short names |
| `summary` | 0.78 | File comment block vs. KB concept docstring summaries |
| `title` | 0.76 | Notebook heading vs. KB concept summaries |
| `pattern_desc` | 0.80 | File comment block vs. pattern intent text |
| `defined_doc` | 0.85 | Docstrings of classes/functions *defined* in the file vs. KB summaries |
| `internal_keywords` | 0.78 | KB concept internal token signatures vs. call-site names |
| `internal_comments` | 0.75 | KB concept inline comments vs. file comment block |

Thresholds are runtime-tunable in `data/analysis_config.json` without code changes.

### Two-phase pipeline

Phase 1 (`just build-dynamic-kbs`) scans each target project's library source with the seed KB and writes a project-specific dynamic KB under `data/dynamic_kb/<project>/`. Phase 2 (`just run_main`) runs the full seven-channel analysis on converted notebooks, loading both the seed KB and all dynamic KBs automatically.

## Current dataset

| Metric | Value |
|---|---|
| Projects searched | 84 |
| Python scripts analyzed | 1,363 |
| Projects with matches | 41 |
| Total pattern instances | 3,593 |
| Files with matches | 576 |
| Patterns detected (of 22) | 22 |
| Avg. similarity score | 0.894 |

**Qrisp held-out evaluation** (framework excluded from the KB):

| | Precision | Recall | F1 |
|---|---|---|---|
| Micro | 0.800 | 0.667 | 0.727 |
| Macro | 0.705 | 0.564 | 0.611 |

## Requirements

- Python 3.12+
- [just](https://github.com/casey/just#installation) command runner
- Git
- A GitHub Personal Access Token in `.env`:

```
GITHUB_TOKEN="ghp_YourTokenHere"
```

## Quickstart

```bash
just all        # full pipeline from scratch (60–90 min on first run)
```

Or run stages individually:

```bash
just search-repos              # GitHub discovery → data/filtered_repo_list.txt
just clone-filtered            # clone/update repos from the list
just identify-qiskit           # extract seed KB from Qiskit
just identify-pennylane        # extract seed KB from PennyLane
just identify-classiq          # extract seed KB from Classiq
just identify-qiskit-algorithms
just enrich-kb                 # add internal keywords/comments to seed KB
just preprocess-notebooks      # extract .ipynb → .py
just convert-archived-notebooks
just build-dynamic-kbs         # phase 1: build per-project dynamic KBs
just run_main                  # phase 2: detect patterns in notebooks
just report                    # generate docs/final_pattern_report.md
just evaluate-qrisp-two-phase  # run held-out Qrisp evaluation
```

## Tuning thresholds

Edit `data/analysis_config.json` to enable/disable channels or adjust thresholds, then re-run `just run_main`. No code changes required.

## Project layout

```
qpa/
├── src/
│   ├── analysis/           # run.py (main matcher), generate_report.py
│   ├── core_concepts/      # seed KB extraction pipelines per framework
│   ├── data_acquisition/   # GitHub search, pattern atlas download
│   ├── preprocessing/      # notebook conversion, repo cloning
│   ├── evaluation/         # metrics, per-framework evaluation pipelines
│   └── conf/               # config.py (paths, model name)
├── scripts/
│   ├── build_dynamic_kbs.py       # phase 1 dynamic KB builder
│   ├── build_qrisp_name_kb.py     # manual Qrisp KB (evaluation target)
│   ├── enrich_kb_with_internals.py
│   └── evaluate_qrisp_metrics.py
├── data/
│   ├── analysis_config.json       # runtime channel config
│   ├── dynamic_kb/                # auto-built per-project KBs
│   ├── knowledge_base/            # classified seed KB CSVs
│   └── qrisp_ground_truth.csv     # held-out evaluation labels
├── converted_notebooks/           # .py files extracted from notebooks
├── target_github_projects/        # cloned repositories
├── paper/                         # companion papers (LaTeX)
├── docs/
│   └── final_pattern_report.md    # latest analysis report
├── justfile                       # all pipeline commands
└── pyproject.toml
```

## Key outputs

| File | Description |
|---|---|
| `docs/final_pattern_report.md` | Main analysis report |
| `data/quantum_concept_matches_with_patterns.csv` | Full match dataset |
| `data/dynamic_kb/<project>/` | Per-project dynamic KB entries |
| `data/report/*.csv` | Individual breakdown tables |

## Utility commands

```bash
just compare-runs                        # diff two archived runs
just list-runs                           # list all run archives
just kappa                               # compute inter-rater agreement
just build-paper                         # compile LaTeX paper to PDF
just build-dynamic-kb-project <name>     # rebuild one project's KB
just evaluate-all-frameworks             # precision/recall on all GT frameworks
just clean                               # remove all generated artifacts
```

## Embedding model

`all-mpnet-base-v2` (sentence-transformers). Max 384 tokens per input. Chosen for reproducibility as there are  no API calls,  and reduced non-determinism.

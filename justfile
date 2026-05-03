# justfile

set shell := ["bash", "-c"]
export PATH := env_var('PATH') + ":" + env_var('HOME') + "/.local/bin:" + env_var('HOME') + "/.cargo/bin"

VENV            := ".venv"
REPO_LIST_FILE  := "data/filtered_repo_list.txt"

# Run the complete experiment from scratch: setup → seed KB → preprocessing →
# dynamic KB construction → pattern detection → report → Qrisp evaluation.
# Expected runtime on first run: 60–90 minutes (dominated by cloning + Phase 1).
all:
    @just install
    @just download_pattern_list
    @just identify-qiskit
    @just identify-pennylane
    @just identify-classiq
    @just identify-qiskit-algorithms
    @just preprocess-notebooks
    @just convert-archived-notebooks
    @just build-dynamic-kbs
    @just run_main
    @just report
    @just evaluate-qrisp-two-phase

# It creates the venv, installs ALL dependencies, and clones the repos.
install: ensure-uv discover-and-clone
    @echo "\n>>> Setting up the project environment in '{{VENV}}'..."
    @uv venv --clear --seed {{VENV}}

    @echo " Installing all dependencies from pyproject.toml..."
    @uv sync --python {{VENV}}/bin/python

    @echo ">>> Environment setup complete."
    @echo "To activate it manually, run: source {{VENV}}/bin/activate"

# Runs all core concept identification scripts. This is the main analysis command.
# It now depends on `install` to ensure the environment is ready.
identify-concepts: install
    @echo "\n>>> Running all core concept identification tasks..."
    @just identify-qiskit
    @just identify-pennylane
    @just identify-classiq
    @just identify-qiskit-algorithms
    @echo "\n All core concept identification tasks are complete."
    @echo "Results are saved in the 'data/' directory."

preprocess-notebooks:
    @echo "\n>>> Preprocessing notebooks (converting to .py and archiving)..."
    @{{VENV}}/bin/python -m src.preprocessing.extract_notebooks

# Utility to convert notebooks from the archive folder to a separate output folder.
convert-archived-notebooks:
    @echo "\n>>> Converting archived notebooks..."
    @{{VENV}}/bin/python -m src.preprocessing.convert_notebooks

# Downloads the pattern list from the patternatlas.planqk.de website
download_pattern_list:
    @echo "\n>>> Downloading pattern list from patternatlas website..."
    @{{VENV}}/bin/python -m src.data_acquisition.download_patterns

run_main:
    @echo "\n>>> Running main analysis..."
    @{{VENV}}/bin/python -m src.analysis.run

# Phase 1: scan every non-seed project's source code and extract high-confidence
# name matches as a project-specific dynamic KB in data/dynamic_kb/<project>/.
# Fingerprint-gated — skips projects whose source hasn't changed since last run.
# Run this before evaluate-qrisp (or run_main) to benefit from the extended vocab.
# Compute inter-rater agreement (Cohen's κ, Fleiss' κ, Light's κ) from the
# kappa validation spreadsheet. Covers Qiskit Algorithms, Qiskit ML
# (single-label) and Qrisp GT (multi-label per-pattern binary κ).
# Usage: just kappa [--file data/kappa_validation_final.xlsx]
kappa file="data/kappa_validation_final.xlsx":
    @echo "\n>>> Computing inter-rater agreement from '{{file}}'..."
    @{{VENV}}/bin/python scripts/compute_interrater_agreement.py --file {{file}}

# Enrich the five seed KB concept JSONs with internal_keywords and
# internal_comments extracted from each framework's source code.
# Run once after cloning the seed frameworks; re-run if source changes.
# Output: updated data/*_quantum_concepts.json (with new fields in-place).
enrich-kb:
    @echo "\n>>> Enriching seed KB with internal keywords and comments..."
    @{{VENV}}/bin/python scripts/enrich_kb_with_internals.py

# Build the Qrisp-specific KB from the algorithm directory structure.
# This is the authoritative Qrisp KB used for the evaluation.
# Output: data/dynamic_kb/Qrisp/ (concepts.json + patterns.csv)
build-qrisp-kb:
    @echo "\n>>> Building Qrisp name-based KB from algorithm directories..."
    @{{VENV}}/bin/python scripts/build_qrisp_name_kb.py

build-dynamic-kbs:
    @echo "\n>>> Building dynamic knowledge bases from project source code..."
    @{{VENV}}/bin/python scripts/build_dynamic_kbs.py

# Same but force-rebuild all (ignores fingerprints).
build-dynamic-kbs-force:
    @echo "\n>>> Rebuilding all dynamic KBs (forced)..."
    @{{VENV}}/bin/python scripts/build_dynamic_kbs.py --force

# Rebuild dynamic KB for a single project (quick test).
# Usage: just build-dynamic-kb-project Qrisp
build-dynamic-kb-project project:
    @echo "\n>>> Building dynamic KB for '{{project}}'..."
    @{{VENV}}/bin/python scripts/build_dynamic_kbs.py --project {{project}} --force

# Run analysis + scoped P/R/F1 across every framework with a ground-truth file.
# Precision is scoped to patterns that appear in each framework's GT, so
# domain-specific frameworks (Qiskit Finance, etc.) are not penalised for
# patterns they don't target.
evaluate-all-frameworks:
    @echo "\n>>> Running multi-framework evaluation..."
    @{{VENV}}/bin/python -m src.analysis.run --evaluate-all

# Same as above but reuses existing eval CSVs (skips the analysis step).
evaluate-all-frameworks-skip:
    @echo "\n>>> Multi-framework evaluation (skip-analysis)..."
    @{{VENV}}/bin/python -m src.analysis.run --evaluate-all --skip-analysis

run_llm:
    @echo "\n>>> Running llm analysis..."
    @{{VENV}}/bin/python -m src.analysis.run_llm

run_qrisp_embeddings:
	@echo "\n>>> Running embedding analysis for Qrisp only..."
	{{VENV}}/bin/python -m src.analysis.run --target-dir converted_notebooks/Qrisp --output data/qrisp_embedding_matches.csv

run_qrisp:
    @echo "\n>>> Running llm analysis..."
    @{{VENV}}/bin/python -m src.analysis.run_qrisp

# Compare two archived runs (default: previous vs latest).
# Usage:
#   just compare-runs                                    # previous vs latest
#   just compare-runs RUN_A RUN_B                        # specific ids/prefixes
#   just compare-runs latest 20260426_063500             # any token resolved by compare_runs.py
compare-runs old="previous" new="latest":
    @{{VENV}}/bin/python scripts/compare_runs.py "{{old}}" "{{new}}"

# List all archived runs with summary stats.
list-runs:
    @{{VENV}}/bin/python scripts/compare_runs.py --list

# Build the paper PDF from paper/QuantumWeekOverleaf/quantum_paper.tex.
# Output is written next to the .tex file. Requires pdflatex + bibtex.
# Usage:
#   just build-paper           # build only
#   just build-paper clean     # build then remove .aux/.log/.bbl etc.
build-paper mode="":
    @echo "\n>>> Building quantum_paper.pdf..."
    @if [ "{{mode}}" = "clean" ]; then \
        {{VENV}}/bin/python paper/utils/build_pdf.py --clean; \
    else \
        {{VENV}}/bin/python paper/utils/build_pdf.py; \
    fi

# Run main analysis on a specific target directory
# Usage: just run_main_target <target_dir> [output_file]
run_main_target target_dir output_file="":
    @echo "\n>>> Running main analysis on '{{target_dir}}'..."
    @if [ -z "{{output_file}}" ]; then \
        {{VENV}}/bin/python -m src.analysis.run --target-dir "{{target_dir}}"; \
    else \
        {{VENV}}/bin/python -m src.analysis.run --target-dir "{{target_dir}}" --output "{{output_file}}"; \
    fi

# ── Precision / Recall Evaluation ──────────────────────────────────────────

# Run full evaluation (analysis + metrics + report) for qiskit-finance
evaluate-qiskit-finance:
    @echo "\n>>> Evaluating qiskit-finance..."
    @{{VENV}}/bin/python -m src.evaluation.pipelines.evaluate_qiskit_finance

# ── Qrisp two-phase evaluation (held-out validation set) ───────────────────
#
# Qrisp is the only labelled ground truth outside the seed KB and is used as
# the held-out validation set for the tool. This recipe runs the full
# reproducible pipeline:
#
#   Phase 1 — vocabulary discovery (skipped automatically if source unchanged)
#     Scans Qrisp library source code with the seed KB; for each public
#     function/class whose docstring matches a KB concept summary at
#     score >= MIN_SCORE_DEFAULT (currently 0.75 in build_dynamic_kbs.py),
#     the function name is added to data/dynamic_kb/Qrisp/.
#
#   Phase 2 — pattern detection in notebooks
#     Runs run.py on converted_notebooks/Qrisp/ with the seed KB +
#     Qrisp dynamic KB loaded; produces data/qrisp_eval_output.csv.
#
#   Metrics — precision / recall / F1
#     Joins predictions against data/qrisp_ground_truth.csv (36 GT pairs,
#     11 patterns, 23 notebooks) and prints per-pattern and micro/macro results.
#
# To adjust precision vs recall: edit MIN_SCORE_DEFAULT in
#   scripts/build_dynamic_kbs.py  (phase 1 strictness)
#   data/analysis_config.json      (phase 2 channel thresholds)
# then re-run this recipe.
#
evaluate-qrisp-two-phase:
    @echo "\n>>> Phase 1: building Qrisp dynamic KB from source code..."
    @{{VENV}}/bin/python scripts/build_dynamic_kbs.py --project Qrisp
    @echo "\n>>> Phase 2: detecting patterns in Qrisp notebooks..."
    @{{VENV}}/bin/python -m src.analysis.run \
        --target-dir converted_notebooks/Qrisp \
        --output data/qrisp_eval_output.csv
    @echo "\n>>> Metrics: precision / recall / F1..."
    @{{VENV}}/bin/python scripts/evaluate_qrisp_metrics.py

# Legacy: evaluate-qrisp uses run.py but bypasses dynamic KB (runs via evaluate.py pipeline).
# Use evaluate-qrisp-two-phase for the full validated pipeline.
evaluate-qrisp:
    @echo "\n>>> Evaluating Qrisp (seed KB only, no dynamic KB)..."
    @{{VENV}}/bin/python -m src.evaluation.pipelines.evaluate_qrisp

# Download 5 Qrisp tutorial notebooks, execute them in an isolated qrisp
# environment, and report the quantum API call sequence per notebook.
# Results are written to experiments/results/qrisp_trace/.
# qrisp is installed via uv (cached after the first run).
trace-qrisp:
    @echo "\n>>> Tracing Qrisp notebook execution..."
    @{{VENV}}/bin/python experiments/qrisp_execution_trace.py

# Run full evaluation for Qualtran
evaluate-qualtran:
    @echo "\n>>> Evaluating Qualtran..."
    @{{VENV}}/bin/python -m src.evaluation.pipelines.evaluate_qualtran

# Run all three evaluations in sequence
evaluate-all: evaluate-qiskit-finance evaluate-qrisp evaluate-qualtran

# ── Embedding Model Comparison ──────────────────────────────────────────────

# Compare embedding models on qiskit-finance (fastest, smallest GT)
compare-embeddings:
    @echo "\n>>> Comparing embedding models on qiskit-finance..."
    @{{VENV}}/bin/python -m src.evaluation.embedding_comparison.run_comparison

# Compare embedding models on a specific project
# Usage: just compare-embeddings-project qualtran | qrisp | qiskit-finance
compare-embeddings-project project:
    @echo "\n>>> Comparing embedding models on '{{project}}'..."
    @{{VENV}}/bin/python -m src.evaluation.embedding_comparison.run_comparison --project {{project}}

# Rebuild ChromaDB index and re-run comparison (use after KB changes)
compare-embeddings-rebuild:
    @echo "\n>>> Rebuilding ChromaDB index and comparing embedding models..."
    @{{VENV}}/bin/python -m src.evaluation.embedding_comparison.run_comparison --rebuild

# Build ChromaDB index for all models without running the comparison
index-embeddings:
    @echo "\n>>> Building ChromaDB collections for all embedding models..."
    @{{VENV}}/bin/python -m src.evaluation.embedding_comparison.indexer

# Re-run metrics only (skip re-running analysis) for a project
# Usage: just evaluate-metrics-only qiskit-finance | qrisp | qualtran
evaluate-metrics-only project:
    @echo "\n>>> Re-computing metrics for '{{project}}' (skipping analysis)..."
    @{{VENV}}/bin/python -m src.evaluation.pipelines.evaluate_{{project}} --skip-analysis

# ── Project Categorization ──────────────────────────────────────────────────

analyze-projects:
    @echo "\n>>> Running project categorization analysis..."
    @{{VENV}}/bin/python -m src.analysis.analyze_projects

report:
    @echo "\n>>> Generating final report..."
    @{{VENV}}/bin/python -m src.analysis.generate_report

# Aggregates patterns found in each file into a single sequence
aggregate-sequences:
    @echo "\n>>> Aggregating pattern sequences..."
    @{{VENV}}/bin/python -m src.analysis.aggregate_pattern_sequences


# Analyze extended pattern coverage across frameworks and target projects
extended-patterns:
    @echo "\n>>> Analyzing extended pattern coverage..."
    @{{VENV}}/bin/python -c "from src.reporting import generate_extended_pattern_analysis; generate_extended_pattern_analysis()"

# Generate PDF files from all Markdown files in docs folder
pdf:
    @echo "\n>>> Generating PDFs from Markdown files..."
    @{{VENV}}/bin/python -c "from src.reporting import generate_pdfs; generate_pdfs()"

# Generate experimental data report with complete datasets
experimental-data:
    @echo "\n>>> Generating experimental data report..."
    @{{VENV}}/bin/python -c "from src.reporting import generate_experimental_data_report; generate_experimental_data_report()"

# Generate base concept report from framework extractions
base-concept-report:
    @echo "\n>>> Generating base concept report..."
    @{{VENV}}/bin/python -c "from src.reporting import generate_base_concept_report; generate_base_concept_report()"

# Generate pattern report from PlanQK Pattern Atlas
pattern-report:
    @echo "\n>>> Generating pattern report..."
    @{{VENV}}/bin/python -c "from src.reporting import generate_pattern_report; generate_pattern_report()"

# Generate all reports at once
all-reports:
    @echo "\n>>> Generating all reports..."
    @{{VENV}}/bin/python -c "from src.reporting import generate_all_reports; generate_all_reports()"

# Consolidate knowledge base from framework data
consolidate-knowledge-base:
    @echo "\n>>> Consolidating knowledge base..."
    @{{VENV}}/bin/python -m src.preprocessing.knowledge_base_consolidator

# Runs the GitHub search script to find and filter top quantum projects.
search-repos:
    @echo ">>> Running GitHub search to find and filter top quantum projects..."
    @if [ ! -d "{{VENV}}" ]; then just _bootstrap-tools; fi
    @{{VENV}}/bin/python -m src.data_acquisition.discover_projects

# Clones/updates repositories listed in the dynamically generated file.
clone-filtered:
    @echo "\n>>> Cloning/updating repositories from '{{REPO_LIST_FILE}}'..."
    @if [ ! -d "{{VENV}}" ]; then just _bootstrap-tools; fi
    @{{VENV}}/bin/python -m src.preprocessing.clone_repos {{REPO_LIST_FILE}}

# The data acquisition task.
discover-and-clone: search-repos clone-filtered
    @echo "\n>>> All source repositories are ready."


# Identifies and extracts core concepts from the Qiskit source code.
identify-qiskit:
    @echo "\n--- Identifying core concepts in Qiskit ---"
    @{{VENV}}/bin/python -m src.core_concepts.pipelines.extract_qiskit

# Identifies and extracts core concepts from the PennyLane source code.
identify-pennylane:
    @echo "\n--- Identifying core concepts in PennyLane ---"
    @{{VENV}}/bin/python -m src.core_concepts.pipelines.extract_pennylane

# Identifies and extracts core concepts from the Classiq source code.
identify-classiq:
    @echo "\n--- Identifying core concepts in Classiq ---"
    @{{VENV}}/bin/python -m src.core_concepts.pipelines.extract_classiq

# Identifies and extracts core concepts from the qiskit-algorithms source code.
identify-qiskit-algorithms:
    @echo "\n--- Identifying core concepts in qiskit-algorithms ---"
    @{{VENV}}/bin/python -m src.core_concepts.pipelines.extract_qiskit_algorithms

# Extracts all public methods/functions from qiskit-algorithms for manual pattern review.
identify-qiskit-algorithms-methods:
    @echo "\n--- Extracting qiskit-algorithms methods for manual review ---"
    @{{VENV}}/bin/python -m src.core_concepts.pipelines.extract_qiskit_algorithms_methods


# A special recipe to create a  venv just for the data acquisition scripts.
_bootstrap-tools:
    @echo ">>> Bootstrapping minimal tools environment..."
    @uv venv --clear --seed {{VENV}}
    @uv pip install --python {{VENV}}/bin/python PyGithub python-dotenv python-dateutil
    @echo ">>> Bootstrap complete."

# Cleans up ALL generated files and environments.
clean:
    @echo ">>> Cleaning up ALL generated files and environments..."
    @rm -rf {{VENV}} target_github_projects data
    @find . -type d -name "__pycache__" -exec rm -rf {} +
    @find . -name "*.ipynb.py" -type f -delete
    @echo ">>> Cleanup complete."

upgrade:
  uv lock --upgrade

# == Workflow Orchestration ==================================================

# Run the complete workflow using Prefect orchestration (ephemeral mode, no server required)
workflow:
    @echo ">>> Starting QPA: Quantum Patterns Analyser Workflow..."
    @PREFECT_PROFILE=ephemeral {{VENV}}/bin/python -c "from src.workflows.qpa_flow import qpa_flow; qpa_flow()"

# Run workflow with Prefect UI (starts local server)
workflow-ui:
    @echo ">>> Starting Prefect UI server..."
    @echo ">>> Open http://localhost:4200 in your browser to monitor the workflow"
    @{{VENV}}/bin/prefect server start --host 0.0.0.0 --port 4200

# Reset the local Prefect database (fixes migration errors after Prefect upgrades)
reset-prefect:
    @echo ">>> Resetting local Prefect database..."
    @rm -f ~/.prefect/prefect.db
    @echo ">>> Prefect database deleted. A fresh one will be created on next server start."

# Run workflow and deploy to Prefect Cloud (requires account)
workflow-deploy:
    @echo ">>> Deploying workflow to Prefect Cloud..."
    @{{VENV}}/bin/prefect deploy src/workflows/qpa_flow.py:qpa_flow --name qpa-analysis

# Run individual workflow steps for debugging
workflow-step step:
    @echo ">>> Running workflow step: {{step}}"
    @{{VENV}}/bin/python -c "from src.workflows.qpa_flow import {{step}}; {{step}}()"

# == Testing =================================================================

# Run all tests
test:
    @echo ">>> Running all tests..."
    @{{VENV}}/bin/python -m pytest tests/ -v

# Run unit tests only
test-unit:
    @echo ">>> Running unit tests..."
    @{{VENV}}/bin/python -m pytest tests/ -m unit -v

# Run integration tests only
test-integration:
    @echo ">>> Running integration tests..."
    @{{VENV}}/bin/python -m pytest tests/ -m integration -v

# Run core concepts tests only
test-core-concepts:
    @echo ">>> Running core concepts tests..."
    @{{VENV}}/bin/python -m pytest tests/test_identify_classiq_core_concepts.py -v

# Run tests with coverage
test-coverage:
    @echo ">>> Running tests with coverage..."
    @{{VENV}}/bin/python -m pytest tests/ --cov=src --cov-report=html --cov-report=term -v

# Run tests with coverage and generate detailed report
test-coverage-report:
    @echo ">>> Running tests with detailed coverage report..."
    @{{VENV}}/bin/python -m pytest tests/ --cov=src --cov-report=html --cov-report=xml --cov-report=term --cov-report=json -v
    @echo ">>> Coverage reports generated:"
    @echo "  - HTML: htmlcov/index.html"
    @echo "  - XML: coverage.xml"
    @echo "  - JSON: coverage.json"

# Run coverage analysis on specific module
test-coverage-module module:
    @echo ">>> Running coverage analysis on {{module}}..."
    @{{VENV}}/bin/python -m pytest tests/ --cov={{module}} --cov-report=html --cov-report=term -v

# Generate coverage report without running tests
coverage-report:
    @echo ">>> Generating coverage report from existing data..."
    @{{VENV}}/bin/coverage html
    @{{VENV}}/bin/coverage report
    @echo ">>> HTML report available at: htmlcov/index.html"

# Show coverage summary
coverage-summary:
    @echo ">>> Coverage summary..."
    @{{VENV}}/bin/coverage report --show-missing

# == Code Formatting =========================================================

# Format all Python files with Black
format:
    @echo ">>> Formatting all Python files..."
    uvx ruff format
    @{{VENV}}/bin/black .

# Format specific file or directory
format-file file:
    @echo ">>> Formatting {{file}} with Black..."
    @{{VENV}}/bin/black {{file}}

# Check formatting without making changes
format-check:
    @echo ">>> Checking code formatting with Black..."
    @{{VENV}}/bin/black --check .

# Format and show diff
format-diff:
    @echo ">>> Showing formatting diff with Black..."
    @{{VENV}}/bin/black --diff .

# Lint all Python files with Ruff
lint:
    @echo ">>> Linting all Python files with Ruff..."
    @{{VENV}}/bin/ruff check .

# Lint specific file or directory
lint-file file:
    @echo ">>> Linting {{file}} with Ruff..."
    @{{VENV}}/bin/ruff check {{file}}

# Lint and fix automatically
lint-fix:
    @echo ">>> Linting and fixing all Python files with Ruff..."
    @{{VENV}}/bin/ruff check --fix .

# Lint and fix specific file
lint-fix-file file:
    @echo ">>> Linting and fixing {{file}} with Ruff..."
    @{{VENV}}/bin/ruff check --fix {{file}}

# Run both formatting and linting
format-lint:
    @echo ">>> Running Black formatting and Ruff linting..."
    @just format
    @just lint

# Check formatting and linting without making changes
check-all:
    @echo ">>> Checking formatting and linting..."
    @just format-check
    @just lint

# Format, lint, and run tests
format-lint-test:
    @echo ">>> Running full code quality pipeline..."
    @just format
    @just lint-fix
    @just test

# Run specific test file
test-file file:
    @echo ">>> Running tests in {{file}}..."
    @{{VENV}}/bin/python -m pytest {{file}} -v

# Run tests in parallel
test-parallel:
    @echo ">>> Running tests in parallel..."
    @{{VENV}}/bin/python -m pytest tests/ -n auto -v

# == One-Time Setup ============================================================

default:
  @just --choose

setup:
    @just _setup-{{ os() }}

_setup-macos:
    @echo "Installing uv for macOS..."
    @curl -LsSf https://astral.sh/uv/install.sh | sh

_setup-linux:
    @echo "Installing uv for Linux..."
    @curl -LsSf https://astral.sh/uv/install.sh | sh

_setup-windows:
    @echo "Installing uv for Windows..."
    @powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

ensure-uv:
    @if ! command -v uv >/dev/null 2>&1; then \
        echo "uv not found. Installing..."; \
        curl -LsSf https://astral.sh/uv/install.sh | sh; \
    else \
        echo "uv is already installed."; \
    fi
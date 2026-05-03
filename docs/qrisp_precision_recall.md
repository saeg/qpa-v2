# Precision and Recall Evaluation — Qrisp

## Setup

- **Target project**: `converted_notebooks/Qrisp`
- **Ground truth**: `data/qrisp_ground_truth.csv` (36 files, 11 patterns)
- **Predictor**: `run_analysis.py --target-dir`
- **Resolution**: highest-scoring prediction per file; ties broken alphabetically by pattern.

---

## Overall Results

| Metric | Value |
|---|---|
| GT files | 36 |
| Files with at least one prediction | 28 (78 %) |
| Files with no prediction (missed) | 8 (22 %) |
| Correct predictions (TP) | 20 |
| Wrong predictions (FP) | 8 |
| **Micro Precision** | **0.741** |
| **Micro Recall** | **0.556** |
| **Micro F1** | **0.635** |
| Macro Precision | 0.583 |
| Macro Recall | 0.496 |
| Macro F1 | 0.524 |

---

## Per-Pattern Results

| Pattern | GT | Predicted | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|---|
| Quantum Approximate Optimization Algorithm (QAOA) | 8 | 5 | 5 | 0 | 3 | 1.000 | 0.625 | 0.769 |
| Quantum Phase Estimation (QPE) | 6 | 4 | 4 | 0 | 2 | 1.000 | 0.667 | 0.800 |
| Basis Change | 4 | 4 | 4 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Grover | 4 | 0 | 0 | 0 | 4 | — | 0.000 | — |
| Initialization | 3 | 3 | 2 | 1 | 1 | 0.667 | 0.667 | 0.667 |
| Linear Combination of Unitaries | 3 | 4 | 3 | 1 | 0 | 0.750 | 1.000 | 0.857 |
| Amplitude Amplification | 2 | 1 | 0 | 1 | 2 | 0.000 | 0.000 | — |
| Hamiltonian Simulation | 2 | 1 | 0 | 1 | 2 | 0.000 | 0.000 | — |
| Quantum Arithmetic | 2 | 1 | 1 | 0 | 1 | 1.000 | 0.500 | 0.667 |
| Quantum Amplitude Estimation | 1 | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Variational Quantum Algorithm (VQA) | 1 | 3 | 0 | 3 | 1 | 0.000 | 0.000 | — |

---

## Correct Predictions

| File | Pattern |
|---|---|
| `documentation/source/general/tutorial/BE_tutorial/BE_vol1.py` | Linear Combination of Unitaries |
| `documentation/source/general/tutorial/BE_tutorial/BE_vol2.py` | Linear Combination of Unitaries |
| `documentation/source/general/tutorial/BigInteger.py` | Basis Change |
| `documentation/source/general/tutorial/CD.py` | Quantum Approximate Optimization Algorithm (QAOA) |
| `documentation/source/general/tutorial/FT_compilation.py` | Basis Change |
| `documentation/source/general/tutorial/GQSP_filtering.py` | Linear Combination of Unitaries |
| `documentation/source/general/tutorial/HHL.py` | Initialization |
| `documentation/source/general/tutorial/HHL.py` | Quantum Phase Estimation (QPE) |
| `documentation/source/general/tutorial/Jasp.py` | Quantum Arithmetic |
| `documentation/source/general/tutorial/QAOAtutorial/MaxCut.py` | Quantum Approximate Optimization Algorithm (QAOA) |
| `documentation/source/general/tutorial/QAOAtutorial/MkCS.py` | Quantum Approximate Optimization Algorithm (QAOA) |
| `documentation/source/general/tutorial/QAOAtutorial/PortfolioRebalancing.py` | Initialization |
| `documentation/source/general/tutorial/QAOAtutorial/QUBO.py` | Quantum Approximate Optimization Algorithm (QAOA) |
| `documentation/source/general/tutorial/QIROtutorial.py` | Quantum Approximate Optimization Algorithm (QAOA) |
| `documentation/source/general/tutorial/QMCItutorial.py` | Quantum Amplitude Estimation |
| `documentation/source/general/tutorial/Shor.py` | Basis Change |
| `documentation/source/general/tutorial/Sudoku.py` | Quantum Phase Estimation (QPE) |
| `documentation/source/general/tutorial/TSP.py` | Quantum Phase Estimation (QPE) |
| `documentation/source/general/tutorial/tutorial.py` | Basis Change |
| `documentation/source/general/tutorial/tutorial.py` | Quantum Phase Estimation (QPE) |

---

## Wrong Predictions

| File | GT Pattern | Predicted Pattern |
|---|---|---|
| `documentation/source/general/tutorial/BigInteger.py` | Quantum Phase Estimation (QPE) | Basis Change |
| `documentation/source/general/tutorial/QAOAtutorial/PortfolioRebalancing.py` | Quantum Approximate Optimization Algorithm (QAOA) | Initialization |
| `documentation/source/general/tutorial/Shor.py` | Quantum Phase Estimation (QPE) | Basis Change |
| `documentation/source/general/tutorial/Sudoku.py` | Amplitude Amplification | Circuit Construction Utility |
| `documentation/source/general/tutorial/Sudoku.py` | Grover | Circuit Construction Utility |
| `documentation/source/general/tutorial/TSP.py` | Grover | Quantum Phase Estimation (QPE) |
| `documentation/source/general/tutorial/tutorial.py` | Amplitude Amplification | Variational Quantum Algorithm (VQA) |
| `documentation/source/general/tutorial/tutorial.py` | Grover | Variational Quantum Algorithm (VQA) |

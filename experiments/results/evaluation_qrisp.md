# QPA Evaluation — Qrisp (Primary GT)

> Qrisp is used as the primary evaluation framework: it is completely outside the KB,
> ensuring zero leakage between training data and evaluation target.

## Overall

| GT | Pred | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 36 | 38 | 34 | 4 | 2 | 0.895 | 0.944 | 0.919 |

## FP Breakdown by Matching Channel

| Channel | FP count |
| --- | --- |
| name | 2 |
| keyword_name | 2 |
| keyword_comment | 1 |

## Per-Pattern Results

| Pattern | GT | Pred | TP | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| Basis Change | 4 | 4 | 4 | 1.000 | 1.000 | 1.000 |
| Grover | 4 | 4 | 4 | 1.000 | 1.000 | 1.000 |
| Initialization | 3 | 3 | 3 | 1.000 | 1.000 | 1.000 |
| Linear Combination of Unitaries | 3 | 3 | 3 | 1.000 | 1.000 | 1.000 |
| Quantum Amplitude Estimation | 1 | 1 | 1 | 1.000 | 1.000 | 1.000 |
| Variational Quantum Algorithm (VQA) | 1 | 1 | 1 | 1.000 | 1.000 | 1.000 |
| Quantum Approximate Optimization Algorithm (QAOA) | 8 | 7 | 7 | 1.000 | 0.875 | 0.933 |
| Quantum Phase Estimation (QPE) | 6 | 7 | 6 | 0.857 | 1.000 | 0.923 |
| Amplitude Amplification | 2 | 3 | 2 | 0.667 | 1.000 | 0.800 |
| Hamiltonian Simulation | 2 | 4 | 2 | 0.500 | 1.000 | 0.667 |
| Quantum Arithmetic | 2 | 1 | 1 | 1.000 | 0.500 | 0.667 |

## True Positives

- `BE_vol1.py` → Linear Combination of Unitaries
- `BE_vol2.py` → Linear Combination of Unitaries
- `BigInteger.py` → Basis Change
- `BigInteger.py` → Quantum Phase Estimation (QPE)
- `FT_compilation.py` → Basis Change
- `GQSP_filtering.py` → Linear Combination of Unitaries
- `H2.py` → Hamiltonian Simulation
- `H2.py` → Initialization
- `HHL.py` → Initialization
- `HHL.py` → Quantum Phase Estimation (QPE)
- `Jasp.py` → Quantum Arithmetic
- `JaspQAOAtutorial.py` → Quantum Approximate Optimization Algorithm (QAOA)
- `JaspQAOAtutorial.py` → Variational Quantum Algorithm (VQA)
- `ConstrainedMixers.py` → Grover
- `ConstrainedMixers.py` → Hamiltonian Simulation
- `ConstrainedMixers.py` → Quantum Approximate Optimization Algorithm (QAOA)
- `MaxCut.py` → Quantum Approximate Optimization Algorithm (QAOA)
- `MkCS.py` → Quantum Approximate Optimization Algorithm (QAOA)
- `PortfolioRebalancing.py` → Initialization
- `PortfolioRebalancing.py` → Quantum Approximate Optimization Algorithm (QAOA)
- `QUBO.py` → Quantum Approximate Optimization Algorithm (QAOA)
- `QIROtutorial.py` → Quantum Approximate Optimization Algorithm (QAOA)
- `QMCItutorial.py` → Quantum Amplitude Estimation
- `Shor.py` → Basis Change
- `Shor.py` → Quantum Phase Estimation (QPE)
- `Sudoku.py` → Amplitude Amplification
- `Sudoku.py` → Grover
- `Sudoku.py` → Quantum Phase Estimation (QPE)
- `TSP.py` → Grover
- `TSP.py` → Quantum Phase Estimation (QPE)
- `tutorial.py` → Amplitude Amplification
- `tutorial.py` → Basis Change
- `tutorial.py` → Grover
- `tutorial.py` → Quantum Phase Estimation (QPE)

## False Positives (predicted, not in GT)

- `BE_vol2.py` → Hamiltonian Simulation  _keyword_name, name_
- `BE_vol2.py` → Quantum Phase Estimation (QPE)  _keyword_comment_
- `GQSP_filtering.py` → Amplitude Amplification  _name_
- `HHL.py` → Hamiltonian Simulation  _keyword_name_

## False Negatives (GT has, tool missed)

- `BigInteger.py` → Quantum Arithmetic
- `CD.py` → Quantum Approximate Optimization Algorithm (QAOA)

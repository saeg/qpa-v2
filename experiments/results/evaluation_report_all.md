# QPA Evaluation Report — Multi-Framework

## Core Quantum Patterns (cross-framework prevalence)

Patterns detected in the most independent frameworks by the tool:

| Pattern | # Frameworks | KB entries (excl. Qualtran) |
| --- | --- | --- |
| Hamiltonian Simulation | 28 | 13 |
| Variational Quantum Algorithm (VQA) | 27 | 49 |
| Variational Quantum Eigensolver (VQE) | 23 | 22 |
| Quantum Approximate Optimization Algorithm (QAOA) | 19 | 21 |
| Circuit Construction Utility | 18 | 36 |
| Initialization | 17 | 24 |
| Creating Entanglement | 16 | 13 |
| Quantum Logical Operators | 14 | 7 |
| Basis Change | 13 | 20 |
| Quantum Neural Network (QNN) | 12 | 13 |
| Grover | 12 | 10 |
| SWAP Test | 11 | 11 |
| Linear Combination of Unitaries | 10 | 14 |
| Domain Specific Application | 9 | 21 |
| Data Encoding | 9 | 14 |
| Quantum Amplitude Estimation | 9 | 13 |
| Amplitude Amplification | 8 | 11 |
| Dynamic Circuit | 6 | 2 |
| Quantum Phase Estimation (QPE) | 6 | 29 |
| Function Table | 6 | 1 |
| Quantum Arithmetic | 6 | 45 |
| Oracle | 5 | 20 |

## Summary: Three Evaluations

| Evaluation | GT size | Predictions | TP | FP | FN | Precision | Recall | F1 | Leakage? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. qiskit-algorithms | 22 | 33 | 20 | 13 | 2 | 0.606 | 0.909 | 0.727 | Yes — KB includes qiskit-algorithms source |
| B. Qualtran (restricted) | 29 | 48 | 15 | 33 | 14 | 0.312 | 0.517 | 0.390 | No — restricted to KB-coverable patterns |
| C. Qrisp | 23 | 52 | 19 | 33 | 4 | 0.365 | 0.826 | 0.507 | No — framework not in KB |
| D. Combined (qibo+squlearn+ReCirq) | 30 | 101 | 20 | 81 | 10 | 0.198 | 0.667 | 0.305 | No — frameworks not in KB |
| E. QPanda-2 | 21 | 48 | 13 | 35 | 8 | 0.271 | 0.619 | 0.377 | Partial — QPanda KB built from own API |

## FP Breakdown by Matching Channel

| Evaluation | Total FP | name | keyword_name | keyword_comment | caller | title | summary | pattern_desc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. qiskit-algorithms | 13 | 7 | 8 | 3 | 0 | 2 | 0 | 0 |
| B. Qualtran restricted | 33 | 12 | 8 | 7 | 1 | 7 | 1 | 0 |
| C. Qrisp | 33 | 8 | 15 | 18 | 2 | 1 | 0 | 0 |
| D. Combined | 81 | 14 | 46 | 20 | 8 | 12 | 0 | 0 |
| E. QPanda-2 | 35 | 8 | 29 | 1 | 21 | 0 | 0 | 0 |

### Qualtran: restricted vs. full evaluation

- Restricted (29 GT entries, patterns KB covers): P=0.312  R=0.517  F1=0.390
- Full (121 GT entries, all patterns): P=0.310  R=0.289  F1=0.299
- Restricted patterns: Amplitude Amplification, Basis Change, Circuit Construction Utility, Data Encoding, Initialization, Quantum Phase Estimation (QPE)

### Combined GT: Per-Framework Breakdown

| Framework | GT | Pred | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qibo | 10 | 34 | 7 | 27 | 3 | 0.206 | 0.700 | 0.318 |
| squlearn | 11 | 37 | 9 | 28 | 2 | 0.243 | 0.818 | 0.375 |
| ReCirq | 9 | 30 | 4 | 26 | 5 | 0.133 | 0.444 | 0.205 |

## Per-Pattern: qiskit-algorithms

| Pattern | GT | Pred | TP | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| Amplitude Amplification | 2 | 2 | 2 | 1.000 | 1.000 | 1.000 |
| Variational Quantum Algorithm (VQA) | 9 | 9 | 9 | 1.000 | 1.000 | 1.000 |
| Grover | 3 | 2 | 2 | 1.000 | 0.667 | 0.800 |
| Hamiltonian Simulation | 2 | 4 | 2 | 0.500 | 1.000 | 0.667 |
| Oracle | 1 | 2 | 1 | 0.500 | 1.000 | 0.667 |
| Variational Quantum Eigensolver (VQE) | 3 | 6 | 3 | 0.500 | 1.000 | 0.667 |
| Quantum Approximate Optimization Algorithm (QAOA) | 2 | 2 | 1 | 0.500 | 0.500 | 0.500 |

## Per-Pattern: Qualtran (restricted)

| Pattern | GT | Pred | TP | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| Quantum Phase Estimation (QPE) | 6 | 7 | 5 | 0.714 | 0.833 | 0.769 |
| Amplitude Amplification | 1 | 2 | 1 | 0.500 | 1.000 | 0.667 |
| Data Encoding | 4 | 2 | 2 | 1.000 | 0.500 | 0.667 |
| Basis Change | 5 | 6 | 3 | 0.500 | 0.600 | 0.545 |
| Initialization | 5 | 9 | 3 | 0.333 | 0.600 | 0.429 |
| Circuit Construction Utility | 8 | 11 | 1 | 0.091 | 0.125 | 0.105 |

## Per-Pattern: Qrisp

| Pattern | GT | Pred | TP | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| Quantum Amplitude Estimation | 1 | 1 | 1 | 1.000 | 1.000 | 1.000 |
| Quantum Approximate Optimization Algorithm (QAOA) | 8 | 7 | 7 | 1.000 | 0.875 | 0.933 |
| Basis Change | 3 | 4 | 3 | 0.750 | 1.000 | 0.857 |
| Linear Combination of Unitaries | 2 | 3 | 2 | 0.667 | 1.000 | 0.800 |
| Quantum Phase Estimation (QPE) | 5 | 8 | 5 | 0.625 | 1.000 | 0.769 |
| Quantum Arithmetic | 2 | 1 | 1 | 1.000 | 0.500 | 0.667 |
| Data Encoding | 1 | 0 | 0 | 0.000 | 0.000 | 0.000 |
| Hamiltonian Simulation | 1 | 5 | 0 | 0.000 | 0.000 | 0.000 |

## Qrisp: True Positives

- ✓ `BE_vol1.py` → Linear Combination of Unitaries
- ✓ `FT_compilation.py` → Basis Change
- ✓ `GQSP_filtering.py` → Linear Combination of Unitaries
- ✓ `HHL.py` → Quantum Phase Estimation (QPE)
- ✓ `Jasp.py` → Quantum Arithmetic
- ✓ `JaspQAOAtutorial.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `ConstrainedMixers.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `MaxCut.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `MkCS.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `PortfolioRebalancing.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `QUBO.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `QIROtutorial.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `QMCItutorial.py` → Quantum Amplitude Estimation
- ✓ `Shor.py` → Basis Change
- ✓ `Shor.py` → Quantum Phase Estimation (QPE)
- ✓ `Sudoku.py` → Quantum Phase Estimation (QPE)
- ✓ `TSP.py` → Quantum Phase Estimation (QPE)
- ✓ `tutorial.py` → Basis Change
- ✓ `tutorial.py` → Quantum Phase Estimation (QPE)

## Qrisp: False Positives (predicted but wrong)

- ✗ `BE_vol1.py` → Hamiltonian Simulation
- ✗ `BE_vol2.py` → Hamiltonian Simulation
- ✗ `BE_vol2.py` → Initialization
- ✗ `BE_vol2.py` → Linear Combination of Unitaries
- ✗ `BE_vol2.py` → Quantum Phase Estimation (QPE)
- ✗ `BigInteger.py` → Basis Change
- ✗ `BigInteger.py` → Quantum Phase Estimation (QPE)
- ✗ `CD.py` → Hamiltonian Simulation
- ✗ `FT_compilation.py` → Dynamic Circuit
- ✗ `FT_compilation.py` → Function Table
- ✗ `GQSP_filtering.py` → Grover
- ✗ `GQSP_filtering.py` → Hamiltonian Simulation
- ✗ `GQSP_filtering.py` → Initialization
- ✗ `GQSP_filtering.py` → Quantum Phase Estimation (QPE)
- ✗ `H2.py` → Initialization
- ✗ `H2.py` → Variational Quantum Eigensolver (VQE)
- ✗ `HHL.py` → Amplitude Amplification
- ✗ `HHL.py` → Initialization
- ✗ `JaspQAOAtutorial.py` → Variational Quantum Algorithm (VQA)
- ✗ `ConstrainedMixers.py` → Grover
- ✗ `ConstrainedMixers.py` → Hamiltonian Simulation
- ✗ `ConstrainedMixers.py` → Initialization
- ✗ `MaxCut.py` → Creating Entanglement
- ✗ `PortfolioRebalancing.py` → Initialization
- ✗ `QMCItutorial.py` → Amplitude Amplification
- ✗ `QMCItutorial.py` → Domain Specific Application
- ✗ `Sudoku.py` → Amplitude Amplification
- ✗ `Sudoku.py` → Grover
- ✗ `Sudoku.py` → Quantum Logical Operators
- ✗ `TSP.py` → Function Table
- ✗ `TSP.py` → Grover
- ✗ `tutorial.py` → Amplitude Amplification
- ✗ `tutorial.py` → Grover

## Qrisp: False Negatives (GT has, tool missed)

- ✗ `BE_vol2.py` → Data Encoding
- ✗ `BigInteger.py` → Quantum Arithmetic
- ✗ `CD.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `H2.py` → Hamiltonian Simulation

## Per-Pattern: Combined GT (qibo + squlearn + ReCirq)

| Pattern | GT | Pred | TP | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| Grover | 1 | 1 | 1 | 1.000 | 1.000 | 1.000 |
| Basis Change | 1 | 2 | 1 | 0.500 | 1.000 | 0.667 |
| SWAP Test | 3 | 8 | 3 | 0.375 | 1.000 | 0.545 |
| Quantum Approximate Optimization Algorithm (QAOA) | 4 | 11 | 4 | 0.364 | 1.000 | 0.533 |
| Variational Quantum Eigensolver (VQE) | 2 | 2 | 1 | 0.500 | 0.500 | 0.500 |
| Data Encoding | 4 | 1 | 1 | 1.000 | 0.250 | 0.400 |
| Quantum Amplitude Estimation | 1 | 4 | 1 | 0.250 | 1.000 | 0.400 |
| Quantum Neural Network (QNN) | 6 | 20 | 5 | 0.250 | 0.833 | 0.385 |
| Variational Quantum Algorithm (VQA) | 5 | 22 | 2 | 0.091 | 0.400 | 0.148 |
| Hamiltonian Simulation | 2 | 19 | 1 | 0.053 | 0.500 | 0.095 |
| Amplitude Amplification | 1 | 0 | 0 | 0.000 | 0.000 | 0.000 |

## Combined GT: True Positives

- ✓ `quickstart.py` → Variational Quantum Algorithm (VQA)
- ✓ `binary_paintshop.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `qaoa_ising.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `qaoa_maxcut.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `evolution.py` → Hamiltonian Simulation
- ✓ `grover.py` → Grover
- ✓ `iqae.py` → Quantum Amplitude Estimation
- ✓ `qft.py` → Basis Change
- ✓ `variational.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `variational.py` → Variational Quantum Algorithm (VQA)
- ✓ `variational.py` → Variational Quantum Eigensolver (VQE)
- ✓ `various_encoding_circuit.py` → Data Encoding
- ✓ `example_fidelity_kernel.py` → SWAP Test
- ✓ `example_projected_kernel.py` → SWAP Test
- ✓ `classification_example.py` → Quantum Neural Network (QNN)
- ✓ `example_qcnn_encoding_circuit.py` → Quantum Neural Network (QNN)
- ✓ `multiclass_classification.py` → Quantum Neural Network (QNN)
- ✓ `kernel_digit_classification.py` → Quantum Neural Network (QNN)
- ✓ `kernel_digit_classification.py` → SWAP Test
- ✓ `qnn_backend_mitigation.py` → Quantum Neural Network (QNN)

## Combined GT: False Positives (predicted but wrong)

- ✗ `experiment_example.py` → Hamiltonian Simulation
- ✗ `ftbbl.py` → Variational Quantum Algorithm (VQA)
- ✗ `molecular_data.py` → Hamiltonian Simulation
- ✗ `molecular_data.py` → Variational Quantum Eigensolver (VQE)
- ✗ `lattice_gauge.py` → Hamiltonian Simulation
- ✗ `lattice_gauge.py` → Variational Quantum Algorithm (VQA)
- ✗ `binary_paintshop.py` → Circuit Construction Utility
- ✗ `example_problems.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `hardware_grid_circuits.py` → Circuit Construction Utility
- ✗ `hardware_grid_circuits.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `landscape_analysis.py` → Hamiltonian Simulation
- ✗ `landscape_analysis.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `optimization_analysis.py` → Hamiltonian Simulation
- ✗ `optimization_analysis.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `precomputed_analysis.py` → Hamiltonian Simulation
- ✗ `qaoa_ising.py` → Circuit Construction Utility
- ✗ `qaoa_maxcut.py` → Quantum Amplitude Estimation
- ✗ `routing_with_tket.py` → Circuit Construction Utility
- ✗ `routing_with_tket.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `experimental_wavefunctions.py` → Hamiltonian Simulation
- ✗ `experimental_wavefunctions.py` → Variational Quantum Algorithm (VQA)
- ✗ `full_workflow.py` → Hamiltonian Simulation
- ✗ `full_workflow.py` → Variational Quantum Algorithm (VQA)
- ✗ `high_level.py` → Hamiltonian Simulation
- ✗ `analysis-walkthrough.py` → Variational Quantum Algorithm (VQA)
- ✗ `plots.py` → Variational Quantum Algorithm (VQA)
- ✗ `adiabatic-qml.py` → Variational Quantum Algorithm (VQA)
- ✗ `qPDF.py` → Variational Quantum Algorithm (VQA)
- ✗ `qcnn_demo.py` → Quantum Neural Network (QNN)
- ✗ `qcnn_demo.py` → Variational Quantum Algorithm (VQA)
- ✗ `qfiae_demo.py` → Hamiltonian Simulation
- ✗ `qfiae_demo.py` → Quantum Amplitude Estimation
- ✗ `qfiae_demo.py` → Variational Quantum Algorithm (VQA)
- ✗ `adiabatic-qml.py` → Variational Quantum Algorithm (VQA)
- ✗ `qibo-draw-circuit-matplotlib.py` → Basis Change
- ✗ `qibo-draw-circuit-matplotlib.py` → Quantum Logical Operators
- ✗ `qibo-draw-circuit-matplotlib.py` → Variational Quantum Algorithm (VQA)
- ✗ `qPDF.py` → Variational Quantum Algorithm (VQA)
- ✗ `qcnn_demo.py` → Quantum Neural Network (QNN)
- ✗ `qcnn_demo.py` → Variational Quantum Algorithm (VQA)
- ✗ `qfiae_demo.py` → Hamiltonian Simulation
- ✗ `qfiae_demo.py` → Quantum Amplitude Estimation
- ✗ `qfiae_demo.py` → Variational Quantum Algorithm (VQA)
- ✗ `encodings.py` → Circuit Construction Utility
- ✗ `encodings.py` → Initialization
- ✗ `grover.py` → Hamiltonian Simulation
- ✗ `grover.py` → Initialization
- ✗ `iqae.py` → Hamiltonian Simulation
- ✗ `qcnn.py` → Hamiltonian Simulation
- ✗ `qcnn.py` → Initialization
- ✗ `qcnn.py` → Variational Quantum Algorithm (VQA)
- ✗ `qft.py` → Initialization
- ✗ `variational.py` → Hamiltonian Simulation
- ✗ `layered_encoding_circuit.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `various_encoding_circuit.py` → Variational Quantum Algorithm (VQA)
- ✗ `mlflow.py` → Hamiltonian Simulation
- ✗ `mlflow.py` → Quantum Neural Network (QNN)
- ✗ `example_projected_kernel.py` → Quantum Neural Network (QNN)
- ✗ `example_projected_kernel.py` → Variational Quantum Algorithm (VQA)
- ✗ `example_qkode.py` → Quantum Neural Network (QNN)
- ✗ `example_qkode.py` → SWAP Test
- ✗ `qgpr_optimization_workflow.py` → Variational Quantum Algorithm (VQA)
- ✗ `qgpr_workflow.py` → SWAP Test
- ✗ `example_adam.py` → Quantum Neural Network (QNN)
- ✗ `example_minibatch.py` → Quantum Neural Network (QNN)
- ✗ `ode_example.py` → Quantum Neural Network (QNN)
- ✗ `regression_example.py` → Hamiltonian Simulation
- ✗ `regression_example.py` → Quantum Neural Network (QNN)
- ✗ `regression_with_variance.py` → Hamiltonian Simulation
- ✗ `regression_with_variance.py` → Quantum Neural Network (QNN)
- ✗ `qrc_classification.py` → Quantum Neural Network (QNN)
- ✗ `qrc_regression.py` → Quantum Neural Network (QNN)
- ✗ `kernel_grid_search.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `kernel_grid_search.py` → Quantum Neural Network (QNN)
- ✗ `kernel_grid_search.py` → SWAP Test
- ✗ `kernel_grid_search.py` → Variational Quantum Algorithm (VQA)
- ✗ `kernel_regression.py` → Quantum Neural Network (QNN)
- ✗ `kernel_regression.py` → SWAP Test
- ✗ `ode_solver.py` → Quantum Logical Operators
- ✗ `ode_solver.py` → Quantum Neural Network (QNN)
- ✗ `ode_solver.py` → SWAP Test

## Combined GT: False Negatives (GT has, tool missed)

- ✗ `quickstart.py` → Hamiltonian Simulation
- ✗ `quickstart.py` → Variational Quantum Eigensolver (VQE)
- ✗ `binary_paintshop.py` → Variational Quantum Algorithm (VQA)
- ✗ `qaoa_ising.py` → Variational Quantum Algorithm (VQA)
- ✗ `qaoa_maxcut.py` → Variational Quantum Algorithm (VQA)
- ✗ `encodings.py` → Data Encoding
- ✗ `grover.py` → Amplitude Amplification
- ✗ `qcnn.py` → Quantum Neural Network (QNN)
- ✗ `layered_encoding_circuit.py` → Data Encoding
- ✗ `example_qcnn_encoding_circuit.py` → Data Encoding

## Per-Pattern: QPanda-2

| Pattern | GT | Pred | TP | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| Variational Quantum Eigensolver (VQE) | 4 | 4 | 3 | 0.750 | 0.750 | 0.750 |
| Quantum Approximate Optimization Algorithm (QAOA) | 6 | 9 | 5 | 0.556 | 0.833 | 0.667 |
| Grover | 1 | 2 | 1 | 0.500 | 1.000 | 0.667 |
| Variational Quantum Algorithm (VQA) | 6 | 7 | 2 | 0.286 | 0.333 | 0.308 |
| Hamiltonian Simulation | 2 | 14 | 2 | 0.143 | 1.000 | 0.250 |
| Amplitude Amplification | 1 | 0 | 0 | 0.000 | 0.000 | 0.000 |
| Oracle | 1 | 0 | 0 | 0.000 | 0.000 | 0.000 |

## QPanda-2: True Positives

- ✓ `VQE_NoGradient.py` → Variational Quantum Eigensolver (VQE)
- ✓ `noisyqaoa.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `Hamitonian_Simulation_Test.py` → Hamiltonian Simulation
- ✓ `Variational Quantum Eigensolver.py` → Variational Quantum Eigensolver (VQE)
- ✓ `qaoa tutorial.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `quantum_gradient.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `vqe.py` → Variational Quantum Algorithm (VQA)
- ✓ `vqe.py` → Variational Quantum Eigensolver (VQE)
- ✓ `Grover.py` → Grover
- ✓ `hamiltonian_simulation.py` → Hamiltonian Simulation
- ✓ `hamiltonian_simulation.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `variational_qaoa_citcuit.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✓ `variational_qaoa_citcuit.py` → Variational Quantum Algorithm (VQA)

## QPanda-2: False Positives

- ✗ `ShorTest.py` → Basis Change
- ✗ `ShorTest.py` → Quantum Arithmetic
- ✗ `ShorTest.py` → Quantum Logical Operators
- ✗ `VQE_Gradient.py` → Hamiltonian Simulation
- ✗ `VQE_Gradient.py` → Initialization
- ✗ `VQE_Gradient.py` → Variational Quantum Algorithm (VQA)
- ✗ `VQE_NoGradient.py` → Hamiltonian Simulation
- ✗ `VQE_NoGradient.py` → Initialization
- ✗ `cancer_classifier.py` → Circuit Construction Utility
- ✗ `cancer_classifier.py` → Initialization
- ✗ `cancer_classifier.py` → Variational Quantum Algorithm (VQA)
- ✗ `noisyqaoa.py` → Hamiltonian Simulation
- ✗ `noisyqaoa.py` → Variational Quantum Algorithm (VQA)
- ✗ `Hello, QPanda.py` → Creating Entanglement
- ✗ `Variational Quantum Eigensolver.py` → Hamiltonian Simulation
- ✗ `quantum_circuit_learning.py` → Circuit Construction Utility
- ✗ `quantum_circuit_learning.py` → Hamiltonian Simulation
- ✗ `quantum_circuit_learning.py` → Initialization
- ✗ `quantum_gradient.py` → Hamiltonian Simulation
- ✗ `quantum_gradient_qaoa_test.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `vqe.py` → Hamiltonian Simulation
- ✗ `fragments.py` → Quantum Logical Operators
- ✗ `qaoa_maxcut_test.py` → Hamiltonian Simulation
- ✗ `qaoa_maxcut_test.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `qaoa_test.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `quantum_gradient_qaoa_test.py` → Hamiltonian Simulation
- ✗ `quantum_gradient_qaoa_test.py` → Quantum Approximate Optimization Algorithm (QAOA)
- ✗ `test_script.py` → Grover
- ✗ `vqe_test.py` → Hamiltonian Simulation
- ✗ `vqe_test.py` → Variational Quantum Algorithm (VQA)
- ✗ `vqe_test.py` → Variational Quantum Eigensolver (VQE)
- ✗ `variational_qaoa_citcuit.py` → Domain Specific Application
- ✗ `variational_qaoa_citcuit.py` → Hamiltonian Simulation
- ✗ `qaoaTest.py` → Hamiltonian Simulation
- ✗ `qaoaTest.py` → Variational Quantum Algorithm (VQA)

## QPanda-2: False Negatives

- ✗ `VQE_Gradient.py` → Variational Quantum Eigensolver (VQE)
- ✗ `Variational Quantum Eigensolver.py` → Variational Quantum Algorithm (VQA)
- ✗ `qaoa tutorial.py` → Variational Quantum Algorithm (VQA)
- ✗ `quantum_gradient.py` → Variational Quantum Algorithm (VQA)
- ✗ `Deustch_Jozsa.py` → Oracle
- ✗ `Grover.py` → Amplitude Amplification
- ✗ `hamiltonian_simulation.py` → Variational Quantum Algorithm (VQA)
- ✗ `qaoaTest.py` → Quantum Approximate Optimization Algorithm (QAOA)

# QUANTUM CONCEPT ANALYSIS REPORT

## I. Overall Summary
- **Total Projects Analyzed:** 52
- **Total Python Scripts:** 1363
- **Projects with Matches:** 41
- **Total Matches Found:** 3593
- **Unique Files with Matches:** 576
- **Unique Concepts Matched:** 560
- **Total Patterns Defined:** 22
- **Total Patterns Found:** 22
- **Average Similarity Score:** 0.8939

### Qrisp Evaluation (two-phase pipeline)
- **Micro P / R / F1:** 0.800 / 0.667 / 0.727
- **Macro P / R / F1:** 0.705 / 0.564 / 0.611
- **GT pairs:** 36  |  **TP:** 24  |  **FP:** 7

## II. Match Type Breakdown

### Match Type Counts

| match_type   |   count |
|:-------------|--------:|
| name         |    1816 |
| title        |    1710 |
| summary      |      66 |
| pattern_desc |       1 |

### Average Score by Match Type

| match_type   |   similarity_score |
|:-------------|-------------------:|
| name         |             0.9868 |
| pattern_desc |             0.8137 |
| summary      |             0.8032 |
| title        |             0.7987 |

---

## III. Source Framework & Target Project Breakdown

### Matches by Source Framework

| framework                                 |   count |
|:------------------------------------------|--------:|
| dynamic (qml)                             |     290 |
| classiq                                   |     289 |
| dynamic (tensorcircuit-ng)                |     262 |
| dynamic (tensorcircuit)                   |     226 |
| dynamic (qiskit-optimization)             |     225 |
| dynamic (qibo)                            |     217 |
| dynamic (Qrisp)                           |     208 |
| dynamic (ReCirq)                          |     163 |
| dynamic (squlearn)                        |     148 |
| qiskit                                    |     145 |
| dynamic (Qualtran)                        |     143 |
| dynamic (amazon-braket-algorithm-library) |     139 |
| qiskit-algorithms                         |     120 |
| qiskit_machine_learning                   |     100 |
| dynamic (merlin)                          |      93 |
| pennylane                                 |      83 |
| dynamic (blueqatSDK)                      |      74 |
| dynamic (Tangelo)                         |      60 |
| dynamic (ProjectQ)                        |      58 |
| dynamic (torchquantum)                    |      52 |
| dynamic (Cirq)                            |      51 |
| dynamic (qadence)                         |      48 |
| dynamic (quimb)                           |      45 |
| dynamic (qiskit-nature)                   |      39 |
| dynamic (scikit-qulacs)                   |      38 |
| dynamic (qiskit-metal)                    |      32 |
| dynamic (graphix)                         |      29 |
| dynamic (discopy)                         |      21 |
| dynamic (jarvis)                          |      17 |
| dynamic (pyquil)                          |      16 |
| dynamic (qclib)                           |      15 |
| dynamic (metriq-gym)                      |      13 |
| dynamic (tensorflow-quantum)              |      12 |
| dynamic (deltakit)                        |      12 |
| dynamic (catalyst)                        |      11 |
| dynamic (qiskit-addon-sqd)                |      11 |
| dynamic (qBraid)                          |      11 |
| dynamic (oqpy)                            |      10 |
| dynamic (OpenFermion-FQE)                 |       9 |
| dynamic (thewalrus)                       |       7 |
| dynamic (piquasso)                        |       7 |
| dynamic (mitiq)                           |       7 |
| dynamic (pennylane-rigetti)               |       7 |
| dynamic (OpenFermion)                     |       5 |
| dynamic (client-superstaq)                |       5 |
| dynamic (Perceval)                        |       4 |
| dynamic (QuCumber)                        |       3 |
| dynamic (predictor)                       |       3 |
| dynamic (qecc)                            |       2 |
| dynamic (ARC-Alkali-Rydberg-Calculator)   |       1 |
| dynamic (pyqtorch)                        |       1 |
| dynamic (qutip)                           |       1 |
| dynamic (amazon-braket-sdk-python)        |       1 |
| dynamic (guppylang)                       |       1 |
| pattern_desc                              |       1 |
| dynamic (qiskit-addon-cutting)            |       1 |
| dynamic (tqec)                            |       1 |

### Matches by Target Project

| project                                                 |   count |
|:--------------------------------------------------------|--------:|
| classiq-library                                         |    1342 |
| tensorcircuit-ng                                        |     320 |
| tensorcircuit                                           |     317 |
| Cirq                                                    |     156 |
| qiskit-algorithms                                       |     149 |
| qiskit-machine-learning                                 |     149 |
| Qualtran                                                |     145 |
| amazon-braket-algorithm-library                         |     135 |
| qiskit-optimization                                     |     106 |
| merlin                                                  |      86 |
| squlearn                                                |      83 |
| Perceval                                                |      75 |
| qiskit-finance                                          |      66 |
| ReCirq                                                  |      47 |
| qiskit-metal                                            |      45 |
| guppylang                                               |      38 |
| torchquantum                                            |      36 |
| ProjectQ                                                |      31 |
| covalent                                                |      25 |
| qiskit-braket-provider                                  |      25 |
| client-superstaq                                        |      24 |
| qibo                                                    |      23 |
| quimb                                                   |      22 |
| scikit-qulacs                                           |      22 |
| qiskit-nature                                           |      21 |
| catalyst                                                |      15 |
| Pulser                                                  |      14 |
| tensorflow-quantum                                      |      13 |
| deltakit                                                |      12 |
| qiskit-addon-cutting                                    |      11 |
| piquasso                                                |       8 |
| qecc                                                    |       7 |
| quantum-computing-exploration-for-drug-discovery-on-aws |       7 |
| qiskit-addon-sqd                                        |       5 |
| OpenFermion                                             |       4 |
| thewalrus                                               |       2 |
| discopy                                                 |       2 |
| qiskit-addon-obp                                        |       2 |
| ARC-Alkali-Rydberg-Calculator                           |       1 |
| mitiq                                                   |       1 |
| tqec                                                    |       1 |

---

## IV. Cross-Framework Pattern Analysis

### Table 4.1: Source Pattern Analysis (Where patterns originate)

| pattern                                           |   Total Matches | Source Frameworks                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|:--------------------------------------------------|----------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Quantum Approximate Optimization Algorithm (QAOA) |            1039 | classiq, dynamic (Cirq), dynamic (Qrisp), dynamic (ReCirq), dynamic (amazon-braket-algorithm-library), dynamic (blueqatSDK), dynamic (metriq-gym), dynamic (qibo), dynamic (qiskit-optimization), dynamic (qml), dynamic (quimb), dynamic (squlearn), dynamic (tensorcircuit), dynamic (tensorcircuit-ng), qiskit, qiskit-algorithms                                                                                                                                                      |
| Variational Quantum Eigensolver (VQE)             |             367 | dynamic (OpenFermion-FQE), dynamic (Qrisp), dynamic (Tangelo), dynamic (blueqatSDK), dynamic (jarvis), dynamic (qibo), dynamic (qiskit-nature), dynamic (qiskit-optimization), dynamic (qml), dynamic (tensorcircuit), dynamic (tensorcircuit-ng), dynamic (torchquantum), pennylane, qiskit-algorithms                                                                                                                                                                                   |
| Quantum Phase Estimation (QPE)                    |             337 | classiq, dynamic (Cirq), dynamic (ProjectQ), dynamic (Qrisp), dynamic (Qualtran), dynamic (Tangelo), dynamic (amazon-braket-algorithm-library), dynamic (pyquil), dynamic (qiskit-addon-sqd), dynamic (qml), pennylane, qiskit, qiskit-algorithms                                                                                                                                                                                                                                         |
| Variational Quantum Algorithm (VQA)               |             304 | classiq, dynamic (ReCirq), dynamic (Tangelo), dynamic (amazon-braket-algorithm-library), dynamic (client-superstaq), dynamic (graphix), dynamic (jarvis), dynamic (merlin), dynamic (predictor), dynamic (pyquil), dynamic (qadence), dynamic (qibo), dynamic (qiskit-nature), dynamic (qiskit-optimization), dynamic (qml), dynamic (quimb), dynamic (squlearn), dynamic (tensorcircuit-ng), dynamic (tensorflow-quantum), pennylane, qiskit, qiskit-algorithms, qiskit_machine_learning |
| Basis Change                                      |             281 | classiq, dynamic (Cirq), dynamic (OpenFermion), dynamic (Qrisp), dynamic (Qualtran), dynamic (amazon-braket-algorithm-library), dynamic (qadence), dynamic (qibo), pennylane, qiskit                                                                                                                                                                                                                                                                                                      |
| Quantum Neural Network (QNN)                      |             203 | dynamic (Cirq), dynamic (QuCumber), dynamic (merlin), dynamic (qadence), dynamic (qibo), dynamic (qml), dynamic (scikit-qulacs), dynamic (squlearn), dynamic (tensorflow-quantum), pennylane, qiskit_machine_learning                                                                                                                                                                                                                                                                     |
| Circuit Construction Utility                      |             176 | classiq, dynamic (Cirq), dynamic (ProjectQ), dynamic (Qrisp), dynamic (Tangelo), dynamic (amazon-braket-algorithm-library), dynamic (amazon-braket-sdk-python), dynamic (blueqatSDK), dynamic (discopy), dynamic (qclib), dynamic (qibo), dynamic (qiskit-addon-cutting), dynamic (qml), dynamic (tensorcircuit-ng), dynamic (torchquantum), pennylane, qiskit                                                                                                                            |
| SWAP Test                                         |             119 | classiq, dynamic (Cirq), dynamic (merlin), dynamic (mitiq), dynamic (piquasso), dynamic (qadence), dynamic (quimb), dynamic (qutip), dynamic (scikit-qulacs), dynamic (squlearn), dynamic (thewalrus), qiskit-algorithms, qiskit_machine_learning                                                                                                                                                                                                                                         |
| Data Encoding                                     |             111 | classiq, dynamic (Perceval), dynamic (Qrisp), dynamic (Qualtran), dynamic (merlin), dynamic (qecc), dynamic (qiskit-optimization), dynamic (qml), dynamic (squlearn), dynamic (tqec), pennylane, qiskit, qiskit_machine_learning                                                                                                                                                                                                                                                          |
| Oracle                                            |             109 | classiq, dynamic (ProjectQ), dynamic (Qrisp), dynamic (Qualtran), dynamic (amazon-braket-algorithm-library), dynamic (catalyst), dynamic (qiskit-optimization), dynamic (qml), pennylane, qiskit                                                                                                                                                                                                                                                                                          |
| Grover                                            |              87 | classiq, dynamic (Qrisp), dynamic (amazon-braket-algorithm-library), dynamic (catalyst), dynamic (qibo), dynamic (qiskit-optimization), dynamic (qml), dynamic (torchquantum), pennylane, qiskit, qiskit-algorithms                                                                                                                                                                                                                                                                       |
| Quantum Arithmetic                                |              83 | classiq, dynamic (Cirq), dynamic (Perceval), dynamic (ProjectQ), dynamic (Qualtran), dynamic (discopy), dynamic (pennylane-rigetti), dynamic (pyqtorch), dynamic (pyquil), dynamic (qBraid), dynamic (qclib), dynamic (qiskit-optimization), dynamic (quimb), pattern_desc, pennylane, qiskit                                                                                                                                                                                             |
| Quantum Logical Operators                         |              74 | dynamic (Cirq), dynamic (Perceval), dynamic (Qrisp), dynamic (Qualtran), dynamic (client-superstaq), dynamic (deltakit), dynamic (graphix), dynamic (guppylang), dynamic (oqpy), dynamic (tensorcircuit), dynamic (tensorcircuit-ng), qiskit                                                                                                                                                                                                                                              |
| Linear Combination of Unitaries                   |              53 | classiq, dynamic (Cirq), dynamic (Qrisp), pennylane                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Quantum Amplitude Estimation                      |              53 | classiq, dynamic (OpenFermion), dynamic (Qrisp), dynamic (merlin), dynamic (qibo), qiskit-algorithms                                                                                                                                                                                                                                                                                                                                                                                      |
| Initialization                                    |              53 | classiq, dynamic (Cirq), dynamic (merlin), dynamic (qiskit-optimization), dynamic (qml), dynamic (quimb), dynamic (torchquantum), pennylane, qiskit                                                                                                                                                                                                                                                                                                                                       |
| Function Table                                    |              37 | dynamic (Cirq), dynamic (OpenFermion), dynamic (Qualtran), dynamic (qiskit-metal), dynamic (tensorcircuit-ng)                                                                                                                                                                                                                                                                                                                                                                             |
| Amplitude Amplification                           |              30 | classiq, dynamic (Qualtran), dynamic (qiskit-optimization), pennylane, qiskit-algorithms                                                                                                                                                                                                                                                                                                                                                                                                  |
| Hamiltonian Simulation                            |              28 | classiq, dynamic (Qrisp), dynamic (Qualtran), qiskit, qiskit-algorithms                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Creating Entanglement                             |              19 | classiq, dynamic (graphix), dynamic (qibo), qiskit                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Domain Specific Application                       |              18 | dynamic (merlin), dynamic (tensorflow-quantum), pennylane, qiskit_machine_learning                                                                                                                                                                                                                                                                                                                                                                                                        |
| Dynamic Circuit                                   |              12 | dynamic (ARC-Alkali-Rydberg-Calculator), dynamic (tensorcircuit), dynamic (tensorcircuit-ng), pennylane                                                                                                                                                                                                                                                                                                                                                                                   |

### Table 4.2: Adoption Pattern Analysis (Where patterns are used)

| pattern                                           |   Project Coverage | Found In Projects                                                                                                                                                                                                                                                                                                                                                                                                                                               |
|:--------------------------------------------------|-------------------:|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Circuit Construction Utility                      |                 28 | Cirq, OpenFermion, Perceval, ProjectQ, Qualtran, ReCirq, amazon-braket-algorithm-library, catalyst, classiq-library, client-superstaq, covalent, deltakit, discopy, merlin, qiskit-addon-cutting, qiskit-addon-obp, qiskit-algorithms, qiskit-braket-provider, qiskit-finance, qiskit-machine-learning, qiskit-optimization, quantum-computing-exploration-for-drug-discovery-on-aws, quimb, squlearn, tensorcircuit, tensorcircuit-ng, thewalrus, torchquantum |
| Variational Quantum Algorithm (VQA)               |                 21 | Cirq, Perceval, Qualtran, ReCirq, classiq-library, client-superstaq, covalent, merlin, qibo, qiskit-addon-cutting, qiskit-algorithms, qiskit-braket-provider, qiskit-finance, qiskit-machine-learning, qiskit-nature, qiskit-optimization, squlearn, tensorcircuit, tensorcircuit-ng, tensorflow-quantum, torchquantum                                                                                                                                          |
| Quantum Approximate Optimization Algorithm (QAOA) |                 14 | Pulser, ReCirq, amazon-braket-algorithm-library, classiq-library, covalent, guppylang, qiskit-algorithms, qiskit-braket-provider, qiskit-finance, qiskit-optimization, quimb, squlearn, tensorcircuit, tensorcircuit-ng                                                                                                                                                                                                                                         |
| Quantum Logical Operators                         |                 14 | Cirq, Perceval, Qualtran, classiq-library, client-superstaq, deltakit, guppylang, qecc, qiskit-algorithms, qiskit-finance, qiskit-nature, quimb, tensorcircuit, tensorcircuit-ng                                                                                                                                                                                                                                                                                |
| SWAP Test                                         |                 13 | Cirq, Perceval, Pulser, ReCirq, classiq-library, covalent, merlin, piquasso, qiskit-algorithms, qiskit-machine-learning, quimb, scikit-qulacs, squlearn                                                                                                                                                                                                                                                                                                         |
| Variational Quantum Eigensolver (VQE)             |                 13 | Cirq, Perceval, ProjectQ, classiq-library, client-superstaq, qiskit-algorithms, qiskit-braket-provider, qiskit-finance, qiskit-nature, qiskit-optimization, tensorcircuit, tensorcircuit-ng, torchquantum                                                                                                                                                                                                                                                       |
| Quantum Neural Network (QNN)                      |                 12 | Cirq, classiq-library, covalent, merlin, qibo, qiskit-machine-learning, quimb, scikit-qulacs, squlearn, tensorcircuit, tensorcircuit-ng, tensorflow-quantum                                                                                                                                                                                                                                                                                                     |
| Initialization                                    |                 12 | Cirq, Pulser, Qualtran, classiq-library, merlin, qiskit-addon-sqd, qiskit-machine-learning, qiskit-optimization, quimb, tensorcircuit, tensorcircuit-ng, torchquantum                                                                                                                                                                                                                                                                                           |
| Oracle                                            |                 11 | Cirq, Perceval, ProjectQ, Qualtran, amazon-braket-algorithm-library, catalyst, classiq-library, guppylang, qiskit-algorithms, tensorcircuit, tensorcircuit-ng                                                                                                                                                                                                                                                                                                   |
| Quantum Arithmetic                                |                 10 | Cirq, Qualtran, classiq-library, covalent, qiskit-finance, qiskit-metal, qiskit-optimization, quantum-computing-exploration-for-drug-discovery-on-aws, tensorcircuit, tensorcircuit-ng                                                                                                                                                                                                                                                                          |
| Data Encoding                                     |                 10 | Qualtran, catalyst, classiq-library, covalent, merlin, qecc, qiskit-machine-learning, qiskit-optimization, squlearn, tqec                                                                                                                                                                                                                                                                                                                                       |
| Grover                                            |                  9 | Cirq, Perceval, amazon-braket-algorithm-library, catalyst, classiq-library, qiskit-algorithms, qiskit-finance, qiskit-optimization, squlearn                                                                                                                                                                                                                                                                                                                    |
| Basis Change                                      |                  8 | Cirq, OpenFermion, Qualtran, ReCirq, amazon-braket-algorithm-library, catalyst, classiq-library, qibo                                                                                                                                                                                                                                                                                                                                                           |
| Creating Entanglement                             |                  7 | Perceval, classiq-library, guppylang, qiskit-addon-obp, qiskit-algorithms, qiskit-machine-learning, qiskit-nature                                                                                                                                                                                                                                                                                                                                               |
| Quantum Phase Estimation (QPE)                    |                  6 | Cirq, Qualtran, amazon-braket-algorithm-library, classiq-library, guppylang, qiskit-addon-sqd                                                                                                                                                                                                                                                                                                                                                                   |
| Domain Specific Application                       |                  6 | Perceval, merlin, mitiq, piquasso, qiskit-machine-learning, tensorflow-quantum                                                                                                                                                                                                                                                                                                                                                                                  |
| Dynamic Circuit                                   |                  6 | ARC-Alkali-Rydberg-Calculator, Cirq, classiq-library, quimb, tensorcircuit, tensorcircuit-ng                                                                                                                                                                                                                                                                                                                                                                    |
| Linear Combination of Unitaries                   |                  6 | Cirq, Perceval, Qualtran, classiq-library, tensorcircuit, tensorcircuit-ng                                                                                                                                                                                                                                                                                                                                                                                      |
| Amplitude Amplification                           |                  5 | Cirq, Qualtran, catalyst, classiq-library, qiskit-algorithms                                                                                                                                                                                                                                                                                                                                                                                                    |
| Function Table                                    |                  5 | OpenFermion, Qualtran, covalent, qiskit-metal, tensorcircuit-ng                                                                                                                                                                                                                                                                                                                                                                                                 |
| Hamiltonian Simulation                            |                  4 | Qualtran, classiq-library, client-superstaq, qiskit-algorithms                                                                                                                                                                                                                                                                                                                                                                                                  |
| Quantum Amplitude Estimation                      |                  3 | classiq-library, qibo, qiskit-finance                                                                                                                                                                                                                                                                                                                                                                                                                           |

---

## V. Quantum Pattern Analysis

### Analysis of Newly Defined Patterns

Found **9** out of **9** newly defined patterns in the target projects.
| Pattern                         |   Matches |
|:--------------------------------|----------:|
| Basis Change                    |       281 |
| Circuit Construction Utility    |       176 |
| Data Encoding                   |       111 |
| Quantum Arithmetic              |        83 |
| Quantum Logical Operators       |        74 |
| Quantum Amplitude Estimation    |        53 |
| Linear Combination of Unitaries |        53 |
| Hamiltonian Simulation          |        28 |
| Domain Specific Application     |        18 |

### Patterns by Match Count (Overall)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Approximate Optimization Algorithm (QAOA) |    1039 |
| Variational Quantum Eigensolver (VQE)             |     367 |
| Quantum Phase Estimation (QPE)                    |     337 |
| Variational Quantum Algorithm (VQA)               |     304 |
| Basis Change                                      |     281 |
| Quantum Neural Network (QNN)                      |     203 |
| Circuit Construction Utility                      |     176 |
| SWAP Test                                         |     119 |
| Data Encoding                                     |     111 |
| Oracle                                            |     109 |
| Grover                                            |      87 |
| Quantum Arithmetic                                |      83 |
| Quantum Logical Operators                         |      74 |
| Linear Combination of Unitaries                   |      53 |
| Quantum Amplitude Estimation                      |      53 |
| Initialization                                    |      53 |
| Function Table                                    |      37 |
| Amplitude Amplification                           |      30 |
| Hamiltonian Simulation                            |      28 |
| Creating Entanglement                             |      19 |
| Domain Specific Application                       |      18 |
| Dynamic Circuit                                   |      12 |

### Average Score by Pattern

| pattern                                           |   similarity_score |
|:--------------------------------------------------|-------------------:|
| Dynamic Circuit                                   |             1      |
| Basis Change                                      |             0.9987 |
| Oracle                                            |             0.9975 |
| Amplitude Amplification                           |             0.9953 |
| Hamiltonian Simulation                            |             0.9951 |
| Domain Specific Application                       |             0.9944 |
| Quantum Logical Operators                         |             0.9941 |
| Circuit Construction Utility                      |             0.9771 |
| Linear Combination of Unitaries                   |             0.9767 |
| SWAP Test                                         |             0.9712 |
| Initialization                                    |             0.9693 |
| Data Encoding                                     |             0.9674 |
| Grover                                            |             0.9652 |
| Function Table                                    |             0.9488 |
| Quantum Amplitude Estimation                      |             0.9464 |
| Creating Entanglement                             |             0.9348 |
| Quantum Arithmetic                                |             0.9128 |
| Quantum Neural Network (QNN)                      |             0.895  |
| Variational Quantum Algorithm (VQA)               |             0.8754 |
| Variational Quantum Eigensolver (VQE)             |             0.8358 |
| Quantum Phase Estimation (QPE)                    |             0.8351 |
| Quantum Approximate Optimization Algorithm (QAOA) |             0.8318 |

### All Patterns within each Source Framework (Sorted by Frequency)


#### Classiq

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Basis Change                                      |      89 |
| Linear Combination of Unitaries                   |      33 |
| Quantum Phase Estimation (QPE)                    |      29 |
| Circuit Construction Utility                      |      24 |
| Amplitude Amplification                           |      22 |
| Hamiltonian Simulation                            |      20 |
| Initialization                                    |      20 |
| Oracle                                            |      12 |
| Data Encoding                                     |      11 |
| Quantum Arithmetic                                |       8 |
| Creating Entanglement                             |       6 |
| SWAP Test                                         |       6 |
| Grover                                            |       4 |
| Quantum Amplitude Estimation                      |       2 |
| Variational Quantum Algorithm (VQA)               |       2 |
| Quantum Approximate Optimization Algorithm (QAOA) |       1 |

#### Dynamic (arc-alkali-rydberg-calculator)

| pattern         |   count |
|:----------------|--------:|
| Dynamic Circuit |       1 |

#### Dynamic (cirq)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Approximate Optimization Algorithm (QAOA) |      14 |
| Quantum Arithmetic                                |      11 |
| Quantum Neural Network (QNN)                      |       7 |
| Circuit Construction Utility                      |       5 |
| Quantum Phase Estimation (QPE)                    |       5 |
| Quantum Logical Operators                         |       3 |
| Initialization                                    |       2 |
| Basis Change                                      |       1 |
| Function Table                                    |       1 |
| Linear Combination of Unitaries                   |       1 |
| SWAP Test                                         |       1 |

#### Dynamic (openfermion)

| pattern                      |   count |
|:-----------------------------|--------:|
| Basis Change                 |       2 |
| Quantum Amplitude Estimation |       2 |
| Function Table               |       1 |

#### Dynamic (openfermion-fqe)

| pattern                               |   count |
|:--------------------------------------|--------:|
| Variational Quantum Eigensolver (VQE) |       9 |

#### Dynamic (perceval)

| pattern                   |   count |
|:--------------------------|--------:|
| Data Encoding             |       2 |
| Quantum Arithmetic        |       1 |
| Quantum Logical Operators |       1 |

#### Dynamic (projectq)

| pattern                        |   count |
|:-------------------------------|--------:|
| Quantum Phase Estimation (QPE) |      27 |
| Circuit Construction Utility   |      17 |
| Oracle                         |      12 |
| Quantum Arithmetic             |       2 |

#### Dynamic (qrisp)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Phase Estimation (QPE)                    |      62 |
| Quantum Approximate Optimization Algorithm (QAOA) |      61 |
| Basis Change                                      |      21 |
| Variational Quantum Eigensolver (VQE)             |      19 |
| Grover                                            |      13 |
| Linear Combination of Unitaries                   |      13 |
| Circuit Construction Utility                      |       5 |
| Data Encoding                                     |       4 |
| Hamiltonian Simulation                            |       3 |
| Quantum Amplitude Estimation                      |       3 |
| Oracle                                            |       2 |
| Quantum Logical Operators                         |       2 |

#### Dynamic (qucumber)

| pattern                      |   count |
|:-----------------------------|--------:|
| Quantum Neural Network (QNN) |       3 |

#### Dynamic (qualtran)

| pattern                        |   count |
|:-------------------------------|--------:|
| Quantum Phase Estimation (QPE) |      93 |
| Oracle                         |      21 |
| Data Encoding                  |      13 |
| Quantum Logical Operators      |       4 |
| Amplitude Amplification        |       3 |
| Hamiltonian Simulation         |       3 |
| Quantum Arithmetic             |       3 |
| Function Table                 |       2 |
| Basis Change                   |       1 |

#### Dynamic (recirq)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Approximate Optimization Algorithm (QAOA) |     153 |
| Variational Quantum Algorithm (VQA)               |      10 |

#### Dynamic (tangelo)

| pattern                               |   count |
|:--------------------------------------|--------:|
| Quantum Phase Estimation (QPE)        |      20 |
| Variational Quantum Algorithm (VQA)   |      20 |
| Variational Quantum Eigensolver (VQE) |      19 |
| Circuit Construction Utility          |       1 |

#### Dynamic (amazon-braket-algorithm-library)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Approximate Optimization Algorithm (QAOA) |      52 |
| Quantum Phase Estimation (QPE)                    |      36 |
| Basis Change                                      |      21 |
| Circuit Construction Utility                      |      14 |
| Grover                                            |       8 |
| Oracle                                            |       6 |
| Variational Quantum Algorithm (VQA)               |       2 |

#### Dynamic (amazon-braket-sdk-python)

| pattern                      |   count |
|:-----------------------------|--------:|
| Circuit Construction Utility |       1 |

#### Dynamic (blueqatsdk)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Approximate Optimization Algorithm (QAOA) |      37 |
| Variational Quantum Eigensolver (VQE)             |      35 |
| Circuit Construction Utility                      |       2 |

#### Dynamic (catalyst)

| pattern   |   count |
|:----------|--------:|
| Oracle    |      10 |
| Grover    |       1 |

#### Dynamic (client-superstaq)

| pattern                             |   count |
|:------------------------------------|--------:|
| Quantum Logical Operators           |       4 |
| Variational Quantum Algorithm (VQA) |       1 |

#### Dynamic (deltakit)

| pattern                   |   count |
|:--------------------------|--------:|
| Quantum Logical Operators |      12 |

#### Dynamic (discopy)

| pattern                      |   count |
|:-----------------------------|--------:|
| Circuit Construction Utility |      14 |
| Quantum Arithmetic           |       7 |

#### Dynamic (graphix)

| pattern                             |   count |
|:------------------------------------|--------:|
| Quantum Logical Operators           |      19 |
| Creating Entanglement               |       9 |
| Variational Quantum Algorithm (VQA) |       1 |

#### Dynamic (guppylang)

| pattern                   |   count |
|:--------------------------|--------:|
| Quantum Logical Operators |       1 |

#### Dynamic (jarvis)

| pattern                               |   count |
|:--------------------------------------|--------:|
| Variational Quantum Eigensolver (VQE) |      11 |
| Variational Quantum Algorithm (VQA)   |       6 |

#### Dynamic (merlin)

| pattern                             |   count |
|:------------------------------------|--------:|
| Data Encoding                       |      31 |
| Quantum Neural Network (QNN)        |      30 |
| SWAP Test                           |      12 |
| Domain Specific Application         |      11 |
| Initialization                      |       6 |
| Quantum Amplitude Estimation        |       2 |
| Variational Quantum Algorithm (VQA) |       1 |

#### Dynamic (metriq-gym)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Approximate Optimization Algorithm (QAOA) |      13 |

#### Dynamic (mitiq)

| pattern   |   count |
|:----------|--------:|
| SWAP Test |       7 |

#### Dynamic (oqpy)

| pattern                   |   count |
|:--------------------------|--------:|
| Quantum Logical Operators |      10 |

#### Dynamic (pennylane-rigetti)

| pattern            |   count |
|:-------------------|--------:|
| Quantum Arithmetic |       7 |

#### Dynamic (piquasso)

| pattern   |   count |
|:----------|--------:|
| SWAP Test |       7 |

#### Dynamic (predictor)

| pattern                             |   count |
|:------------------------------------|--------:|
| Variational Quantum Algorithm (VQA) |       3 |

#### Dynamic (pyqtorch)

| pattern            |   count |
|:-------------------|--------:|
| Quantum Arithmetic |       1 |

#### Dynamic (pyquil)

| pattern                             |   count |
|:------------------------------------|--------:|
| Quantum Arithmetic                  |       8 |
| Quantum Phase Estimation (QPE)      |       7 |
| Variational Quantum Algorithm (VQA) |       1 |

#### Dynamic (qbraid)

| pattern            |   count |
|:-------------------|--------:|
| Quantum Arithmetic |      11 |

#### Dynamic (qadence)

| pattern                             |   count |
|:------------------------------------|--------:|
| Basis Change                        |      21 |
| Variational Quantum Algorithm (VQA) |      12 |
| Quantum Neural Network (QNN)        |       8 |
| SWAP Test                           |       7 |

#### Dynamic (qclib)

| pattern                      |   count |
|:-----------------------------|--------:|
| Circuit Construction Utility |      14 |
| Quantum Arithmetic           |       1 |

#### Dynamic (qecc)

| pattern       |   count |
|:--------------|--------:|
| Data Encoding |       2 |

#### Dynamic (qibo)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Basis Change                                      |      82 |
| Variational Quantum Eigensolver (VQE)             |      39 |
| Quantum Approximate Optimization Algorithm (QAOA) |      35 |
| Quantum Amplitude Estimation                      |      22 |
| Circuit Construction Utility                      |      14 |
| Variational Quantum Algorithm (VQA)               |      13 |
| Quantum Neural Network (QNN)                      |       7 |
| Grover                                            |       3 |
| Creating Entanglement                             |       2 |

#### Dynamic (qiskit-addon-cutting)

| pattern                      |   count |
|:-----------------------------|--------:|
| Circuit Construction Utility |       1 |

#### Dynamic (qiskit-addon-sqd)

| pattern                        |   count |
|:-------------------------------|--------:|
| Quantum Phase Estimation (QPE) |      11 |

#### Dynamic (qiskit-metal)

| pattern        |   count |
|:---------------|--------:|
| Function Table |      32 |

#### Dynamic (qiskit-nature)

| pattern                               |   count |
|:--------------------------------------|--------:|
| Variational Quantum Algorithm (VQA)   |      30 |
| Variational Quantum Eigensolver (VQE) |       9 |

#### Dynamic (qiskit-optimization)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Variational Quantum Eigensolver (VQE)             |      86 |
| Quantum Approximate Optimization Algorithm (QAOA) |      66 |
| Variational Quantum Algorithm (VQA)               |      23 |
| Grover                                            |      22 |
| Initialization                                    |      11 |
| Oracle                                            |      10 |
| Data Encoding                                     |       3 |
| Amplitude Amplification                           |       2 |
| Quantum Arithmetic                                |       2 |

#### Dynamic (qml)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Approximate Optimization Algorithm (QAOA) |     131 |
| Variational Quantum Algorithm (VQA)               |      59 |
| Quantum Phase Estimation (QPE)                    |      33 |
| Oracle                                            |      20 |
| Variational Quantum Eigensolver (VQE)             |      18 |
| Circuit Construction Utility                      |      14 |
| Quantum Neural Network (QNN)                      |       7 |
| Grover                                            |       4 |
| Data Encoding                                     |       2 |
| Initialization                                    |       2 |

#### Dynamic (quimb)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Approximate Optimization Algorithm (QAOA) |      26 |
| Quantum Arithmetic                                |       7 |
| SWAP Test                                         |       7 |
| Variational Quantum Algorithm (VQA)               |       3 |
| Initialization                                    |       2 |

#### Dynamic (qutip)

| pattern   |   count |
|:----------|--------:|
| SWAP Test |       1 |

#### Dynamic (scikit-qulacs)

| pattern                      |   count |
|:-----------------------------|--------:|
| Quantum Neural Network (QNN) |      27 |
| SWAP Test                    |      11 |

#### Dynamic (squlearn)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Neural Network (QNN)                      |      67 |
| Quantum Approximate Optimization Algorithm (QAOA) |      31 |
| Data Encoding                                     |      18 |
| Variational Quantum Algorithm (VQA)               |      17 |
| SWAP Test                                         |      15 |

#### Dynamic (tensorcircuit)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Approximate Optimization Algorithm (QAOA) |     195 |
| Variational Quantum Eigensolver (VQE)             |      25 |
| Quantum Logical Operators                         |       4 |
| Dynamic Circuit                                   |       2 |

#### Dynamic (tensorcircuit-ng)

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Quantum Approximate Optimization Algorithm (QAOA) |     195 |
| Variational Quantum Eigensolver (VQE)             |      25 |
| Circuit Construction Utility                      |      21 |
| Variational Quantum Algorithm (VQA)               |      14 |
| Quantum Logical Operators                         |       4 |
| Dynamic Circuit                                   |       2 |
| Function Table                                    |       1 |

#### Dynamic (tensorflow-quantum)

| pattern                             |   count |
|:------------------------------------|--------:|
| Quantum Neural Network (QNN)        |       5 |
| Variational Quantum Algorithm (VQA) |       4 |
| Domain Specific Application         |       3 |

#### Dynamic (thewalrus)

| pattern   |   count |
|:----------|--------:|
| SWAP Test |       7 |

#### Dynamic (torchquantum)

| pattern                               |   count |
|:--------------------------------------|--------:|
| Variational Quantum Eigensolver (VQE) |      34 |
| Initialization                        |       8 |
| Circuit Construction Utility          |       6 |
| Grover                                |       4 |

#### Dynamic (tqec)

| pattern       |   count |
|:--------------|--------:|
| Data Encoding |       1 |

#### Pattern_desc

| pattern            |   count |
|:-------------------|--------:|
| Quantum Arithmetic |       1 |

#### Pennylane

| pattern                               |   count |
|:--------------------------------------|--------:|
| Basis Change                          |      22 |
| Grover                                |      12 |
| Quantum Neural Network (QNN)          |       8 |
| Variational Quantum Algorithm (VQA)   |       8 |
| Dynamic Circuit                       |       7 |
| Quantum Arithmetic                    |       7 |
| Linear Combination of Unitaries       |       6 |
| Data Encoding                         |       3 |
| Domain Specific Application           |       3 |
| Variational Quantum Eigensolver (VQE) |       2 |
| Amplitude Amplification               |       1 |
| Circuit Construction Utility          |       1 |
| Initialization                        |       1 |
| Oracle                                |       1 |
| Quantum Phase Estimation (QPE)        |       1 |

#### Qiskit

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Variational Quantum Algorithm (VQA)               |      30 |
| Circuit Construction Utility                      |      22 |
| Basis Change                                      |      21 |
| Data Encoding                                     |      19 |
| Oracle                                            |      15 |
| Grover                                            |      12 |
| Quantum Logical Operators                         |      10 |
| Quantum Arithmetic                                |       6 |
| Quantum Approximate Optimization Algorithm (QAOA) |       3 |
| Quantum Phase Estimation (QPE)                    |       3 |
| Creating Entanglement                             |       2 |
| Hamiltonian Simulation                            |       1 |
| Initialization                                    |       1 |

#### Qiskit-algorithms

| pattern                                           |   count |
|:--------------------------------------------------|--------:|
| Variational Quantum Eigensolver (VQE)             |      36 |
| Quantum Approximate Optimization Algorithm (QAOA) |      26 |
| Quantum Amplitude Estimation                      |      22 |
| Variational Quantum Algorithm (VQA)               |      14 |
| Quantum Phase Estimation (QPE)                    |      10 |
| SWAP Test                                         |       5 |
| Grover                                            |       4 |
| Amplitude Amplification                           |       2 |
| Hamiltonian Simulation                            |       1 |

#### Qiskit_machine_learning

| pattern                             |   count |
|:------------------------------------|--------:|
| Quantum Neural Network (QNN)        |      34 |
| SWAP Test                           |      33 |
| Variational Quantum Algorithm (VQA) |      30 |
| Data Encoding                       |       2 |
| Domain Specific Application         |       1 |

---

## VI. Top Matched Concepts

### Top 20 Most Frequently Matched Concepts

| Framework                                 | Concept                  |   Matches |
|:------------------------------------------|:-------------------------|----------:|
| Dynamic (qibo)                            | ...hadamard_transform    |        61 |
| Classiq                                   | ...hadamard_transform    |        61 |
| Qiskit-algorithms                         | ...QAOA                  |        26 |
| Dynamic (merlin)                          | ...QuantumLayer          |        25 |
| Qiskit-algorithms                         | ...VQE                   |        25 |
| Dynamic (blueqatsdk)                      | ...Vqe                   |        24 |
| Dynamic (qiskit-optimization)             | ...VQE                   |        24 |
| Dynamic (torchquantum)                    | ...VQE                   |        24 |
| Dynamic (qibo)                            | ...VQE                   |        24 |
| Classiq                                   | ...apply_to_all          |        23 |
| Dynamic (tensorcircuit-ng)                | ...QAOA_ansatz_for_Ising |        22 |
| Dynamic (tensorcircuit)                   | ...QAOA_ansatz_for_Ising |        22 |
| Dynamic (qadence)                         | ...qft                   |        21 |
| Classiq                                   | ...qft                   |        21 |
| Dynamic (blueqatsdk)                      | ...qaoa                  |        21 |
| Dynamic (qml)                             | ...qaoa                  |        21 |
| Dynamic (qibo)                            | ...QAOA                  |        21 |
| Dynamic (qibo)                            | ...QFT                   |        21 |
| Dynamic (amazon-braket-algorithm-library) | ...qaoa                  |        21 |
| Dynamic (tensorcircuit-ng)                | ...any                   |        21 |

---

## VII. Unmatched Pattern Analysis

All patterns defined in the source files were found in the analysis.

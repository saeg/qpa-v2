# Pattern Classification Validation Guide

**Inter-rater Reliability Study — Quantum Programming Patterns**

---

## Overview

This guide explains how to classify quantum computing API concepts and tutorial files into one of **22 recurring software patterns**. Your classifications will be compared against two other independent raters using **Fleiss' Kappa**, a standard statistical measure of multi-rater agreement.

No prior knowledge of quantum computing is required. All the information you need is contained in the pattern descriptions and the source links provided.

---

## The Spreadsheet

The file `kappa_validation.xlsx` has five tabs:

| Tab | Contents |
|-----|----------|
| **Instructions** | This guide, embedded in the workbook |
| **Patterns Reference** | All 22 patterns with intent, aliases, and keywords |
| **Qiskit Algorithms** | 39 API concepts → assign one pattern each |
| **Qiskit ML** | 31 API concepts → assign one pattern each |
| **Qrisp GT** | 22 tutorial files → assign one or more patterns each |

**Yellow columns** show the proposer's current classification.  
**Green columns** are where you write your classification.

---

## Step-by-Step Instructions

### Tabs: Qiskit Algorithms and Qiskit ML

Each row is one API concept (a class or function from a quantum computing framework).

1. Read the **Concept Name** (column B) and **Description** (column C).
2. Click the **GitHub link** (column D) to see the full class definition, docstring, and implementation if needed.
3. In **your rater column** (F, G, or H — your name will be in the header), select the matching pattern from the dropdown list.
4. If you are uncertain between two patterns, choose the one that best matches the *primary purpose* of the concept and add a comment in the Notes column.

### Tab: Qrisp GT

Each row is one tutorial file from the Qrisp quantum framework.

1. Click the **GitHub link** (column C) to open the tutorial source file.
2. Read the file and identify **all patterns** it uses. A single tutorial can implement more than one pattern.
3. In **your rater column** (E, F, or G), type the pattern names **separated by commas**.
   - Example: `Grover, Quantum Phase Estimation (QPE), Amplitude Amplification`
4. Use **exact pattern names** as they appear in the Patterns Reference tab.

---

## Pattern Reference

Full descriptions are at: [data/pattern_descriptions.json](../data/pattern_descriptions.json)

An online version of the same patterns is available in the Qiskit documentation and the Classiq documentation.

### The 22 Patterns — Quick Reference

| # | Pattern | What it is |
|---|---------|------------|
| 1 | **Amplitude Amplification** | Boosts probability of target states via repeated oracle + diffusion. Generalises Grover. |
| 2 | **Basis Change** | Transforms a register between bases (QFT, Hadamard transform, AQFT). |
| 3 | **Circuit Construction Utility** | Low-level helper primitives — permutations, multi-control gates, gate broadcast. No standalone algorithm. |
| 4 | **Creating Entanglement** | Generates Bell/GHZ/graph states; any entangled initial state. |
| 5 | **Data Encoding** | Maps classical data into quantum states: amplitude, angle, basis encoding, feature maps. |
| 6 | **Domain Specific Application** | End-to-end algorithm for one specific domain (quantum Monte Carlo, interferometry, quantum walk, quantum finance). |
| 7 | **Dynamic Circuit** | Uses mid-circuit measurement and classical feedback to condition later gates. |
| 8 | **Function Table** | Encodes a classical function as a quantum lookup table / oracle for coherent evaluation. |
| 9 | **Grover** | Full Grover search: oracle marks solutions, diffusion operator amplifies them, for *unstructured search*. |
| 10 | **Hamiltonian Simulation** | Implements time evolution exp(−iHt) via Trotter, LCU, or qubitization. |
| 11 | **Initialization** | Prepares a non-trivial initial quantum state (uniform superposition, Dicke state, Möttönen, QROM). |
| 12 | **Linear Combination of Unitaries** | Implements A = Σ αₖUₖ via PREPARE + SELECT oracles; includes block encoding, QSVT, QSP. |
| 13 | **Oracle** | Marks target states with a phase flip or bit flip; building block for amplitude amplification and search. |
| 14 | **Quantum Amplitude Estimation** | Estimates a probability using O(1/ε) quantum samples (quadratic speedup over Monte Carlo). |
| 15 | **Quantum Approximate Optimization Algorithm (QAOA)** | Combinatorial optimization by alternating cost and mixer Hamiltonians with classically optimised parameters. |
| 16 | **Quantum Arithmetic** | Reversible arithmetic on registers: addition, multiplication, modular exponentiation, comparison. |
| 17 | **Quantum Logical Operators** | Reversible boolean logic (Toffoli/AND, CNOT/XOR, NOT) inside quantum circuits. |
| 18 | **Quantum Neural Network (QNN)** | Parameterised quantum circuit used as a trainable ML model (classifier, regressor, hybrid layer). |
| 19 | **Quantum Phase Estimation (QPE)** | Estimates the eigenvalue of a unitary U for a given eigenstate using ancilla qubits + inverse QFT. |
| 20 | **SWAP Test** | Estimates overlap \|⟨φ\|ψ⟩\|² between two quantum states (Hadamard test, compute-uncompute, quantum kernel). |
| 21 | **Variational Quantum Algorithm (VQA)** | General variational training loop: parameterised ansatz + classical optimiser. Broader than VQE. |
| 22 | **Variational Quantum Eigensolver (VQE)** | Specific VQA for finding ground-state energy of a Hamiltonian (chemistry/physics). |

---

## Key Distinctions to Watch

These pairs are easy to confuse. Use the rules below.

### Grover vs Amplitude Amplification

- Use **Grover** when the concept directly implements the *full search algorithm*: it has an oracle that marks solutions and a diffusion operator, and the goal is finding marked items in an unstructured set.
- Use **Amplitude Amplification** when the concept is the *generalised subroutine* that boosts amplitudes — it may be used inside another algorithm, not necessarily for search.

> `qiskit_algorithms.amplitude_amplifiers.grover.Grover` → **Grover**  
> `qiskit_algorithms.amplitude_amplifiers.amplification_problem.AmplificationProblem` → **Amplitude Amplification** (it defines the *input* to any amplitude amplification algorithm)

### VQA vs VQE

- Use **Variational Quantum Eigensolver (VQE)** only when the concept is about finding eigenvalues of a Hamiltonian — chemistry, molecular energy, second-quantised operators.
- Use **Variational Quantum Algorithm (VQA)** for everything else that is variational: time evolution, gradient estimation, adaptive circuits, general hybrid training loops.

> `qiskit_algorithms.minimum_eigensolvers.vqe.VQE` → **VQE** (explicitly about eigenvalues)  
> `qiskit_algorithms.time_evolvers.pvqd.pvqd.PVQD` → **VQA** (variational dynamics, not eigensolving)  
> `qiskit_machine_learning.gradients.QFI` → **VQA** (quantum Fisher information for variational training)

### SWAP Test vs QNN

- Use **SWAP Test** when the concept computes *state overlap, fidelity, or a quantum kernel* — the inner product ⟨φ|ψ⟩.
- Use **QNN** when the concept uses a parameterised circuit as a *trainable model* for ML tasks.

> `qiskit_machine_learning.kernels.FidelityQuantumKernel` → **SWAP Test** (computes fidelity = overlap)  
> `qiskit_machine_learning.neural_networks.EstimatorQNN` → **QNN** (trainable quantum model)  
> `qiskit_machine_learning.algorithms.classifiers.QSVC` → **SWAP Test** (SVM using quantum kernel)

### QPE vs Hamiltonian Simulation

- **QPE** *estimates eigenvalues*. It uses controlled-U gates and an inverse QFT.
- **Hamiltonian Simulation** *evolves a quantum state in time* under a Hamiltonian. It implements exp(−iHt).

A file can legitimately use *both*: it may first simulate the Hamiltonian to prepare controlled-U^k, then apply QPE to read off the energy eigenvalue.

### Domain Specific Application

Use this only when no other pattern applies. It is for highly specialised end-to-end algorithms that are tightly coupled to one application domain:
- Quantum Monte Carlo integration
- Quantum walk (not as a subroutine in Grover — as the primary subject)
- Interferometry / photonics
- Quantum signal processing as a black-box transform (QSVT/GQSP when not used for LCU)

---

## Worked Examples

### Example 1 — Single-label (unambiguous)

**Concept:** `qiskit_algorithms.amplitude_estimators.iae.IterativeAmplitudeEstimation`  
**Description:** The Iterative Amplitude Estimation algorithm.

**Reasoning:** The name and description both explicitly reference Amplitude Estimation — a specific algorithm for estimating probabilities via Grover-like iteration, distinct from generic amplitude amplification.

**Classification: `Quantum Amplitude Estimation`**

---

### Example 2 — Single-label (requires disambiguation)

**Concept:** `qiskit_machine_learning.gradients.LinCombEstimatorGradient`  
**Description:** Computes expectation value gradients using the linear combination of unitaries method as an alternative to the parameter-shift rule.

**Reasoning:** The description mentions "linear combination of unitaries" as the *method for computing gradients*, not as an LCU block encoding circuit. The primary purpose is variational gradient computation for a VQA training loop.

**Classification: `Variational Quantum Algorithm (VQA)`** (not Linear Combination of Unitaries)

---

### Example 3 — Multi-label (Qrisp GT)

**File:** `documentation/source/general/tutorial/Sudoku.py`  
**GitHub:** https://github.com/eclipse-qrisp/Qrisp/blob/main/documentation/source/general/tutorial/Sudoku.ipynb

**After reading the file:**
- It builds an oracle that marks invalid Sudoku assignments — this is an **Oracle** component used inside a search
- It runs Grover's algorithm to find valid solutions — **Grover**
- It uses QPE to count the number of solutions before running Grover — **Quantum Phase Estimation (QPE)**
- The amplitude amplification is the mechanism inside Grover — but since the outer algorithm is full Grover search, label it **Grover** (not separately Amplitude Amplification unless the file also uses AA in a non-Grover context)

**Classification:** `Grover, Quantum Phase Estimation (QPE)`

---

### Example 4 — Multi-label (time evolution + VQA)

**File:** `documentation/source/general/tutorial/JaspQAOAtutorial.py`

**After reading the file:**
- It implements QAOA — **Quantum Approximate Optimization Algorithm (QAOA)**
- The circuit is optimised using a classical variational outer loop — **Variational Quantum Algorithm (VQA)**

*Note: QAOA is itself a VQA, so both labels are appropriate here. Label QAOA when the file's primary subject is the QAOA structure (cost + mixer + classical optimizer for combinatorial optimization).*

**Classification:** `Quantum Approximate Optimization Algorithm (QAOA), Variational Quantum Algorithm (VQA)`

---

## Contact

If you have questions about specific items, please reach out to the study authors before submitting your classifications. Do not discuss your classifications with the other raters to preserve independence.

---

*Prepared for the inter-rater reliability study of the qpa (Quantum Pattern Analyser) tool.*

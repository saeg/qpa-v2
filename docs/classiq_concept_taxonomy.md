# Classiq Quantum Concept Taxonomy

Three-tier classification based on the principle: **label what a concept is, not which algorithm uses it.**

- **Tier 1 — Basic Building Blocks**: composed of gates only; cannot be decomposed into other named blocks
- **Tier 2 — Quantum Composed Building Blocks**: composed of other named blocks from Tier 1 or Tier 2
- **Tier 3 — Applications**: end-to-end algorithms or practical solutions

---

## Tier 1 — Basic Building Blocks (31 concepts)

### State Preparation
| Concept | Description |
|---|---|
| `prepare_basis_state` | Initializes a register to a specific computational basis state |
| `prepare_bell_state` | Prepares one of the four 2-qubit Bell states |
| `prepare_ghz_state` | Prepares an n-qubit GHZ entangled state |
| `prepare_dicke_state` | Prepares a Dicke state with exactly k excitations |
| `prepare_dicke_state_unary_input` | Dicke state with variable excitations from a unary-encoded input |
| `prepare_linear_amplitudes` | State with linearly increasing amplitudes |
| `prepare_exponential_state` | State with exponentially decreasing amplitudes |
| `prepare_uniform_interval_state` | Uniform superposition over a specified interval |
| `prepare_uniform_trimmed_state` | Uniform superposition over the first m basis states |
| `prepare_int` *(deprecated)* | Initializes a register to an integer value |
| `inplace_prepare_int` *(deprecated)* | In-place integer initialization |

### Gate-level Utilities
| Concept | Description |
|---|---|
| `hadamard_transform` | Applies H gate to all qubits simultaneously |
| `apply_to_all` | Applies any single-qubit gate to every qubit in a register |
| `reflect_about_zero` | Reflects the state about \|0⟩ (a single multi-controlled phase) |
| `multiswap` | Swaps qubit states between two arrays element-wise |
| `swap_test` | Measures fidelity (overlap) between two quantum states |

### Phase & Rotation Primitives
| Concept | Description |
|---|---|
| `phase_oracle` | Applies phase kickback based on a predicate function |
| `projector_controlled_phase` | Assigns a phase to an entire subspace defined by a projector |
| `projector_controlled_double_phase` | Assigns two phases to a subspace with two separate controls |
| `linear_pauli_rotations` | Pauli rotations whose angle is a linear function of a quantum register |

### Arithmetic Primitives
| Concept | Description |
|---|---|
| `modular_increment` | Adds a constant a to x modulo the range of x |
| `qft_space_add_const` | Adds a constant to a register already in QFT (Fourier) space |
| `modular_add_qft_space` | Modular constant addition when register is in QFT space |
| `cc_modular_add` | Doubly controlled modular addition of a constant |

### QAOA Layers
| Concept | Description |
|---|---|
| `qaoa_init` | Initializes QAOA by applying H to all qubits |
| `qaoa_cost_layer` | Applies the cost Hamiltonian layer |
| `qaoa_mixer_layer` | Applies the X-rotation mixer layer |
| `qaoa_penalty` | Applies a penalty term layer to the QAOA circuit |

### Ansatz & Simulation Primitives
| Concept | Description |
|---|---|
| `full_hea` | Hardware-efficient ansatz with configurable 1- and 2-qubit gate layers |
| `encode_in_angle` | Angle encoding: maps n classical values to n qubit rotations |
| `encode_on_bloch` | Dense angle encoding: maps n values to n/2 qubits via Ry/Rz |
| `suzuki_trotter` | *(moved to Tier 2 — see below)* |

---

## Tier 2 — Quantum Composed Building Blocks (31 concepts)

### Fourier & Signal Transforms
| Concept | Composition | Description |
|---|---|---|
| `qft` | H gates + controlled-Rk phase rotations + SWAP gates | Full Quantum Fourier Transform |
| `qft_no_swap` | H gates + controlled-Rk phase rotations | QFT without the final bit-reversal swap layer |
| `qct_qst_type1` | qft + diagonal phase pre/post-processing gates | Quantum DCT and DST of type 1 |
| `qct_qst_type2` | qft + diagonal phase shifts (π·k/2N scaling) + qubit reordering | Quantum DCT and DST of type 2 |
| `qct_type2` | qft + type-2 DCT-specific phase pre/post-multiplications | Quantum DCT type 2 only |
| `qst_type2` | qft + type-2 DST-specific phase pre/post-multiplications | Quantum DST type 2 only |

### Amplitude Amplification Components
| Concept | Composition | Description |
|---|---|---|
| `grover_diffuser` | space_transform (A) + reflect_about_zero + space_transform† (A†) | Reflects about A\|0⟩; the diffusion step of Grover |
| `grover_operator` | phase_oracle + grover_diffuser | Full Grover iterate: marks solution then reflects about mean |
| `amplitude_amplification` | state_prep (A) + [phase_oracle + grover_diffuser] × k iterations | General AA loop with configurable oracle and state preparation |
| `exact_amplitude_amplification` | state_prep (A) + [phase_oracle + grover_diffuser] × k* (analytically derived) | AA variant that computes the exact number of iterations to avoid overshoot |

### Phase Estimation
| Concept | Composition | Description |
|---|---|---|
| `qpe` | H gates (ancilla) + controlled-U^(2^j) + qft_no_swap† | Standard QPE: encodes eigenphase into ancilla then reads via inverse QFT |
| `qpe_flexible` | H gates (ancilla) + controlled-U^(2^j) (configurable) + qft† | QPE with configurable ancilla width and unitary interface |

### Linear Combination of Unitaries
| Concept | Composition | Description |
|---|---|---|
| `lcu` | PREPARE (prepare_complex_amplitudes) + SELECT (controlled-U_i per term) + PREPARE† | General LCU: PREPARE selects a weighted superposition, SELECT applies matching unitary |
| `lcu_pauli` | PREPARE (Pauli coefficients) + SELECT (controlled Pauli applications) + PREPARE† | LCU specialised for Pauli-sum Hamiltonians |

### QSVT Framework Components
| Concept | Composition | Description |
|---|---|---|
| `qsvt_step` | projector_controlled_phase (φ_k) + block_encoding (U) + projector_controlled_phase (φ_{k+1}) | Single QSVT iteration: two phase rotations interleaved with one block-encoding application |
| `qsvt_lcu_step` | projector_controlled_double_phase (×2) + block_encoding (U) + block_encoding† | QSVT-LCU step handling simultaneously odd and even polynomial components |
| `qsvt` | block_encoding + qsvt_step × d (d = polynomial degree) | Sequences d QSVT steps to realize a degree-d polynomial transformation |
| `qsvt_lcu` | block_encoding + qsvt_lcu_step × d | QSVT for a linear combination of an odd and an even polynomial |
| `gqsp` | Rz rotations (signal angles φ_k) + controlled-U applications, interleaved | Generalized QSP: achieves a Laurent polynomial transformation |

### Modular Arithmetic (composed)
| Concept | Composition | Description |
|---|---|---|
| `modular_multiply` | qft + cc_modular_add × n + qft† | Out-of-place modular multiplication via iterated QFT-space additions |
| `c_modular_multiply` | controlled-qft + controlled-(cc_modular_add × n) + controlled-qft† | Controlled modular multiplication |
| `inplace_modular_multiply` | c_modular_multiply + multiswap + c_modular_multiply† (a^{-1} mod n) | In-place modular multiply via ancilla, swap, and uncompute |
| `inplace_c_modular_multiply` | controlled-inplace_modular_multiply | Controlled in-place modular multiply |
| `modular_exp` | inplace_c_modular_multiply × n (one per exponent bit, applying a^{2^j} mod n) | Modular exponentiation — core subroutine of Shor's algorithm |
| `span_lookup_table` | unary_iteration + X gates (per address) + unary_iteration† | Applies a classical lookup function via ROM-style multiplexed write |

### State Preparation (complex)
| Concept | Composition | Description |
|---|---|---|
| `prepare_complex_amplitudes` | Binary tree of Ry (amplitudes) + Rz (phases) rotations (Shende–Mottonen) | Prepares arbitrary complex amplitudes given in polar form |
| `inplace_prepare_complex_amplitudes` | Same binary-tree Ry/Rz structure applied in-place | In-place variant of complex amplitude preparation |
| `prepare_sparse_amplitudes` | span_lookup_table + prepare_complex_amplitudes | Prepares a state from a sparse list of (index, amplitude) pairs |
| `inplace_prepare_sparse_amplitudes` | span_lookup_table (in-place) + inplace_prepare_complex_amplitudes | In-place sparse amplitude preparation |

### QAOA (composed layer)
| Concept | Composition | Description |
|---|---|---|
| `qaoa_layer` | qaoa_cost_layer + qaoa_mixer_layer | One full QAOA round with independent γ and β parameters |

### Hamiltonian Simulation
| Concept | Composition | Description |
|---|---|---|
| `suzuki_trotter` | linear_pauli_rotations (one per Pauli term) in symmetric product formula P₁·…·Pₙ·…·P₁ | Decomposes e^{-iHt} into a product of Pauli exponentials via Suzuki-Trotter |

---

## Tier 3 — Applications & Higher-Level Solutions (3 concepts)

| Concept | Composition | Description |
|---|---|---|
| `grover_search` | grover_operator (×k) + oracle + state prep | End-to-end Grover search over an unstructured database |
| `amplitude_estimation` | QPE + amplitude_amplification + oracle | Estimates the probability that a marked oracle state is "good" |
| `qsvt_inversion` | QSVT + block encoding | Practical matrix inversion via polynomial approximation of 1/x |

---

## Notes on labelling philosophy

The classification follows the principle: **label what a concept is, not which algorithm uses it.**

- A concept is Tier 1 if it is composed solely of primitive gates
- A concept is Tier 2 if it is composed of other named Tier 1 or Tier 2 blocks
- A concept is Tier 3 if it is a complete, end-to-end algorithm or application
- QAOA layers (`qaoa_init`, `qaoa_cost_layer`, `qaoa_mixer_layer`, `qaoa_penalty`) are Tier 1 primitives — they happen to be used in QAOA but their intrinsic nature is gate-level
- `reflect_about_zero` is a Tier 1 phase primitive, not the AA algorithm itself
- `grover_diffuser` and `grover_operator` are Tier 2 composed blocks, not applications

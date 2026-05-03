_TRACE_OUTPUT = '/Users/I763567/projects/qpa-v2/experiments/results/qrisp_trace/BE_vol1_raw_calls.json'
import sys as _trace_sys
import json as _trace_json

_call_log = []          # [(cell_idx, module_func)]
_current_cell = [0]

def _qrisp_tracer(frame, event, arg):
    if event != 'call':
        return _qrisp_tracer
    mod = frame.f_globals.get('__name__', '') or ''
    if not mod.startswith('qrisp'):
        return _qrisp_tracer
    fn = frame.f_code.co_name
    if fn.startswith('_'):
        return _qrisp_tracer
    _call_log.append((_current_cell[0], f"{mod}.{fn}"))
    return _qrisp_tracer

_trace_sys.settrace(_qrisp_tracer)

# ── notebook cells below ──────────────────────────────────────────────────
import numpy as np
from qrisp.block_encodings import BlockEncoding

A = np.array([[0,1,0,1],
              [1,0,0,0],
              [0,0,1,0],
              [1,0,0,0]])
B_A = BlockEncoding.from_array(A)
_current_cell[0] += 1
from qrisp.block_encodings import BlockEncoding
from qrisp.operators import X, Y

H = X(0)*X(1) + 0.2*Y(0)*Y(1)
B_H = BlockEncoding.from_operator(H)
_current_cell[0] += 1
from qrisp import conjugate, prepare, q_switch, QuantumFloat
from qrisp.operators import X, Y

H = X(0)*X(1) + 0.2*Y(0)*Y(1)

# Returns a list of unitaries, i.e., functions performing in-place operations 
# on the operand quantum variable, and a list of coefficients.
unitaries, coeffs = H.unitaries()
n = len(unitaries).bit_length() # Number of qubits for ancillary variable.
alpha = np.sum(coeffs) # Block encoding normalization factor.

# Define block-encoding unitary using LCU = PREP SELECT PREP_dg.
def U(anc, operand):
    with conjugate(prepare)(anc, coeffs):
        q_switch(anc, unitaries, operand) # quantum switch aka SELECT

BE = BlockEncoding(
    alpha,  # Block encoding normalization factor.
    [QuantumFloat(n)],  # Templates for ancilla variables.
    U,  # Block encoding unitary.
    num_ops=1,  # Number of operand variables. The default is 1.
    is_hermitian=True,  # Indicates whether the unitary is Hermitian.
)
_current_cell[0] += 1
import numpy as np

N = 16
I = np.eye(N)
L = 2 * I - np.eye(N, k=1) - np.eye(N, k=-1)
L[0, N-1] = -1
L[N-1, 0] = -1

print(L)
_current_cell[0] += 1
B_L = BlockEncoding.from_array(L)
_current_cell[0] += 1
from qrisp import QuantumFloat

# Use a 4-qubit variable for a 2^4 by 2^4 matrix.
quantum_resources = B_L.resources(QuantumFloat(4))
print(quantum_resources)
_current_cell[0] += 1
from qrisp import gphase

def I(qv):
    # Identity: do nothing
    pass

def V(qv):
    # Forward cyclic shift with a global phase -1
    qv += 1
    gphase(np.pi, qv[0])  # multiply by -1

def V_dg(qv):
    # Backward cyclic shift with a global phase -1
    qv -= 1
    gphase(np.pi, qv[0])
_current_cell[0] += 1
unitaries = [I, V, V_dg]
coeffs = np.array([2.0, 1.0, 1.0])
_current_cell[0] += 1
BE = BlockEncoding.from_lcu(coeffs, unitaries)

# Use a 4-qubit variable for a 2^4 by 2^4 matrix.
quantum_resources = BE.resources(QuantumFloat(4))
print(quantum_resources)
_current_cell[0] += 1
from qrisp import *
from qrisp.block_encodings import BlockEncoding
from qrisp.operators import X, Y, Z

H = sum(X(i)*X(i+1) + Y(i)*Y(i+1) + Z(i)*Z(i+1) for i in range(3))
BE = BlockEncoding.from_operator(H)
b = np.array([1.,2.,3.,1.,1.,2.,3.,1.,1.,2.,3.,1.,1.,2.,3.,1.])

operand = QuantumFloat(4)
prepare(operand, b)

ancillas = BE.apply(operand)
_current_cell[0] += 1
from qrisp.interface import QiskitBackend
from qiskit_aer import AerSimulator
example_backend = QiskitBackend(backend = AerSimulator())

# Use backend keyword to specify quantum backend
res_dict = multi_measurement([operand] + ancillas,
                            shots=1000000,
                            backend=example_backend)

# Post-selection on ancillas being in |0> state
filtered_dict = {k[0]: p for k, p in res_dict.items() \
                if all(x == 0 for x in k[1:])}
success_prob = sum(filtered_dict.values())
filtered_dict = {k: p / success_prob for k, p in filtered_dict.items()}
amps = np.sqrt([filtered_dict.get(i,0) for i in range(16)])
print(amps)
_current_cell[0] += 1
H_arr = H.to_array()

psi = H_arr @ b
psi = psi / np.linalg.norm(psi)
print(psi)

print(np.linalg.norm(psi-amps))
_current_cell[0] += 1
from qrisp import *
from qrisp.block_encodings import BlockEncoding
from qrisp.operators import X, Y, Z

H = sum(X(i)*X(i+1) + Y(i)*Y(i+1) + Z(i)*Z(i+1) for i in range(3))
BE = BlockEncoding.from_operator(H)

# Prepare initial system state
def operand_prep():
    operand = QuantumFloat(4)
    b = np.array([1.,2.,3.,1.,1.,2.,3.,1.,1.,2.,3.,1.,1.,2.,3.,1.])
    prepare(operand, b)
    return operand

# Apply the operator to an initial system state
@terminal_sampling
def main():
    return BE.apply_rus(operand_prep)()
res_dict = main()

amps = np.sqrt([res_dict.get(i,0) for i in range(16)])

H_arr = H.to_array()

psi = H_arr @ b
psi = psi / np.linalg.norm(psi)
print(psi)
print(np.linalg.norm(psi-amps))
_current_cell[0] += 1
from qrisp import *
from qrisp.block_encodings import BlockEncoding
from qrisp.operators import X, Z

# Define two simple operators
A = BlockEncoding.from_operator(X(0) * X(1))
B = BlockEncoding.from_operator(Z(0) * Z(1))

# Perform arithmetic: 2.5 * A - B
# Qrisp handles the LCU logic and the Z-gate for the sign flip automatically
# In practice, use BlockEncoding.from_operator(2.5 * X(0) * X(1) - Z(0) * Z(1))
H_total = 2.5 * A - B

def prep_zeros():
    return QuantumVariable(2)

@terminal_sampling
def run_arithmetic():
    # Use apply_rus to see the result of the combined operator
    return H_total.apply_rus(prep_zeros)()

print(f"New Alpha: {H_total.alpha}") # Alpha is now 2.5 + 1.0 = 3.5
print(f"Resulting Distribution: {run_arithmetic()}")
_current_cell[0] += 1
from qrisp import *
from qrisp.block_encodings import BlockEncoding
from qrisp.operators import X, Z

# Create two 2-qubit block encodings
BE1 = BlockEncoding.from_operator(X(0) * X(1))
BE2 = BlockEncoding.from_operator(Z(0) * Z(1))

# 1. Expand the Hilbert space: BE1 (on qubits 0,1) tensor BE2 (on qubits 2,3)
# The resulting BE acts on 4 qubits total.
BE_large = BE1.kron(BE2)

# 2. Composition: Multiply the large system by itself (A^2)
# The '@' operator implements operator multiplication (matrix product)
BE_squared = BE_large @ BE_large

def operand_prep():
    return QuantumVariable(2), QuantumVariable(2)
@terminal_sampling
def main():
    return BE_squared.apply_rus(operand_prep)()

print(BE_squared.resources(QuantumVariable(2), QuantumVariable(2)))# ── end of notebook cells ─────────────────────────────────────────────────
_trace_sys.settrace(None)
with open(_TRACE_OUTPUT, 'w', encoding='utf-8') as _f:
    _trace_json.dump(_call_log, _f)

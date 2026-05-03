_TRACE_OUTPUT = '/Users/I763567/projects/qpa-v2/experiments/results/qrisp_trace/GQSP_filtering_raw_calls.json'
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
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from qrisp import *
from qrisp.gqsp import GQSP
from qrisp.operators import X, Y, Z
from qrisp.vqe.problems.heisenberg import create_heisenberg_init_function


def generate_1D_chain_graph(L):
    graph = nx.Graph()
    graph.add_edges_from([(k, (k+1)%L) for k in range(L-1)])
    return graph


# Define Heisenberg Hamiltonian with spectrum in [-1,1].
L = 10
G = generate_1D_chain_graph(L)
H = (1 / (3 * L - 3)) * sum((X(i) * X(j) + Y(i) * Y(j) + Z(i) * Z(j)) \
                            for i, j in G.edges())

# Finds a maximum matching M of the graph G.
# For a chain graph G, M contains every second edge of G.
M = nx.maximal_matching(G)
# Prepares a tensor product of Singlet states 
# corresponding to the edges in M when applied to 
# a QuantumVariable in state |0>.
U0 = create_heisenberg_init_function(M)


# Define initial state preparation function
# preparing a tensor product of Singlet states.
def psi_prep():
    operand = QuantumVariable(L)
    U0(operand)
    return operand


# Calculate the energy for the initial state.
# Computes the operator's expectation value using Pauli measurement settings.
E = H.expectation_value(psi_prep, precision=0.001)()
print(E)
_current_cell[0] += 1
H_matrix = H.to_array()
eigvals, eigvecs = np.linalg.eigh(H_matrix)

idx = np.argsort(eigvals)
eigvals_sorted = eigvals[idx].real
eigvecs_sorted = eigvecs[:, idx]
print(f'Ground state energy: {eigvals_sorted[0]}\n') # lambda_0
print(f'First excited state energy: {eigvals_sorted[1]}\n') # lambda_1

psi0 = psi_prep().qs.statevector_array()
fidelities = np.abs(eigvecs_sorted.conj().T @ psi0) ** 2

threshold = 0.01
significant_mask = fidelities > threshold
indices = np.where(significant_mask)[0]

print(f'Indices: {indices}\n')
print(f'Eigenvalues: {eigvals_sorted[indices]}\n')
print(f'Fidelities: {fidelities[indices]}\n')
_current_cell[0] += 1
from numpy.polynomial import Chebyshev
from numpy.polynomial.chebyshev import chebval

# Define the Gaussian centered at minimal eigenvalue lambda_0 on [-1, 1].
mu = eigvals_sorted[0]
sigma = 0.05

def gaussian(x):
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2)

# Chebyshev fit
x_nodes = np.cos(np.pi * np.arange(201) / 200)
f_nodes = gaussian(x_nodes)
cheb_fit = Chebyshev.fit(x_nodes, f_nodes, deg=100)
cheb_coeffs = cheb_fit.coef

x_plot = np.linspace(-1, 1, 2000)
f_gaussian = gaussian(x_plot)
f_cheb_10 = chebval(x_plot, cheb_coeffs[:11]) 
f_cheb_20 = chebval(x_plot, cheb_coeffs[:21])  

# Plot
plt.figure(figsize=(10, 5))
plt.plot(x_plot, f_gaussian, color='#20306f', label='Gaussian', linewidth=2)
plt.plot(x_plot, f_cheb_10, color='#6929C4', label='d=10', linestyle='--')
plt.plot(x_plot, f_cheb_20, color='#444444', label='d=20', linestyle='--')
plt.axvline(mu, color='k', linestyle=':', alpha=0.4)
plt.xlabel('x', fontsize=15)
plt.xticks(fontsize=12)
plt.ylabel('f(x)', fontsize=15)
plt.yticks(fontsize=12)
plt.title('Chebyshev approximation of Gaussian filter', fontsize=15)
plt.legend(fontsize=15)
plt.grid()
plt.tight_layout()
plt.show()
_current_cell[0] += 1
from qrisp.block_encodings import BlockEncoding

# Encodes the operator $H$.
BE = BlockEncoding.from_operator(H)

# Encodes the operator p(H) for a degree 10 Chebychev approximation 
# of the Gaussian filter.
BE_filter = BE.poly(cheb_coeffs[:11], kind="Chebyshev") 

# Returns the filtered state.
def filtered_psi_prep():
    # Applies p(H) to the inital state |psi_0>.
    operand = BE_filter.apply_rus(psi_prep)()
    return operand
_current_cell[0] += 1
@jaspify(terminal_sampling=True)
def main(): 

    E = H.expectation_value(filtered_psi_prep, precision=0.001)()
    return E

print(main())
_current_cell[0] += 1
# Returns a list of unitaries, i.e., functions performing in-place operations 
# on the operand quantum variable, and a list of coefficients.
unitaries, coeffs = H.unitaries()
n = len(unitaries).bit_length() # Number of qubits for auxiliary variable.

# Define block-encoding unitary using LCU = PREP SELECT PREP_dg.
def U(anc, operand):
    with conjugate(prepare)(anc, coeffs):
        q_switch(anc, unitaries, operand) # quantum switch aka SELECT
_current_cell[0] += 1
@RUS
def filtered_psi_prep():

    # Qubitization step: RU^k is a block-encoding of T_k(H).
    def RU(case, operand):
        U(case, operand)
        reflection(case) # Reflection around |0>.


    # GQSP requires one 1-qubit ancilla variable.
    anc_qsp = QuantumBool()
    # Pauli block-encoding requires one n-qubit ancilla variable.
    anc_be = QuantumFloat(n)
    operand = psi_prep()

    # Apply degree 10 Chebyshev approximation of Gaussian filter.
    GQSP(anc_qsp, # Ancilla variable for GQSP protocol.
         anc_be, # Ancilla variable for block-encoding.
         operand, # Variable holding the system state |psi_0>.
         unitary=RU, # Block-encoding unitary.
         p=cheb_coeffs[:11], # Polynomial transformation to apply.
    )

    # Protocol is successful if all ancilla variables are measured in state |0>.
    success_bool = (measure(anc_qsp) == 0) & (measure(anc_be) == 0)
    # Release quantum resources.
    # The operand variable will be realeased automatically if success_bool=False.
    reset(anc_qsp)
    reset(anc_be)
    anc_qsp.delete()
    anc_be.delete()
    return success_bool, operand
_current_cell[0] += 1
@jaspify(terminal_sampling=True)
def main(): 

    E = H.expectation_value(filtered_psi_prep, precision=0.001)()
    return E

print(main())# ── end of notebook cells ─────────────────────────────────────────────────
_trace_sys.settrace(None)
with open(_TRACE_OUTPUT, 'w', encoding='utf-8') as _f:
    _trace_json.dump(_call_log, _f)

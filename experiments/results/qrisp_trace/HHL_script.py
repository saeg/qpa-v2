_TRACE_OUTPUT = '/Users/I763567/projects/qpa-v2/experiments/results/qrisp_trace/HHL_raw_calls.json'
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
from qrisp import *


def fake_inversion(qf, res=None):
    if res is None:
        res = QuantumFloat(qf.size + 1)

    for i in jrange(qf.size):
        cx(qf[i], res[qf.size - i])

    return res
_current_cell[0] += 1
qf = QuantumFloat(3, -3)
x(qf[2])
dicke_state(qf, 1)
res = fake_inversion(qf)
print(multi_measurement([qf, res]))
_current_cell[0] += 1
@RUS(static_argnums=[0, 1])
def HHL_encoding(b, hamiltonian_evolution, n, precision):

    # Prepare the state |b>. Step 1
    qf = QuantumFloat(n)
    # Reverse the endianness for compatibility with Hamiltonian simulation.
    prepare(qf, b, reversed=True)

    qpe_res = QPE(qf, hamiltonian_evolution, precision=precision)  # Step 2
    inv_res = fake_inversion(qpe_res)  # Step 3

    case_indicator = QuantumFloat(inv_res.size)

    with conjugate(h)(case_indicator):
        qbl = case_indicator >= inv_res

    cancellation_bool = (measure(case_indicator) == 0) & (measure(qbl) == 0)

    # Clean up case-indicator and qbl
    # When using the RUS decorator, all local variables of the
    # trial function need to be deallocated in order to avoid
    # quantum memory leaks.
    qrisp.reset(case_indicator)
    qrisp.reset(qbl)
    qbl.delete()
    case_indicator.delete()

    # The first return value is a boolean.
    # Additional return values are QuantumVariables.
    return cancellation_bool, qf, qpe_res, inv_res
_current_cell[0] += 1
def HHL(b, hamiltonian_evolution, n, precision):

    qf, qpe_res, inv_res = HHL_encoding(b, hamiltonian_evolution, n, precision)

    with invert():
        QPE(qf, hamiltonian_evolution, target=qpe_res)
        fake_inversion(qpe_res, res=inv_res)

    # Reverse the endianness for compatibility with Hamiltonian simulation.
    for i in jrange(qf.size // 2):
        swap(qf[i], qf[n - i - 1])

    return qf
_current_cell[0] += 1
from qrisp.operators import QubitOperator
import numpy as np

A = np.array([[3 / 8, 1 / 8], [1 / 8, 3 / 8]])

b = np.array([1, 1])

H = QubitOperator.from_matrix(A).to_pauli()


def U(qf):
    # By default e^{-itH} is performed. Therefore, we set t=-pi.
    H.trotterization()(qf, t=-np.pi, steps=1)
_current_cell[0] += 1
@terminal_sampling
def main():

    x = HHL(tuple(b), U, 1, 3)
    return x


res_dict = main()

for k, v in res_dict.items():
    res_dict[k] = v**0.5

print(res_dict)
_current_cell[0] += 1
x = (np.linalg.inv(A) @ b) / np.linalg.norm(np.linalg.inv(A) @ b)
print(x)
_current_cell[0] += 1
def hermitian_matrix_with_power_of_2_eigenvalues(n):
    # Generate eigenvalues as inverse powers of 2.
    eigenvalues = 1 / np.exp2(np.random.randint(1, 4, size=n))

    # Generate a random unitary matrix.
    Q, _ = np.linalg.qr(np.random.randn(n, n))

    # Construct the Hermitian matrix.
    A = Q @ np.diag(eigenvalues) @ Q.conj().T

    return A


# Example
n = 3
A = hermitian_matrix_with_power_of_2_eigenvalues(2**n)

H = QubitOperator.from_matrix(A).to_pauli()


def U(qf):
    H.trotterization()(qf, t=-np.pi, steps=5)


b = np.random.randint(0, 2, size=2**n)

print("Hermitian matrix A:")
print(A)

print("Eigenvalues:")
print(np.linalg.eigvals(A))

print("b:")
print(b)
_current_cell[0] += 1
@terminal_sampling
def main():

    x = HHL(tuple(b), U, n, 4)
    return x


res_dict = main()

for k, v in res_dict.items():
    res_dict[k] = v**0.5

np.array([res_dict[key] for key in sorted(res_dict)])
_current_cell[0] += 1
x = (np.linalg.inv(A) @ b) / np.linalg.norm(np.linalg.inv(A) @ b)
print(x)
_current_cell[0] += 1
def main():
    x = HHL(tuple(b), U, n, 4)
    # Note that we have to return a classical value
    # (in this case the measurement result of the
    # quantum variable returned by the HHL algorithm)
    # Within the above examples, we used the terminal_sampling
    # decorator, which is a convenience feature and allows
    # a much faster sampling procedure.
    # The terminal_sampling decorator expects a function returning
    # quantum variables, while most other evaluation modes require
    # classical return values.
    return measure(x)


jaspr = make_jaspr(main)()
qir_str = jaspr.to_qir()
# Print only the first few lines - the whole string is very long.
print(qir_str[:2000])
_current_cell[0] += 1
A = np.array([[3 / 8, 1 / 8], [1 / 8, 3 / 8]])

b = np.array([1, 1])

H = QubitOperator.from_matrix(A).to_pauli()


# By default e^{-itH} is performed. Therefore, we set t=-pi.
def U(qf):
    H.trotterization()(qf, t=-np.pi, steps=1)


@qjit
def main():
    x = HHL(tuple(b), U, 1, 3)

    return measure(x)


samples = []
for i in range(5):
    samples.append(float(main()))

print(samples)# ── end of notebook cells ─────────────────────────────────────────────────
_trace_sys.settrace(None)
with open(_TRACE_OUTPUT, 'w', encoding='utf-8') as _f:
    _trace_json.dump(_call_log, _f)

_TRACE_OUTPUT = '/Users/I763567/projects/qpa-v2/experiments/results/qrisp_trace/Shor_raw_calls.json'
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

N = 13
qg = QuantumModulus(N)
qg[:] = 8
_current_cell[0] += 1
qg += 8
print(qg)
_current_cell[0] += 1
print(qg.qs)
_current_cell[0] += 1
N = 99
a = 10
qg = QuantumModulus(N)
qg[:] = 1
_current_cell[0] += 1
n = qg.size
qpe_res = QuantumFloat(2 * n + 1, exponent=-(2 * n + 1))
h(qpe_res)
_current_cell[0] += 1
x = a
for i in range(len(qpe_res)):
    with control(qpe_res[i]):
        qg *= x
    x = (x * x) % N
_current_cell[0] += 1
QFT(qpe_res, inv=True)
meas_res = qpe_res.get_measurement()
print(meas_res)
_current_cell[0] += 1
from sympy import continued_fraction_convergents, continued_fraction_iterator, Rational


def get_r_candidates(approx):
    rationals = continued_fraction_convergents(
        continued_fraction_iterator(Rational(approx))
    )
    return [rat.q for rat in rationals]
_current_cell[0] += 1
r_candidates = sum([get_r_candidates(approx) for approx in meas_res.keys()], [])
_current_cell[0] += 1
for cand in r_candidates:
    if (a**cand) % N == 1:
        r = cand
        break
else:
    raise Exception("Please sample again")

if r % 2:
    raise Exception("Please choose another a")
_current_cell[0] += 1
import numpy as np

g = np.gcd(a ** (r // 2) + 1, N)
print(g)
_current_cell[0] += 1
def find_order(a, N):
    qg = QuantumModulus(N)
    qg[:] = 1
    qpe_res = QuantumFloat(2 * qg.size + 1, exponent=-(2 * qg.size + 1))
    h(qpe_res)
    for i in range(len(qpe_res)):
        with control(qpe_res[i]):
            qg *= a
            a = (a * a) % N
    QFT(qpe_res, inv=True)
    return qpe_res.get_measurement()# ── end of notebook cells ─────────────────────────────────────────────────
_trace_sys.settrace(None)
with open(_TRACE_OUTPUT, 'w', encoding='utf-8') as _f:
    _trace_json.dump(_call_log, _f)

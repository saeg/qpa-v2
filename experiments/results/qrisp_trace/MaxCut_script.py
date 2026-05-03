_TRACE_OUTPUT = '/Users/I763567/projects/qpa-v2/experiments/results/qrisp_trace/MaxCut_raw_calls.json'
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
from qrisp import QuantumVariable, h, barrier, rz, rx, cx
import networkx as nx
from sympy import Symbol

G = nx.Graph()
G.add_edges_from([[0, 3], [0, 4], [1, 3], [1, 4], [2, 3], [2, 4]])
# nx.draw(G, with_labels=True)
N = G.number_of_nodes()
_current_cell[0] += 1
gamma = Symbol("γ")


def apply_cost_operator(qv, gamma):
    for pair in list(G.edges()):
        cx(qv[pair[0]], qv[pair[1]])
        rz(2 * gamma, qv[pair[1]])
        cx(qv[pair[0]], qv[pair[1]])
        barrier(qv)
    return qv
_current_cell[0] += 1
beta = Symbol("β")


def apply_mixer(qv, beta):
    for i in range(0, N):
        rx(2 * beta, qv[i])
    barrier(qv)
    return qv
_current_cell[0] += 1
qv_1 = QuantumVariable(N)
h(qv_1)
apply_cost_operator(qv_1, gamma)
apply_mixer(qv_1, beta)
print(qv_1.qs)
_current_cell[0] += 1
def maxcut_obj(x):
    cut = 0
    for i, j in G.edges():
        if x[i] != x[j]:
            cut -= 1
    return cut
_current_cell[0] += 1
def maxcut_cost_funct(meas_res):
    energy = 0
    for meas, p in meas_res.items():
        obj_for_meas = maxcut_obj(meas)
        energy += obj_for_meas * p
    return energy
_current_cell[0] += 1
p = 3


def apply_p_layers(qv, beta, gamma):
    assert len(beta) == len(gamma)
    p = len(beta)
    h(qv)
    for i in range(p):
        apply_cost_operator(qv, gamma[i])
        apply_mixer(qv, beta[i])
    barrier(qv)
    return qv
_current_cell[0] += 1
def quantum_objective(theta):
    qv_p = QuantumVariable(N)
    beta = theta[:p]
    gamma = theta[p:]
    qv = apply_p_layers(qv_p, beta, gamma)
    results = qv.get_measurement()
    return maxcut_cost_funct(results)
_current_cell[0] += 1
import numpy as np
from scipy.optimize import minimize
from operator import itemgetter

init_point = np.pi * np.random.rand(2 * p)

res_sample = minimize(
    quantum_objective, init_point, method="COBYLA", options={"maxiter": 50}
)

optimal_theta = res_sample["x"]
qv_p = QuantumVariable(N)
qv = apply_p_layers(qv_p, optimal_theta[:p], optimal_theta[p:])
results = qv_p.get_measurement()

best_cut, best_solution = min(
    [(maxcut_obj(x), x) for x in results.keys()], key=itemgetter(0)
)
print(f"Best string: {best_solution} with cut: {-best_cut}")

colors = ["r" if best_solution[node] == "0" else "b" for node in G]
nx.draw(
    G,
    with_labels=True,
    font_color="white",
    node_size=1000,
    font_size=22,
    node_color=colors,
    pos=nx.bipartite_layout(G, [node for node in G if best_solution[node] == "0"]),
)
_current_cell[0] += 1
qarg = QuantumVariable(len(G))

depth = 3
_current_cell[0] += 1
from qrisp.qaoa import QAOAProblem, RX_mixer

maxcut_instance = QAOAProblem(apply_cost_operator, RX_mixer, maxcut_cost_funct)

res = maxcut_instance.run(qarg, depth, max_iter=50)  # runs the simulation
_current_cell[0] += 1
best_cut, best_solution = min(
    [(maxcut_obj(x), x) for x in res.keys()], key=itemgetter(0)
)
print(f"Best string: {best_solution} with cut: {-best_cut}")

res_str = list(res.keys())[0]
print("QAOA solution: ", res_str)
best_cut, best_solution = (maxcut_obj(res_str), res_str)

"""
colors = ["r" if best_solution[node] == "0" else "b" for node in G]
nx.draw(
    G,
    with_labels=True,
    font_color="white",
    node_size=1000,
    font_size=22,
    node_color=colors,
    pos=nx.bipartite_layout(G, [node for node in G if best_solution[node] == "0"]),
)
"""
_current_cell[0] += 1
print("RND")

benchmark_data = maxcut_instance.benchmark(
    qarg=QuantumVariable(len(G)),
    depth_range=[1, 2, 3, 4, 5],
    shot_range=[1000, 10000],
    iter_range=[100, 200],
    optimal_solution="00011",
    repetitions=1,
    init_type="random",
)

temp = benchmark_data.rank(print_res=True)

_, rndFO = benchmark_data.evaluate()

print("Approximation ratio: ", sum(rndFO) / len(rndFO))
print("Variance: ", np.var(rndFO))
_current_cell[0] += 1
print("TQA")

benchmark_data = maxcut_instance.benchmark(
    qarg=QuantumVariable(len(G)),
    depth_range=[1, 2, 3, 4, 5],
    shot_range=[1000, 10000],
    iter_range=[100, 200],
    optimal_solution="00011",
    repetitions=1,
    init_type="tqa",
)

temp = benchmark_data.rank(print_res=True)

_, tqaFO = benchmark_data.evaluate()

print("Approximation ratio: ", sum(tqaFO) / len(tqaFO))
print("Variance: ", np.var(tqaFO))
_current_cell[0] += 1
from qrisp import QuantumArray, QuantumVariable
from qrisp.qaoa import (
    QAOAProblem,
    maxcut_obj,
    create_maxcut_cl_cost_function,
    create_maxcut_cost_operator,
    RX_mixer,
)
import networkx as nx
from operator import itemgetter

G = nx.Graph()
G.add_edges_from([[0, 3], [0, 4], [1, 3], [1, 4], [2, 3], [2, 4]])

qarg = QuantumVariable(len(G))

depth = 5

maxcut_instance = QAOAProblem(
    create_maxcut_cost_operator(G), RX_mixer, create_maxcut_cl_cost_function(G)
)

res = maxcut_instance.run(qarg, depth, max_iter=50)

best_cut, best_solution = min(
    [(maxcut_obj(x, G), x) for x in res.keys()], key=itemgetter(0)
)

res_str = list(res.keys())[0]
print("QAOA solution: ", res_str)
best_cut, best_solution = (maxcut_obj(res_str, G), res_str)

"""
colors = ["r" if best_solution[node] == "0" else "b" for node in G]
nx.draw(
    G,
    with_labels=True,
    font_color="white",
    node_size=1000,
    font_size=22,
    node_color=colors,
    pos=nx.bipartite_layout(G, [node for node in G if best_solution[node] == "0"]),
)
"""# ── end of notebook cells ─────────────────────────────────────────────────
_trace_sys.settrace(None)
with open(_TRACE_OUTPUT, 'w', encoding='utf-8') as _f:
    _trace_json.dump(_call_log, _f)

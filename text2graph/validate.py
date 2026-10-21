"""Checks a Graph before anything is built in Houdini.

Returns a list of human-readable problems; an empty list means the graph is
safe to build. The same checks apply whether the graph came from the
rule-based parser, a language model or a hand-written JSON file.
"""

from __future__ import annotations

from numbers import Number

from .registry import REGISTRY
from .spec import Graph


def _check_value(value, size: int) -> bool:
    if size == 1:
        return isinstance(value, Number) and not isinstance(value, bool)
    return (isinstance(value, (list, tuple)) and len(value) == size
            and all(isinstance(v, Number) and not isinstance(v, bool) for v in value))


def validate(graph: Graph) -> list:
    problems = []
    names = [n.name for n in graph.nodes]

    if not graph.nodes:
        return ["the graph has no nodes"]
    if len(names) != len(set(names)):
        problems.append("node names are not unique")
    if graph.output not in names:
        problems.append(f"output node '{graph.output}' does not exist")

    for node in graph.nodes:
        spec = REGISTRY.get(node.type)
        if spec is None:
            problems.append(f"{node.name}: unknown node type '{node.type}'")
            continue
        n_inputs = len(node.inputs)
        if n_inputs < spec.min_inputs or (spec.max_inputs != -1 and n_inputs > spec.max_inputs):
            problems.append(f"{node.name}: has {n_inputs} inputs, "
                            f"needs {spec.min_inputs} to "
                            f"{'any number' if spec.max_inputs == -1 else spec.max_inputs}")
        for upstream in node.inputs:
            if upstream not in names:
                problems.append(f"{node.name}: input '{upstream}' does not exist")
        for parm, value in node.parms.items():
            pspec = spec.parms.get(parm)
            if pspec is None:
                problems.append(f"{node.name}: '{node.type}' has no parameter '{parm}'")
            elif not _check_value(value, pspec.size):
                problems.append(f"{node.name}: parameter '{parm}' needs "
                                f"{pspec.size} number(s), got {value!r}")

    problems.extend(_find_cycles(graph))
    return problems


def _find_cycles(graph: Graph) -> list:
    inputs = {n.name: list(n.inputs) for n in graph.nodes}
    state = {}  # name -> "visiting" | "done"

    def visit(name, path):
        if state.get(name) == "done" or name not in inputs:
            return None
        if state.get(name) == "visiting":
            return path + [name]
        state[name] = "visiting"
        for upstream in inputs[name]:
            cycle = visit(upstream, path + [name])
            if cycle:
                return cycle
        state[name] = "done"
        return None

    for name in inputs:
        cycle = visit(name, [])
        if cycle:
            return ["cycle: " + " -> ".join(cycle)]
    return []

"""Builds a validated Graph as native nodes inside Houdini.

Only this module needs Houdini. It is passed the `hou` module explicitly so
that the tests can use a stand-in; inside Houdini call build(graph) and it
imports `hou` itself.

Parameters that a Houdini version does not have are skipped and reported,
rather than stopping the build, so the artist still gets an editable network.
"""

from __future__ import annotations

from .registry import REGISTRY
from .spec import Graph
from .validate import validate


def _create(hou, parent, node_type: str, fallbacks, name: str):
    for type_name in (node_type, *fallbacks):
        try:
            return parent.createNode(type_name, name)
        except hou.OperationFailed:
            continue
    raise ValueError(f"Houdini could not create a '{node_type}' node")


def build(graph: Graph, parent_path: str = "/obj", geo_name: str = "text2graph", hou=None):
    """Create the network; return (geo_node, warnings)."""
    if hou is None:
        import hou  # noqa: F811  (only available inside Houdini)

    problems = validate(graph)
    if problems:
        raise ValueError("graph is not valid:\n  " + "\n  ".join(problems))

    geo = hou.node(parent_path).createNode("geo", geo_name)
    created, warnings = {}, []

    for node in graph.nodes:
        spec = REGISTRY[node.type]
        hnode = _create(hou, geo, spec.houdini_type, spec.fallbacks, node.name)
        created[node.name] = hnode
        if node.source:
            hnode.setComment(node.source)  # keeps the link back to the description
        for parm, value in node.parms.items():
            pspec = spec.parms[parm]
            target = hnode.parmTuple(pspec.houdini_name) if pspec.size > 1 \
                else hnode.parm(pspec.houdini_name)
            if target is None:
                warnings.append(f"{node.name}: this Houdini version has no "
                                f"'{pspec.houdini_name}' parameter; left at default")
                continue
            target.set(tuple(value) if pspec.size > 1 else value)

    for node in graph.nodes:
        for index, upstream in enumerate(node.inputs):
            created[node.name].setInput(index, created[upstream])

    out = created[graph.output]
    out.setDisplayFlag(True)
    out.setRenderFlag(True)
    geo.layoutChildren()
    return geo, warnings

import pytest

from fake_hou import FakeHou
from text2graph import Graph, Node, parse, validate
from text2graph.houdini_build import build


def test_validator_catches_hand_written_mistakes():
    g = Graph(nodes=[
        Node("g", "grid", {"size": [1.0]}),           # wrong tuple size
        Node("s", "scatter", {"density": 3}, []),      # unknown parm, missing input
        Node("x", "teapot", {}, ["g"]),                # unknown type
        Node("c", "copytopoints", {}, ["g", "ghost"]),  # missing upstream node
    ], output="OUT")
    problems = validate(g)
    assert "output node 'OUT' does not exist" in problems
    assert any("needs 2 number(s)" in p for p in problems)
    assert any("no parameter 'density'" in p for p in problems)
    assert any("has 0 inputs" in p for p in problems)
    assert any("unknown node type 'teapot'" in p for p in problems)
    assert any("input 'ghost' does not exist" in p for p in problems)


def test_validator_catches_cycles():
    g = Graph(nodes=[Node("a", "null", {}, ["b"]), Node("b", "null", {}, ["a"])], output="a")
    assert any(p.startswith("cycle:") for p in validate(g))


def test_json_round_trip():
    g = parse("a grid 2 by 2, scatter 5 points")
    assert Graph.from_json(g.to_json()) == g


def test_build_creates_wires_and_flags_nodes():
    hou = FakeHou()
    g = parse("a grid 10 by 10, scatter 200 points, copy spheres of radius 0.1 onto the points")
    geo, warnings = build(g, hou=hou)
    assert warnings == []
    nodes = geo.children
    assert set(nodes) == {"grid1", "scatter1", "sphere1", "copytopoints1", "OUT"}
    assert nodes["grid1"].parmTuple("size").value == (10.0, 10.0)
    assert nodes["scatter1"].parm("npts").value == 200
    assert nodes["copytopoints1"].inputs == {0: nodes["sphere1"], 1: nodes["scatter1"]}
    assert nodes["OUT"].display and nodes["OUT"].render and geo.laid_out
    assert nodes["scatter1"].comment == "scatter 200 points"


def test_build_uses_versioned_fallback_and_reports_missing_parms():
    # this "Houdini" only knows the versioned scatter, and its grid lacks 'rows'
    hou = FakeHou(creatable={"geo": (), "grid": ("size",), "scatter::2.0": ("npts",), "null": ()})
    g = parse("a grid 4 by 4 with 8 rows, scatter 10 points")
    geo, warnings = build(g, hou=hou)
    assert geo.children["scatter1"].type_name == "scatter::2.0"
    assert warnings == ["grid1: this Houdini version has no 'rows' parameter; left at default"]


def test_build_refuses_invalid_graph():
    with pytest.raises(ValueError, match="graph is not valid"):
        build(Graph(), hou=FakeHou())

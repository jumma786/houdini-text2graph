from text2graph import parse, validate


def types(graph):
    return [n.type for n in graph.nodes]


def test_scatter_and_copy_chain():
    g = parse("a grid 10 by 10, scatter 200 points, copy spheres of radius 0.1 onto the points")
    assert types(g) == ["grid", "scatter", "sphere", "copytopoints", "null"]
    assert g.get("grid1").parms == {"size": [10.0, 10.0]}
    assert g.get("scatter1").parms == {"count": 200}
    assert g.get("sphere1").parms == {"radius": [0.1, 0.1, 0.1]}
    # copy to points: shape in input 0, target points in input 1
    assert g.get("copytopoints1").inputs == ["sphere1", "scatter1"]
    assert g.output == "OUT" and g.get("OUT").inputs == ["copytopoints1"]
    assert validate(g) == []


def test_terrain_with_transform():
    g = parse("make a grid 50 by 50 with 100 rows and 100 columns, "
              "add mountain noise with height 3, then move it up 2")
    assert types(g) == ["grid", "mountain", "xform", "null"]
    assert g.get("grid1").parms == {"size": [50.0, 50.0], "rows": 100, "cols": 100}
    assert g.get("mountain1").parms == {"height": 3.0}
    assert g.get("xform1").parms == {"translate": [0.0, 2.0, 0.0]}
    assert validate(g) == []


def test_and_splits_only_before_a_new_action():
    g = parse("a box size 2 and extrude it by 0.5 and subdivide it 2 times")
    assert types(g) == ["box", "polyextrude", "subdivide", "null"]
    assert g.get("box1").parms == {"size": [2.0, 2.0, 2.0]}
    assert g.get("polyextrude1").parms == {"distance": 0.5}
    assert g.get("subdivide1").parms == {"iterations": 2}


def test_rotation_axis_and_scale():
    g = parse("a box, rotate 45 degrees around x, scale by 2")
    assert g.get("xform1").parms == {"rotate": [45.0, 0.0, 0.0]}
    assert g.get("xform2").parms == {"uniform_scale": 2.0}


def test_second_shape_is_merged_not_lost():
    g = parse("a sphere of radius 1, a box size 3")
    assert types(g) == ["sphere", "box", "merge", "null"]
    assert g.get("merge1").inputs == ["sphere1", "box1"]
    assert validate(g) == []


def test_every_node_records_where_it_came_from():
    g = parse("a grid 4 by 4, scatter 10 points")
    assert g.get("grid1").source == "a grid 4 by 4"
    assert g.get("scatter1").source == "scatter 10 points"


def test_unknown_words_are_reported_not_dropped():
    g = parse("a grid 4 by 4, make it look like a castle")
    assert g.unparsed == ["make it look like a castle"]
    assert validate(g) == []


def test_nothing_understood_gives_invalid_graph():
    g = parse("something beautiful")
    assert g.nodes == []
    assert validate(g) == ["the graph has no nodes"]

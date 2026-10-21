"""The SOP node types the prototype knows about.

Each entry lists the Houdini node type name (plus fallbacks for versioned
names), how many inputs the node accepts, and the parameters the parser may
set, with the Houdini parameter name and how many values it takes.
Keeping this in one table means the parser, the validator and the builder
all agree on what is allowed.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParmSpec:
    houdini_name: str  # parm or parmTuple name in Houdini
    size: int = 1      # 1 = scalar, 2 or 3 = tuple


@dataclass(frozen=True)
class NodeSpec:
    houdini_type: str
    fallbacks: tuple = ()
    min_inputs: int = 0
    max_inputs: int = 0          # -1 means unlimited (merge)
    parms: dict = field(default_factory=dict)


REGISTRY = {
    # generators (no inputs)
    "grid": NodeSpec("grid", parms={"size": ParmSpec("size", 2),
                                    "rows": ParmSpec("rows"),
                                    "cols": ParmSpec("cols")}),
    "box": NodeSpec("box", parms={"size": ParmSpec("size", 3)}),
    "sphere": NodeSpec("sphere", parms={"radius": ParmSpec("rad", 3)}),
    "line": NodeSpec("line", parms={"length": ParmSpec("dist"),
                                    "points": ParmSpec("points")}),
    # modifiers (one input)
    "scatter": NodeSpec("scatter", ("scatter::2.0",), 1, 1,
                        {"count": ParmSpec("npts")}),
    "mountain": NodeSpec("mountain", ("mountain::2.0",), 1, 1,
                         {"height": ParmSpec("height")}),
    "polyextrude": NodeSpec("polyextrude", ("polyextrude::2.0",), 1, 1,
                            {"distance": ParmSpec("dist")}),
    "subdivide": NodeSpec("subdivide", (), 1, 1,
                          {"iterations": ParmSpec("iterations")}),
    "xform": NodeSpec("xform", (), 1, 1,
                      {"translate": ParmSpec("t", 3),
                       "rotate": ParmSpec("r", 3),
                       "uniform_scale": ParmSpec("scale")}),
    # combiners
    "copytopoints": NodeSpec("copytopoints", ("copytopoints::2.0",), 2, 2),
    "merge": NodeSpec("merge", (), 1, -1),
    "null": NodeSpec("null", (), 1, 1),
}

GENERATORS = ("grid", "box", "sphere", "line")

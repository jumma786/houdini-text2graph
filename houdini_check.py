r"""Check the prototype inside Houdini and write the results to houdini_check_results.txt.

Run from Houdini's Python Shell (Windows > Python Shell):
    exec(open(r"<this folder>\houdini_check.py").read())
"""
import sys
import traceback

import hou

LINES = []


def say(*parts):
    line = " ".join(str(p) for p in parts)
    LINES.append(line)
    print(line)


REPO = r"C:\Users\jumma\Downloads\PhD Applications\ABERTAY UNIVERSITY - R-LINCS2 Studentship\houdini-text2graph"
sys.path.insert(0, REPO)

from text2graph import parse, validate  # noqa: E402
from text2graph.houdini_build import build  # noqa: E402
from text2graph.registry import REGISTRY  # noqa: E402

say("Houdini", hou.applicationVersionString(), "|", hou.licenseCategory())

# 1. every registry type and parameter name against this Houdini version
geo = hou.node("/obj").createNode("geo", "registry_check")
for key, spec in REGISTRY.items():
    try:
        node = None
        for t in (spec.houdini_type,) + tuple(spec.fallbacks):
            try:
                node = geo.createNode(t)
                break
            except hou.OperationFailed:
                pass
        if node is None:
            say("TYPE MISSING:", key)
            continue
        missing = []
        for pname, p in spec.parms.items():
            target = node.parmTuple(p.houdini_name) if p.size > 1 else node.parm(p.houdini_name)
            if target is None:
                missing.append(p.houdini_name)
            elif p.size > 1 and len(target) != p.size:
                missing.append(f"{p.houdini_name} (has {len(target)} values, expected {p.size})")
        say(f"{key:13s} -> {node.type().name():22s} parms ok" if not missing
              else f"{key:13s} -> {node.type().name():22s} MISSING {missing}")
    except Exception:
        say(traceback.format_exc())
geo.destroy()

# 2. the example descriptions, built and cooked
examples = [
    "a grid 10 by 10, scatter 200 points, copy spheres of radius 0.1 onto the points",
    "a grid 50 by 50 with 100 rows and 100 columns, add mountain noise with height 3, then move it up 2",
    "a box size 2 and extrude it by 0.5 and subdivide it 2 times",
    "a sphere of radius 1, a box size 3",
]
for i, text in enumerate(examples, 1):
    say(f"\n[{i}] {text}")
    try:
        g = parse(text)
        problems = validate(g)
        if problems:
            say("  invalid:", problems)
            continue
        geo, warnings = build(g, geo_name=f"example{i}", hou=hou)
        out = geo.node("OUT")
        out.cook(force=True)
        errors = [n.name() + ": " + "; ".join(n.errors()) for n in geo.children() if n.errors()]
        geom = out.geometry()
        say("  built:", " ".join(f"{n.name()}({n.type().name()})" for n in geo.children()))
        say("  warnings:", warnings or "none", "| cook errors:", errors or "none")
        say(f"  OUT geometry: {len(geom.points())} points, {len(geom.prims())} primitives")
    except Exception:
        say(traceback.format_exc())

hou.hipFile.save(REPO + r"\examples_test.hipnc")
say("\nsaved examples_test.hipnc")
with open(REPO + r"\houdini_check_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(LINES))
if hou.isUIAvailable():
    hou.ui.displayMessage("text2graph check finished.\nResults saved to houdini_check_results.txt")

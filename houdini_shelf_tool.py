"""Paste into a Houdini shelf tool (or run in the Python Shell).

Asks for a description, shows what was understood, then builds the network
under /obj. Change REPO to the folder that contains the text2graph package.
"""

import sys

import hou

REPO = r"C:\path\to\houdini-text2graph"
if REPO not in sys.path:
    sys.path.append(REPO)

from text2graph import parse, validate  # noqa: E402
from text2graph.houdini_build import build  # noqa: E402

button, text = hou.ui.readInput(
    "Describe the network, for example:\n"
    "a grid 10 by 10, scatter 200 points, copy spheres of radius 0.1 onto the points",
    buttons=("Build", "Cancel"), title="text2graph")

if button == 0 and text.strip():
    graph = parse(text)
    problems = validate(graph)
    if problems:
        hou.ui.displayMessage("Could not build:\n" + "\n".join(problems))
    else:
        geo, warnings = build(graph, hou=hou)
        notes = []
        if graph.unparsed:
            notes.append("Not understood: " + "; ".join(graph.unparsed))
        notes.extend(warnings)
        hou.ui.displayMessage("Built " + geo.path() + ("\n\n" + "\n".join(notes) if notes else ""))

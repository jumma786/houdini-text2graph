"""Rule-based parser: plain English -> Graph.

The description is split into clauses ("a grid 10 by 10, scatter 200 points,
copy spheres of radius 0.1 onto the points"). Each clause becomes one or more
nodes, and every node keeps the clause it came from, so an artist can see why
it exists. Clauses the parser cannot use are kept in Graph.unparsed instead of
being silently dropped.

This is deliberately simple. It is the baseline that a learned model (for
example a language model that writes the same Graph format) would have to beat,
and its output goes through the same validator.
"""

from __future__ import annotations

import re

from .registry import GENERATORS
from .spec import Graph, Node

NUM = r"-?\d+(?:\.\d+)?"
SPLIT = re.compile(r"\s*(?:,|;|\band then\b|\bthen\b)\s*")
# "and" only starts a new clause when a new action follows it, so
# "20 rows and 20 columns" stays together but "scatter points and copy spheres" splits.
AND_ACTION = re.compile(r"\band\s+(?=(?:scatter|cop|add|make|create|extrud|subdivid|smooth|"
                        r"move|rotate|scale|merge|raise|lift|lower|translate)\w*\b)")

GENERATOR_WORDS = {
    "grid": "grid", "plane": "grid", "ground": "grid",
    "box": "box", "boxes": "box", "cube": "box", "cubes": "box",
    "sphere": "sphere", "spheres": "sphere", "ball": "sphere", "balls": "sphere",
    "line": "line", "lines": "line",
}


def _numbers(text: str) -> list:
    return [float(n) for n in re.findall(NUM, text)]


def _num_after(pattern: str, text: str):
    match = re.search(pattern + r"\s*(?:of\s*|=\s*)?(" + NUM + ")", text)
    return float(match.group(1)) if match else None


def _num_before(pattern: str, text: str):
    match = re.search("(" + NUM + r")\s*" + pattern, text)
    return float(match.group(1)) if match else None


def _generator_in(text: str):
    for word in re.findall(r"[a-z]+", text):
        if word in GENERATOR_WORDS:
            return GENERATOR_WORDS[word]
    return None


def _generator_parms(kind: str, text: str) -> dict:
    parms = {}
    dims = re.search("(" + NUM + r")\s*(?:by|x)\s*(" + NUM + r")(?:\s*(?:by|x)\s*(" + NUM + "))?", text)
    if kind == "grid":
        if dims:
            parms["size"] = [float(dims.group(1)), float(dims.group(2))]
        elif _num_after(r"size", text) is not None:
            s = _num_after(r"size", text)
            parms["size"] = [s, s]
        rows = _num_before(r"rows", text)
        cols = _num_before(r"(?:columns|cols)", text)
        if rows is not None:
            parms["rows"] = int(rows)
        if cols is not None:
            parms["cols"] = int(cols)
    elif kind == "box":
        if dims and dims.group(3):
            parms["size"] = [float(dims.group(i)) for i in (1, 2, 3)]
        else:
            s = _num_after(r"size", text)
            if s is not None:
                parms["size"] = [s, s, s]
    elif kind == "sphere":
        r = _num_after(r"radius", text)
        if r is not None:
            parms["radius"] = [r, r, r]
    elif kind == "line":
        length = _num_after(r"length", text)
        points = _num_before(r"points", text)
        if length is not None:
            parms["length"] = length
        if points is not None:
            parms["points"] = int(points)
    return parms


class _Builder:
    def __init__(self):
        self.graph = Graph()
        self.counts = {}
        self.current = None  # name of the last node on the main chain

    def add(self, kind: str, parms=None, inputs=None, source: str = "") -> str:
        self.counts[kind] = self.counts.get(kind, 0) + 1
        name = f"{kind}{self.counts[kind]}"
        self.graph.nodes.append(Node(name, kind, parms or {}, inputs or [], source))
        return name


def _transform_parms(text: str) -> dict:
    parms = {}
    amount = _numbers(text)
    if re.search(r"\b(move|raise|lift)\b.*\bup\b", text) and amount:
        parms["translate"] = [0.0, amount[0], 0.0]
    elif re.search(r"\b(move|lower)\b.*\bdown\b", text) and amount:
        parms["translate"] = [0.0, -amount[0], 0.0]
    elif re.search(r"\b(move|translate)\b", text) and len(amount) >= 3:
        parms["translate"] = amount[:3]
    if re.search(r"\brotate\b", text) and amount:
        axis = re.search(r"\b(?:around|about)\s+(?:the\s+)?([xyz])\b", text)
        index = "xyz".index(axis.group(1)) if axis else 1
        rotation = [0.0, 0.0, 0.0]
        rotation[index] = amount[0]
        parms["rotate"] = rotation
    if re.search(r"\bscale\b", text) and amount:
        parms["uniform_scale"] = amount[0]
    return parms


def parse(text: str) -> Graph:
    b = _Builder()
    text = AND_ACTION.sub(", ", text.strip().lower())
    clauses = [c for c in SPLIT.split(text) if c and c.strip(" .")]

    for raw in clauses:
        clause = raw.strip(" .")
        kind = _generator_in(clause)

        if re.search(r"\bcop(?:y|ies)\b", clause) and b.current:
            if kind is None:
                b.graph.unparsed.append(raw)
                continue
            shape = b.add(kind, _generator_parms(kind, clause), source=clause)
            b.current = b.add("copytopoints", inputs=[shape, b.current], source=clause)

        elif re.search(r"\bscatter\b", clause) and b.current:
            count = _num_before(r"points?", clause)
            if count is None and _numbers(clause):
                count = _numbers(clause)[0]
            parms = {"count": int(count)} if count is not None else {}
            b.current = b.add("scatter", parms, [b.current], clause)

        elif re.search(r"\b(mountain|noise|noisy|bumpy|terrain|hills?)\b", clause) and b.current:
            height = _num_after(r"height", clause) or _num_after(r"by", clause)
            parms = {"height": height} if height is not None else {}
            b.current = b.add("mountain", parms, [b.current], clause)

        elif re.search(r"\bextrud", clause) and b.current:
            dist = _num_after(r"by", clause)
            if dist is None and _numbers(clause):
                dist = _numbers(clause)[0]
            parms = {"distance": dist} if dist is not None else {}
            b.current = b.add("polyextrude", parms, [b.current], clause)

        elif re.search(r"\b(subdivide|smooth)", clause) and b.current:
            times = _num_before(r"(?:times|iterations|levels)", clause)
            parms = {"iterations": int(times)} if times is not None else {}
            b.current = b.add("subdivide", parms, [b.current], clause)

        elif re.search(r"\b(move|translate|raise|lift|lower|rotate|scale)\b", clause) and b.current:
            parms = _transform_parms(clause)
            if not parms:
                b.graph.unparsed.append(raw)
                continue
            b.current = b.add("xform", parms, [b.current], clause)

        elif re.search(r"\bmerge\b", clause) and b.current and kind:
            other = b.add(kind, _generator_parms(kind, clause), source=clause)
            b.current = b.add("merge", inputs=[b.current, other], source=clause)

        elif kind in GENERATORS:
            node = b.add(kind, _generator_parms(kind, clause), source=clause)
            if b.current:  # a second shape: keep both by merging
                node = b.add("merge", inputs=[b.current, node],
                             source=f"implicit merge: {clause}")
            b.current = node

        else:
            b.graph.unparsed.append(raw)

    if b.current:
        b.graph.nodes.append(Node("OUT", "null", {}, [b.current], "output"))
        b.graph.output = "OUT"
    return b.graph

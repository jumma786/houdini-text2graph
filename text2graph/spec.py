"""A plain, Houdini-independent description of a node network."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class Node:
    name: str
    type: str                                    # key in registry.REGISTRY
    parms: dict = field(default_factory=dict)    # registry parm name -> value(s)
    inputs: list = field(default_factory=list)   # names of upstream nodes, in input order
    source: str = ""                             # the words this node came from


@dataclass
class Graph:
    nodes: list = field(default_factory=list)
    output: str = ""                             # node that gets the display flag
    unparsed: list = field(default_factory=list)  # clauses the parser could not use

    def get(self, name: str):
        for node in self.nodes:
            if node.name == name:
                return node
        return None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Graph":
        data = json.loads(text)
        nodes = [Node(**n) for n in data.get("nodes", [])]
        return cls(nodes=nodes, output=data.get("output", ""),
                   unparsed=data.get("unparsed", []))

"""Turn a plain-English description into an editable Houdini SOP network.

The pipeline has three separate, testable steps:

    parse(text)      -> Graph   (rule-based; every node records the words it came from)
    validate(graph)  -> list of problems (empty list means the graph can be built)
    build(graph)     -> native Houdini nodes (only this step needs Houdini)
"""

from .spec import Graph, Node
from .parser import parse
from .validate import validate

__all__ = ["Graph", "Node", "parse", "validate"]

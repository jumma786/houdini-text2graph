"""Command line: python -m text2graph "a grid 10 by 10, scatter 200 points, ..."

Prints the parsed graph as JSON and any validation problems. Needs no Houdini.
"""

import sys

from .parser import parse
from .validate import validate


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    graph = parse(" ".join(argv))
    print(graph.to_json())
    problems = validate(graph)
    if graph.unparsed:
        print("\nNot understood (ignored):", *graph.unparsed, sep="\n  ")
    if problems:
        print("\nProblems:", *problems, sep="\n  ")
        return 1
    print("\nValid: ready to build in Houdini.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

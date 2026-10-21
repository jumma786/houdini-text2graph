# houdini-text2graph

A small prototype that turns a plain-English description into an **editable, native Houdini SOP network**.

```
"a grid 10 by 10, scatter 200 points, copy spheres of radius 0.1 onto the points"
        │ parse                      │ validate                     │ build (inside Houdini)
        ▼                            ▼                              ▼
   Graph (JSON)  ──────────►  list of problems  ──────────►  grid1 → scatter1 → copytopoints1 → OUT
                                                                     sphere1 ┘
```

The point is not to replace the artist. The output is an ordinary node network with normal
parameters that a technical artist can inspect and change, and every node keeps the words it came
from in its comment.

## Design

| Step | File | Needs Houdini? |
|---|---|---|
| **Parse** text into a `Graph` (nodes, parameters, inputs, source words) | `text2graph/parser.py` | No |
| **Validate** the graph: known node types and parameters, value shapes, input counts, missing nodes, cycles | `text2graph/validate.py` | No |
| **Build** native nodes under `/obj`, set parameters, wire inputs, set display/render flags, lay out | `text2graph/houdini_build.py` | Yes |

All three steps share one table of allowed node types and parameters (`text2graph/registry.py`).

Two choices matter for the research project this prototype was written for:

1. **The graph format is separate from the parser.** The rule-based parser is a baseline. A language
   model could write the same `Graph` JSON, and its output would go through exactly the same validator
   before anything touches Houdini. That makes it possible to measure, not just show, how often a
   generated network is valid and how close it is to what was asked for.
2. **Nothing is silently dropped.** Words the parser cannot use are listed in `Graph.unparsed`, and
   parameters a Houdini version does not have are reported as warnings while the rest of the network
   is still built.

Supported so far: grid, box, sphere and line; scatter, mountain (noise), poly extrude, subdivide,
transform (move, rotate, scale); copy to points, merge, and a null `OUT` node.

## Try it without Houdini

```bash
python -m text2graph "a grid 20 by 20, add mountain noise with height 2, scatter 300 points and copy boxes size 0.2 onto the points"
python -m pytest -q
```

The tests (14) cover the parser, the validator, JSON round-trips, and the builder against a small
stand-in for Houdini's `hou` module, including versioned node-type fallbacks and missing parameters.

## Run it in Houdini

1. Install Houdini Apprentice (free, non-commercial).
2. Open `houdini_shelf_tool.py`, set `REPO` to this folder, and paste it into a new shelf tool
   (or run it in **Windows → Python Shell**).
3. Click the tool, type a description, and press **Build**. A `text2graph` geometry node appears
   under `/obj`.

## Limits (honest status)

- **Not yet run inside Houdini.** The builder is tested only against a stand-in `hou` module. Node
  and parameter names (`npts`, `rad`, `dist`, `height`, `t`/`r`/`scale`, ...) come from Houdini's
  documentation and must be checked in a real Houdini session; the builder already tries versioned
  type names (for example `scatter::2.0`) and reports missing parameters instead of failing.
- The parser is rule-based and only understands the small vocabulary above.
- There is no evaluation with technical artists yet.

## Next steps

- Verify every node type and parameter in Houdini Apprentice and record the version.
- Add a language-model backend that writes the `Graph` JSON, and compare it with the rule-based
  baseline on a fixed set of descriptions: validity rate, node-type accuracy, parameter error.
- Expose "artistic controls": promote the key parameters (counts, sizes, heights) to the top-level
  geometry node so an artist can tune the result without opening the network.

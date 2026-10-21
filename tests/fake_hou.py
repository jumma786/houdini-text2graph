"""A small stand-in for Houdini's `hou` module, enough to test the builder."""


class OperationFailed(Exception):
    pass


class FakeParm:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value


class FakeNode:
    def __init__(self, type_name, name, known_parms=(), creatable=None):
        self.type_name = type_name
        self.name = name
        self.children = {}
        self.inputs = {}
        self.comment = ""
        self.display = self.render = self.laid_out = False
        self._parms = {p: FakeParm() for p in known_parms}
        self._creatable = creatable

    # creation -------------------------------------------------------------
    def createNode(self, type_name, name=None):
        if self._creatable is not None and type_name not in self._creatable:
            raise OperationFailed(type_name)
        parms = (self._creatable or {}).get(type_name, KNOWN_PARMS.get(type_name, ()))
        child = FakeNode(type_name, name or type_name, parms, creatable=self._creatable)
        self.children[child.name] = child
        return child

    # parameters ------------------------------------------------------------
    def parm(self, name):
        return self._parms.get(name)

    def parmTuple(self, name):
        return self._parms.get(name)

    # wiring and flags --------------------------------------------------------
    def setInput(self, index, node):
        self.inputs[index] = node

    def setComment(self, text):
        self.comment = text

    def setDisplayFlag(self, on):
        self.display = on

    def setRenderFlag(self, on):
        self.render = on

    def layoutChildren(self):
        self.laid_out = True

    def path(self):
        return "/obj/" + self.name


KNOWN_PARMS = {
    "grid": ("size", "rows", "cols"), "box": ("size",), "sphere": ("rad",),
    "line": ("dist", "points"), "scatter": ("npts",), "mountain": ("height",),
    "polyextrude": ("dist",), "subdivide": ("iterations",),
    "xform": ("t", "r", "scale"), "copytopoints": (), "merge": (), "null": (),
    "geo": (),
}


class FakeHou:
    OperationFailed = OperationFailed

    def __init__(self, creatable=None):
        self.obj = FakeNode("objnet", "obj", creatable=creatable)

    def node(self, path):
        assert path == "/obj"
        return self.obj

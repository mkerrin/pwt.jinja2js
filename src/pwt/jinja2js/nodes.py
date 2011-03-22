import jinja2.nodes

# Copied from jinja2.nodes.NodeType.__new__ so that we can create node types
def __new__(cls, name, bases, d):
    for attr in 'fields', 'attributes':
        storage = []
        storage.extend(getattr(bases[0], attr, ()))
        storage.extend(d.get(attr, ()))
        assert len(bases) == 1, 'multiple inheritance not allowed'
        assert len(storage) == len(set(storage)), 'layout conflict'
        d[attr] = tuple(storage)
    d.setdefault('abstract', False)
    return type.__new__(cls, name, bases, d)

# This is the old failing_new test so that jinja2 can catch protential errors.
_failing_new = jinja2.nodes.NodeType.__new__

jinja2.nodes.NodeType.__new__ = staticmethod(__new__)

class NamespaceNode(jinja2.nodes.Stmt):
    fields = ("namespace",)

# Re-install the failing_new method
jinja2.nodes.NodeType.__new__ = _failing_new
del __new__

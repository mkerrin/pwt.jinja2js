from jscompiler import register_filter

@register_filter("default")
def filter_default(generator, node, frame, default_value = ""):
    generator.visit(node.node, frame)
    generator.write(" ? ")
    generator.visit(node.node, frame)
    generator.write(" : ")
    generator.visit(default_value, frame)


@register_filter("truncate")
def filter_truncate(generator, node, frame, length):
    generator.visit(node.node, frame)
    generator.write(".substring(0, ")
    generator.visit(length, frame)
    generator.write(")")


@register_filter("capitalize")
def filter_capitalize(generator, node, frame):
    generator.visit(node.node, frame)
    generator.write(".substring(0, 1).toUpperCase(), ")
    generator.visit(node.node, frame)
    generator.write(".substring(1)")


@register_filter("last")
def filter_last(generator, node, frame):
    generator.visit(node.node, frame)
    generator.write(".pop()")


@register_filter("length")
def filter_length(generator, node, frame):
    generator.visit(node.node, frame)
    generator.write(".length")


@register_filter("replace")
def filter_replace(generator, node, frame, old, new): #, count = None)
    generator.visit(node.node, frame)
    generator.write(".replace(")
    generator.visit(old, frame)
    generator.write(", ")
    generator.visit(new, frame)
    generator.write(")")

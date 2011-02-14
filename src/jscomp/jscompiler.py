from cStringIO import StringIO

from jinja2.visitor import NodeVisitor
import jinja2.nodes
import jinja2.compiler
from jinja2.utils import Markup, concat, escape, is_python_keyword, next

def generate(node, environment, name, filename, stream = None):
    """Generate the python source for a node tree."""
    if not isinstance(node, jinja2.nodes.Template):
        raise TypeError("Can't compile non template nodes")
    generator = CodeGenerator(environment, name, filename, stream)
    generator.visit(node)
    if stream is None:
        return generator.stream.getvalue()


class CodeGenerator(NodeVisitor):

    def __init__(self, environment, name, filename, stream = None):
        super(CodeGenerator, self).__init__()

        if stream is None:
            stream = StringIO()

        self.environment = environment
        self.name = name
        self.filename = filename
        self.stream = stream

        # the current line number
        self.code_lineno = 1

        # the debug information
        self.debug_info = []
        self._write_debug_info = None

        # the number of new lines before the next write()
        self._new_lines = 0

        # true if nothing was written so far.
        self._first_write = True

        # the current indentation
        self._indentation = 0

    # Copied
    def indent(self):
        """Indent by one."""
        self._indentation += 1

    # Copied
    def outdent(self, step=1):
        """Outdent by step."""
        self._indentation -= step

    # Copied
    def write(self, x):
        """Write a string into the output stream."""
        if self._new_lines:
            if not self._first_write:
                self.stream.write('\n' * self._new_lines)
                self.code_lineno += self._new_lines
                if self._write_debug_info is not None:
                    self.debug_info.append((self._write_debug_info,
                                            self.code_lineno))
                    self._write_debug_info = None
            self._first_write = False
            self.stream.write('    ' * self._indentation)
            self._new_lines = 0
        self.stream.write(x)

    # Copied
    def writeline(self, x, node=None, extra=0):
        """Combination of newline and write."""
        self.newline(node, extra)
        self.write(x)

    # Copied
    def newline(self, node=None, extra=0):
        """Add one or more newlines before the next write."""
        self._new_lines = max(self._new_lines, 1 + extra)
        if node is not None and node.lineno != self._last_line:
            self._write_debug_info = node.lineno
            self._last_line = node.lineno

    def visit_Template(self, node, frame = None):
        """
        Setup the template output.

        Includes imports, macro definitions, etc.
        """
        assert frame is None, "no root frame allowed"

        have_extends = node.find(jinja2.nodes.Extends) is not None
        if have_extends:
            raise ValueError("JSCompiler doesn't support extends")

        have_blocks = node.find(jinja2.nodes.Block) is not None
        if have_blocks:
            raise ValueError("JSCompiler doesn't support blocks")

        eval_ctx = jinja2.nodes.EvalContext(self.environment, self.name)

        self.writeline("function root(opt_data, opt_sb) {")
        self.indent()

        self.writeline("var output = opt_sb || new soy.StringBuilder();")

        # process the root
        frame = jinja2.compiler.Frame(eval_ctx)
        frame.inspect(node.body)
        frame.toplevel = frame.rootlevel = True

        # pull_locals(frame)
        # pull_dependencies(node.body)
        self.blockvisit(node.body, frame)

        self.writeline("if (!opt_sb) return output.toString();")
        self.outdent()
        self.writeline("};")

    def blockvisit(self, nodes, frame):
        """
        Visit a list of noes ad block in a frame.
        """
        # if frame.buffer
        for node in nodes:
            self.visit(node, frame)

    def visit_Output(self, node, frame):
        finalize = str # unicode

        # try to evaluate as many chunks as possible into a static
        # string at compile time.
        body = []
        for child in node.nodes:
            try:
                const = child.as_const(frame.eval_ctx)
            except jinja2.nodes.Impossible:
                body.append(child)
                continue

            # the frame can't be volatile here, becaus otherwise the
            # as_const() function would raise an Impossible exception
            # at that point.
            try:
                if frame.eval_ctx.autoescape:
                    if hasattr(const, '__html__'):
                        const = const.__html__()
                    else:
                        const = escape(const)
                const = finalize(const)
            except:
                # if something goes wrong here we evaluate the node
                # at runtime for easier debugging
                body.append(child)
                continue

            if body and isinstance(body[-1], list):
                body[-1].append(const)
            else:
                body.append([const])

        first = True
        self.writeline("opt_sb.append(")
        for item in body:
            if isinstance(item, list):
                if not first:
                    self.write(", ")
                self.write(repr("".join(item)))
            else:
                # XXX - escape / do not escape variables.
                if not first:
                    self.write(", ")
                self.visit(item, frame)

            first = False
        self.write(");")

    def visit_Name(self, node, frame):
        self.write("opt_data." + node.name)
        frame.assigned_names.add(node.name)

    def visit_For(self, node, frame):
        children = node.iter_child_nodes(exclude = ("iter",))

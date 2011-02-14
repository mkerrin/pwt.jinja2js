from cStringIO import StringIO

from jinja2.visitor import NodeVisitor
import jinja2.nodes
import jinja2.compiler
import jinja2.ext
from jinja2.utils import Markup, concat, escape, is_python_keyword, next

class NamespaceNode(jinja2.nodes.Stmt):
    fields = ("namespace",)

class Namespace(jinja2.ext.Extension):
    """
    [Token(1, 'name', 'examples'),
     Token(1, 'dot', u'.'),
     Token(1, 'name', 'const'),
     Token(1, 'block_end', u'%}')
     ]
    """

    tags = set(["namespace"])

    def parse(self, parser):
        node = NamespaceNode(lineno = next(parser.stream).lineno)
        namespace = []
        while not parser.is_tuple_end():
            namespace.append(parser.stream.next().value)
        node.namespace = "".join(namespace)
        return node


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

        namespace = list(node.find_all(NamespaceNode))
        if len(namespace) != 1:
            raise ValueError("You must supply one namespace for your template")
        namespace = namespace[0].namespace

        have_extends = node.find(jinja2.nodes.Extends) is not None
        if have_extends:
            raise ValueError("JSCompiler doesn't support extends")

        have_blocks = node.find(jinja2.nodes.Block) is not None
        if have_blocks:
            raise ValueError("JSCompiler doesn't support blocks")

        eval_ctx = jinja2.nodes.EvalContext(self.environment, self.name)
        eval_ctx.namespace = namespace

        # process the root
        frame = jinja2.compiler.Frame(eval_ctx)
        frame.inspect(node.body)
        frame.toplevel = frame.rootlevel = True

        # pull_locals(frame)
        # pull_dependencies(node.body)
        self.blockvisit(node.body, frame)

    def blockvisit(self, nodes, frame):
        """
        Visit a list of noes ad block in a frame.
        """
        # if frame.buffer
        for node in nodes:
            self.visit(node, frame)

    def visit_Output(self, node, frame):
        # XXX - JS is only interested in macros etc, as all of JavaScript
        # is rendered into the global namespace so we need to ignore data in
        # the templates that is out side the macros.
        if frame.toplevel:
            return

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

    def function_scoping(self, node, frame, children = None, find_special = True):
        if children is None:
            children = node.iter_child_nodes()
        children = list(children)
        func_frame = frame.inner()
        func_frame.inspect(children, hard_scope = True)

        # variables that are undeclared (accessed before declaration) and
        # declared locally *and* part of an outside scope raise a template
        # assertion error. Reason: we can't generate reasonable code from
        # it without aliasing all the variables.
        # this could be fixed in Python 3 where we have the nonlocal
        # keyword or if we switch to bytecode generation
        overriden_closure_vars = (
            func_frame.identifiers.undeclared &
            func_frame.identifiers.declared &
            (func_frame.identifiers.declared_locally |
             func_frame.identifiers.declared_parameter)
        )
        if overriden_closure_vars:
            self.fail("It's not possible to set and access variables "
                      "derived from an outer scope! (affects: %s)" %
                      ", ".join(sorted(overriden_closure_vars)), node.lineno)

        # remove variables from a closure from the frame's undeclared
        # identifiers.
        func_frame.identifiers.undeclared -= (
            func_frame.identifiers.undeclared &
            func_frame.identifiers.declared
        )

        undeclared = jinja2.compiler.find_undeclared(children, ("caller", "kwargs", "varargs"))

        return func_frame

    def macro_body(self, node, frame, children = None):
        frame = self.function_scoping(node, frame, children = children)
        # macros are delayed, they never require output checks
        frame.require_output_check = False

        self.writeline("%s.%s = function(opt_data, opt_sb) {" %(
            frame.eval_ctx.namespace, node.name))
        self.indent()
        self.writeline("var output = opt_sb || new soy.StringBuilder();")
        self.blockvisit(node.body, frame)
        self.writeline("if (!opt_sb) return output.toString();")
        self.outdent()
        self.writeline("}")
        

    def visit_Macro(self, node, frame):
        body = self.macro_body(node, frame)
        frame.assigned_names.add(node.name)

    def visit_For(self, node, frame):
        children = node.iter_child_nodes(exclude = ("iter",))

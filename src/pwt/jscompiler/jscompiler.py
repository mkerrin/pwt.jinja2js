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


BINOPERATORS = {
    "and": "&&",
    "or": "||",
    }

OPERATORS = {
    "eq":    "==",
    "ne":    "!=",
    "gt":    ">",
    "gteq":  ">=",
    "lt":    "<",
    "lteq":  "<=",
    ## "in":    "in",
    ## "notin": "not in"
    }


def generate(node, environment, name, filename, stream = None):
    """Generate the python source for a node tree."""
    if not isinstance(node, jinja2.nodes.Template):
        raise TypeError("Can't compile non template nodes")
    generator = CodeGenerator(environment, name, filename, stream)
    generator.visit(node)
    if stream is None:
        return generator.stream.getvalue()


class JSFrameIdentifierVisitor(jinja2.compiler.FrameIdentifierVisitor):

    def __init__(self, identifiers, hard_scope, environment, ctx):
        super(JSFrameIdentifierVisitor, self).__init__(identifiers, hard_scope)

        self.environment = environment
        self.ctx = ctx

    # def visit_Name

    def visit_If(self, node):
        self.visit(node.test)
        for body in node.body:
            self.visit(body)
        for else_ in node.else_:
            self.visit(else_)

    def visit_Macro(self, node):
        self.identifiers.declared_locally.add(
            ("%s.%s" %(self.ctx.namespace, node.name)).encode("utf-8")
            )

    def visit_Import(self, node):
        # register import target as declare_locally
        super(JSFrameIdentifierVisitor, self).visit_Import(node)

        # Need to find namespace
        name = node.template.value
        source, filename, uptodate = self.environment.loader.get_source(
            self.environment, name)
        fromnode = self.environment._parse(source, name, filename)

        # Need to find the namespace
        namespace = list(fromnode.find_all(NamespaceNode))
        if len(namespace) != 1:
            raise jinja2.compiler.TemplateAssertionError(
                "You must supply one namespace for your template",
                0,
                name,
                filename)
        namespace = namespace[0].namespace

        self.identifiers.imports[node.target] = namespace.encode("utf-8")

        # Need to find all the macros defined in this namespace

    # def visit_FromImport(self, node):

    # def visit_Assign

    def visit_For(self, node):
        # declare the iteration variable
        self.visit(node.iter)
        # declare the target variable
        self.visit(node.target)

    # def visit_Callblock

    # def visit_FilterBlock

    # def visit_Block


class JSFrame(jinja2.compiler.Frame):

    def __init__(self, environment, eval_ctx, parent = None):
        super(JSFrame, self).__init__(eval_ctx, parent)

        # map local variables to imported code
        self.identifiers.imports = {}

        self.environment = environment

        # mapping of visit_Name callback to reassign variable names for use
        # in 'for' loops
        self.reassigned_names = {}

        # name -> method mapping for handling special variables in the
        # for loop
        self.forloop_buffer = None

    def inspect(self, nodes, hard_scope = False):
        """Walk the node and check for identifiers.  If the scope is hard (eg:
        enforce on a python level) overrides from outer scopes are tracked
        differently.
        """
        visitor = JSFrameIdentifierVisitor(
            self.identifiers, hard_scope, self.environment, self.eval_ctx)
        for node in nodes:
            visitor.visit(node)

    def inner(self):
        frame = JSFrame(self.environment, self.eval_ctx, self)
        frame.identifiers.imports = self.identifiers.imports
        return frame


class BaseCodeGenerator(NodeVisitor):

    def __init__(self, environment, name, filename, stream = None):
        super(BaseCodeGenerator, self).__init__()

        self.environment = environment
        self.name = name
        self.filename = filename

        if stream is None:
            stream = StringIO()

        self.stream = stream

        # the current line number
        self.code_lineno = 1

        # the debug information
        self.debug_info = []
        self._write_debug_info = None

        # the number of new lines before the next write()
        self._new_lines = 0

        # the line number of the last written statement
        self._last_line = 0

        # true if nothing was written so far.
        self._first_write = True

        # the current indentation
        self._indentation = 0

        self.encoding = "utf-8"

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

    def blockvisit(self, nodes, frame):
        """
        Visit a list of noes ad block in a frame. Some times we want to
        pass lists to the the visit method. Get around this here.
        """
        # if frame.buffer
        for node in nodes:
            self.visit(node, frame)


class CodeGenerator(BaseCodeGenerator):

    def visit_Template(self, node):
        """
        Setup the template output.

        Includes imports, macro definitions, etc.
        """
        namespace = list(node.find_all(NamespaceNode))
        if len(namespace) != 1:
            raise jinja2.compiler.TemplateAssertionError(
                "You must supply one namespace for your template",
                0, self.name, self.filename)
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
        frame = JSFrame(self.environment, eval_ctx)
        frame.inspect(node.body)
        frame.toplevel = frame.rootlevel = True

        # XXX - Need to validate the template here. Only accept macros

        self.writeline("goog.provide(" + repr(namespace.encode(self.encoding)) + ");")
        self.writeline("goog.require('soy');")

        # XXX - need to pull in extra requirements by inspecting any
        # call blocks.

        # pull_locals(frame)
        # pull_dependencies(node.body)
        self.blockvisit(node.body, frame)

    def visit_Import(self, node, frame):
        namespace = frame.identifiers.imports[node.target]
        self.writeline("goog.require('%s');" % namespace.encode("utf-8"), node)

    def visit_Macro(self, node, frame):
        self.writeline("", node)
        generator = MacroCodeGenerator(
            self.environment,
            self.name,
            self.filename,
            self.stream)
        generator.visit(node, frame)

    def visit_TemplateData(self, node, frame):
        self.writeline(node.data, node)


class GetNodeName(NodeVisitor):

    def visit_Name(self, node, frame, names):
        try:
            names.append(frame.reassigned_names[node.name])
        except KeyError:
            names.append(node.name)

    def visit_Getattr(self, node, frame, names):
        self.visit(node.node, frame, names)
        names.append(node.attr)

    def getName(self, node, frame):
        names = []

        self.visit(node, frame, names)

        return ".".join(names)
            

class MacroCodeGenerator(BaseCodeGenerator):
    # split out the macro code generator. This generate the guts of the
    # JavaScript we need to render the templates. Note that we do this
    # here seperate from the template generator above as we want to restrict
    # the Jinja2 template syntax for the JS implementation and we want to
    # format the generate code a bit like the templates. Gaps between templates,
    # comments should be displayed in the JS file. We need them for any closure
    # compiler hints we may want to put in.

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

        start = True
        for item in body:
            if isinstance(item, list):
                if start:
                    self.writeline("output.append(", node)
                    start = False
                else:
                    self.write(", ")
                self.write(repr("".join(item)))
            else:
                # XXX - escape / do not escape variables.
                if isinstance(item, jinja2.nodes.Call):
                    if not start:
                        self.write(");")
                        start = True
                    self.writeline("")
                    self.visit(item, frame)
                    self.write(";")
                else:
                    if start:
                        self.writeline("output.append(", item)
                        start = False
                    else:
                        self.write(", ")
                    self.visit(item, frame)
        if not start:
            self.write(");")

    def visit_Const(self, node, frame):
        # XXX - need to know the JavaScript ins and out here.
        val = node.value
        if val is None:
            self.write("null")
        elif val is True:
            self.write("true")
        elif val is False:
            self.write("false")
        else:
            self.write(repr(val))

    def visit_Name(self, node, frame):
        # declared_parameter
        # declared
        # outer_undeclared
        # declared_locally
        # undeclared
        name = node.name

        if name in frame.identifiers.declared_parameter:
            self.write("opt_data." + name)
            frame.assigned_names.add("opt_data." + name) # neccessary?
        elif name in frame.identifiers.declared or \
                 name in frame.identifiers.declared_locally:
            try:
                # Has this variable been reassigned to avoid duplication
                name = frame.reassigned_names[name]
            except KeyError:
                pass
            self.write(name)

            frame.assigned_names.add(name) # neccessary?
        elif name in frame.identifiers.imports:
            self.write(frame.identifiers.imports[name])
        else:
            raise Exception("Where is the parameter %s (%s:%d)" %(
                name, self.filename, node.lineno))

    def visit_Getattr(self, node, frame):
        if frame.forloop_buffer and node.node.name == "loop":
            if node.attr == "index0":
                self.write("%sIndex" % frame.forloop_buffer)
            elif node.attr == "index":
                self.write("%sIndex" % frame.forloop_buffer)
                self.write(" + 1")
            elif node.attr == "revindex0":
                self.write("%sListLen - %sIndex" %(frame.forloop_buffer,
                                                   frame.forloop_buffer))
            elif node.attr == "revindex":
                self.write("%sListLen - %sIndex - 1" %(frame.forloop_buffer,
                                                       frame.forloop_buffer))
            elif node.attr == "first":
                self.write("%sIndex == 0" % frame.forloop_buffer)
            elif node.attr == "last":
                self.write("%sIndex == (%sListLen - 1)" %(frame.forloop_buffer,
                                                          frame.forloop_buffer))
            elif node.attr == "length":
                self.write("%sListLen" % frame.forloop_buffer)
            else:
                raise AttributeError("loop.%s not defined" % node.attr)
        else:
            possible_macro = GetNodeName().getName(node, frame)
            if possible_macro in frame.identifiers.declared:
                self.write(possible_macro)
            else:
                self.visit(node.node, frame)
                self.write(".%s" % node.attr)

    def binop(operator):
        def visitor(self, node, frame):
            self.write("(")
            self.visit(node.left, frame)
            self.write(" %s " % BINOPERATORS[operator])
            self.visit(node.right, frame)
            self.write(")")
        return visitor

    visit_And = binop("and")
    visit_Or = binop("or")

    def visit_Compare(self, node, frame):
        self.visit(node.expr, frame)
        for op in node.ops:
            self.visit(op, frame)

    def visit_Operand(self, node, frame):
        self.write(" %s " % OPERATORS[node.op])
        self.visit(node.expr, frame)

    def visit_If(self, node, frame):
        if_frame = frame.soft()
        self.writeline("if (", node)
        self.visit(node.test, if_frame)
        self.write(") {")

        self.indent()
        self.blockvisit(node.body, if_frame)
        self.outdent()

        if node.else_:
            self.writeline("} else {")
            self.indent()
            self.blockvisit(node.else_, if_frame)
            self.outdent()

        self.writeline("}")

    def visit_For(self, node, frame):
        children = node.iter_child_nodes(exclude = ("iter",))

        if node.recursive:
            raise NotImplementedError(
                "JSCompiler doesn't support recursive loops")

        # try to figure out if we have an extended loop.  An extended loop
        # is necessary if the loop is in recursive mode or if the special loop
        # variable is accessed in the body.
        extended_loop = "loop" in jinja2.compiler.find_undeclared(
            node.iter_child_nodes(only = ("body",)), ("loop",))

        loop_frame = frame.soft() # JavaScript for loops don't change namespace

        if extended_loop:
            loop_frame.identifiers.add_special("loop")
            loop_frame.forloop_buffer = node.target.name
        for name in node.find_all(jinja2.nodes.Name):
            if name.ctx == "store" and name.name == "loop":
                self.fail("Can't assign to special loop variable "
                          "in for-loop target", name.lineno)

        self.writeline("var %sList = " % node.target.name)
        self.visit(node.iter, loop_frame)
        self.write(";")

        self.writeline("var %(name)sListLen = %(name)sList.length;" %{"name": node.target.name})
        if node.else_:
            self.writeline("if (%sListLen > 0) {" % node.target.name)
            self.indent()

        self.writeline("for (var %(name)sIndex = 0; %(name)sIndex < %(name)sListLen; %(name)sIndex++) {" %{"name": node.target.name})
        self.indent()

        self.writeline("var %(name)sData = %(name)sList[%(name)sIndex];" %{"name": node.target.name})
        loop_frame.reassigned_names[node.target.name] = "%sData" % node.target.name
        self.blockvisit(node.body, loop_frame)
        self.outdent()
        self.writeline("}")

        if node.else_:
            self.outdent()
            self.writeline("} else {")
            self.indent()
            self.blockvisit(node.else_, frame)
            self.outdent()
            self.writeline("}")

    def function_scoping(
            self, node, frame, children = None, find_special = True):
        if children is None:
            children = node.iter_child_nodes()

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
        frame.assigned_names.add("%s.%s" %(frame.eval_ctx.namespace, node.name))

    def signature(self, node, frame, extra_kwargs = {}):
        if node.args:
            raise jinja2.compiler.TemplateAssertionError(
                "Function call with positional arguments not allowed with JS",
                node.lineno, self.name, self.filename)

        start = True
        self.write("{")
        for kwarg in node.kwargs:
            if not start:
                self.write(", ")
                start = False
            self.write(kwarg.key)
            self.write(": ")
            self.visit(kwarg.value, frame)
        self.write("}")

        if node.dyn_args or node.dyn_kwargs:
            raise jinja2.compiler.TemplateAssertionError(
                "JS Does not support positional or keyword arguments",
                node.lineno, self.name, self.filename)

    def visit_Call(self, node, frame, forward_caller = False):
        # function symbol to call
        self.visit(node.node, frame)
        # function signature
        self.write("(")
        extra_kwargs = forward_caller and {"caller": "caller"} or None
        self.signature(node, frame, extra_kwargs)
        self.write(", output)")

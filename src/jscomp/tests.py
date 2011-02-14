import unittest
from cStringIO import StringIO

import jinja2
import jinja2.compiler
import jinja2.optimizer
import jinja2.runtime

class DictBCache(jinja2.BytecodeCache):

    def __init__(self):
        self.cache = {}

    def load_bytecode(self, bucket):
        if bucket.key in self.cache:
            raise Exception("Never happens")
            stream = self.cache[bucket.key]
            bucket.load_bytecode(stream)

    def dump_bytecode(self, bucket):
        # write bytecode in bucket to cache
        stream = self.cache[bucket.key] = StringIO()
        bucket.write_bytecode(stream)


class TemplatesTestCase(unittest.TestCase):

    def test_get_template(self):
        env = jinja2.Environment(
            loader = jinja2.PackageLoader("jscomp", "test_templates"))
        tmpl = env.get_template("hello.html")
        self.assertEqual(tmpl.render(), """<ul>
  
  <li>No items.</li>
  
</ul>""")

    def test_get_template2(self):
        # cached
        env = jinja2.Environment(
            loader = jinja2.PackageLoader("jscomp", "test_templates"),
            bytecode_cache = DictBCache())
        tmpl = env.get_template("hello.html")
        self.assertEqual(tmpl.render(), """<ul>
  
  <li>No items.</li>
  
</ul>""")

    def test_get_template3(self):
        # use cached package
        env = jinja2.Environment(
            loader = jinja2.PackageLoader("jscomp", "test_templates"),
            bytecode_cache = DictBCache())
        # load
        env.get_template("hello.html")
        # get cached
        tmpl = env.get_template("hello.html")
        self.assertEqual(tmpl.render(), """<ul>
  
  <li>No items.</li>
  
</ul>""")


class CompilerTemplateTestCase(unittest.TestCase):

    def setUp(self):
        self.loader = jinja2.PackageLoader("jscomp", "test_templates")
        self.env = jinja2.Environment(
            loader = self.loader, extensions = ["jscomp.jscompiler.Namespace"])

    def get_template_node(self, name):
        source, filename, uptodate = self.loader.get_source(self.env, name)
        # code = env.compile(source, name, filename)

        node = self.env._parse(source, name, filename)
        # jinja2.optimizer.optimize(source)

        return node

    def test_for_compile1(self):
        # load
        name = "for.html"

        node = self.get_template_node(name)

        stream = StringIO()
        jinja2.compiler.generate(node, self.env, name, name, stream = stream)
        source_code = stream.getvalue()
        code = compile(source_code, name, "exec")

        # from_code
        namespace = {
            "environment": self.env,
            "__file__": name
            }
        exec code in namespace

        context = jinja2.runtime.new_context(
            self.env, name, namespace["blocks"], {"data": [1, 3, 5]})

        ## self.assertEqual("".join(namespace["root"](context)), """
##   Item 1.

##   Item 3.

##   Item 5.
## """)

    def test_const1(self):
        name = "const.html"

        node = self.get_template_node(name)

        stream = StringIO()
        jinja2.compiler.generate(node, self.env, name, name, stream = stream)
        source_code = stream.getvalue()
        code = compile(source_code, name, "exec")

        # from_code
        namespace = {
            "environment": self.env,
            "__file__": name
            }
        exec code in namespace

        context = jinja2.runtime.new_context(self.env, name, namespace["blocks"], {})

        # self.assertEqual("".join(namespace["root"](context)), "Hello, world!")

    def test_var1(self):
        name = "var1.html"

        node = self.get_template_node(name)

        stream = StringIO()
        jinja2.compiler.generate(node, self.env, name, name, stream = stream)
        source_code = stream.getvalue()
        code = compile(source_code, name, "exec")

        # from_code
        namespace = {
            "environment": self.env,
            "__file__": name
            }
        exec code in namespace

        context = jinja2.runtime.new_context(self.env, name, namespace["blocks"], {"name": "Michael Kerrin"})

        # self.assertEqual("".join(namespace["root"](context)), "Michael Kerrin")

    def test_var2(self):
        name = "var2.html"

        node = self.get_template_node(name)

        stream = StringIO()
        jinja2.compiler.generate(node, self.env, name, name, stream = stream)
        source_code = stream.getvalue()
        code = compile(source_code, name, "exec")

        # from_code
        namespace = {
            "environment": self.env,
            "__file__": name
            }
        exec code in namespace

        context = jinja2.runtime.new_context(self.env, name, namespace["blocks"], {"name": "Michael"})

        # self.assertEqual("".join(namespace["root"](context)), "Hello, Michael!")


import jscompiler

class JSCompilerTemplateTestCase(unittest.TestCase):

    def setUp(self):
        super(JSCompilerTemplateTestCase, self).setUp()

        self.loader = jinja2.PackageLoader("jscomp", "test_templates")
        self.env = jinja2.Environment(
            loader = self.loader,
            extensions = ["jscomp.jscompiler.Namespace"],
            )

    def get_compile(self, name, env = None):
        env = env or self.env
        # load
        source, filename, uptodate = self.loader.get_source(env, name)
        # code = env.compile(source, name, filename)

        node = env._parse(source, name, filename)
        # jinja2.optimizer.optimize(source)

        return node

    def test_missing_namespace1(self):
        node = self.get_compile("const.html")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "const.html", "const.html", stream = stream)

    def test_const1(self):
        node = self.get_compile("const.html")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "const.html", "const.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """examples.const.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    opt_sb.append('\\nHello, world!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var1(self):
        node = self.get_compile("var1.html")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "var1.html", "var1.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """examples.var1.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    opt_sb.append('\\n', opt_data.name, '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var2(self):
        node = self.get_compile("var2.html")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "var2.html", "var2.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """examples.var2.helloName = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    opt_sb.append('\\nHello, ', opt_data.name, '!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_for1(self):
        node = self.get_compile("for.html")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

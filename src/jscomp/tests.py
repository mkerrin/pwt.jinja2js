import unittest
from cStringIO import StringIO

import soy_wsgi

import jinja2.compiler
import jinja2.optimizer
import jinja2.runtime

class CompilerTemplateTestCase(unittest.TestCase):

    def setUp(self):
        self.loader = jinja2.PackageLoader("jscomp", "test_templates")
        self.env = jinja2.Environment(
            loader = self.loader, extensions = ["jscomp.jscompiler.Namespace"])

    def get_template_node(self, name):
        source, filename, uptodate = self.loader.get_source(self.env, name)
        # code = env.compile(source, name, filename)

        node = self.env._parse(source, name, filename)
        # node = jinja2.optimizer.optimize(node, self.env)

        return node

    def test_for1(self):
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

    def test_if1(self):
        node = self.get_template_node("if1.html")

        stream = StringIO()
        jinja2.compiler.generate(
            node, self.env, "if1.html", "if1.html", stream = stream)
        source_code = stream.getvalue()

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
        # jinja2.optimizer.optimize(node, env)

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

        self.assertEqual(source_code, """goog.provide('examples.const');
goog.require('soy');
examples.const.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, world!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var1(self):
        node = self.get_compile("var1.html")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "var1.html", "var1.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('examples.var1');
goog.require('soy');
examples.var1.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', opt_data.name, '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var2(self):
        node = self.get_compile("var2.html")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "var2.html", "var2.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('examples.var2');
goog.require('soy');
examples.var2.helloName = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, ', opt_data.name, '!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_for1(self):
        # XXX - test recursive loop
        node = self.get_compile("for.html")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('examples.for');
goog.require('soy');
examples.for.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n');
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    if (itemListLen > 0) {
        for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
            var itemData = itemList[itemIndex];
            output.append('\\n  Item ', itemData, '.\\n');
        }
    } else {
        output.append('\\n  No items.\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_if1(self):
        node = self.get_compile("if1.html")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('examples.if1');
goog.require('soy');
examples.if1.iftest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n');
    if (opt_data.option) {
        output.append('\\nOption set.\\n');
    } else {
        output.append('\\nNo option.\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
}""")


class JSCompilerTemplateTestCaseOptimized(JSCompilerTemplateTestCase):

    def get_compile(self, name, env = None):
        env = env or self.env
        # load
        source, filename, uptodate = self.loader.get_source(env, name)
        # code = env.compile(source, name, filename)

        node = env._parse(source, name, filename)
        node = jinja2.optimizer.optimize(node, env)

        return node


import webtest

class SoyServer(unittest.TestCase):

    def get_app(self):
        return webtest.TestApp(
            soy_wsgi.Resources(
                url = "/soy/", packages = "jscomp:test_templates"))

    def test_soy1(self):
        app = self.get_app()
        self.assertRaises(webtest.AppError, app.get, "/soy/missing.soy")

    def test_soy2(self):
        app = self.get_app()
        res = app.get("/soy/example.soy")

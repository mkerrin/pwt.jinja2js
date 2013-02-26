from cStringIO import StringIO
import os
import os.path
import shutil
import tempfile
import unittest
import webtest

import zc.buildout.testing
from zc.buildout.rmtree import rmtree

import jinja2.compiler
import jinja2.nodes
import jinja2.optimizer
import jinja2.environment

import jscompiler
import cli
import environment
import wsgi
import app


def generateMacro(
        node, environment, name, filename, autoescape = False, writer = None):
    # Need to test when we are not using an Environment from jinja2js
    if writer is None:
        writer = getattr(environment, "writer", jscompiler.StringBuilder)
    generator = jscompiler.MacroCodeGenerator(
        environment, writer(), None, None)
    eval_ctx = jinja2.nodes.EvalContext(environment, name)
    eval_ctx.namespace = "test"
    eval_ctx.autoescape = autoescape
    generator.blockvisit(node.body, jscompiler.JSFrame(environment, eval_ctx))
    return generator.writer.stream.getvalue()


class JSCompilerTestCase(unittest.TestCase):

    def setUp(self):
        super(JSCompilerTestCase, self).setUp()

        self.env = environment.create_environment(
            packages = ["pwt.jinja2js:test_templates"],
            writer = "pwt.jinja2js.jscompiler.StringBuilder",
            )

    def get_compile_from_string(self, source, name = None, filename = None):
        node = self.env._parse(source, name, filename)
        # node = jinja2.optimizer.optimize(node, self.env)

        return node


class JSEnvironment(unittest.TestCase):

    def test_env_directories(self):
        env = environment.create_environment(
            directories = ["%s/test_templates" % os.path.dirname(jscompiler.__file__)],
            writer = "pwt.jinja2js.jscompiler.StringBuilder",
            )

        source = env.loader.get_source(env, "example.jinja2")
        self.assertEqual(source[0], "{% namespace example %}\n\n{% macro hello(name) %}\nHello, {{ name }}!\n{% endmacro %}\n")


class JSCompilerTemplateTestCase(JSCompilerTestCase):

    def test_missing_namespace1(self):
        node = self.get_compile_from_string("""{% macro hello() %}
Hello, world!
{% endmacro %}""")
        source_code = jscompiler.generateClosure(
            node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\nHello, world!\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_const1(self):
        node = self.get_compile_from_string("""{% macro hello() %}
Hello, world!
{% endmacro %}""")
        source_code = generateMacro(node, self.env, "const.html", "const.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\nHello, world!\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_undeclared_var1(self):
        # variable is undeclared
        node = self.get_compile_from_string("""{% macro hello() %}
{{ name }}
{% endmacro %}
""")
        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            generateMacro, node, self.env, "var1.html", "var1.html")

    def test_namespaced_var1(self):
        # variable is undeclared. We if need to require these variables then
        # we can do so outside the macro definition, like so.
        node = self.get_compile_from_string("""{% namespace test %}
goog.require('goog.color.names'); // needed to use goog.color.names data
{% macro hello() %}
{{ goog.color.names.aqua }}
{% endmacro %}
""")
        source_code = jscompiler.generateClosure(
            node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.provide('test');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

goog.require('goog.color.names'); // needed to use goog.color.names data
test.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n', goog.color.names.aqua, '\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_var1(self):
        node = self.get_compile_from_string("""{% macro hello(name) %}
{{ name }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var1.html", "var1.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n', opt_data.name, '\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_var1_accessobject1(self):
        # Try and access the property `name` from the object properties
        node = self.get_compile_from_string("""{% macro hello(properties) %}
{{ properties["name"] }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var1.html", "var1.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n', opt_data.properties['name'], '\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_var1_accessobject2(self):
        # Try and access the property name reference by `name` from the object
        # properties
        node = self.get_compile_from_string("""{% macro hello(properties, name) %}
{{ properties[name] }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var1.html", "var1.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n', opt_data.properties[opt_data.name], '\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_var2(self):
        node = self.get_compile_from_string("""{% macro helloName(name) %}
Hello, {{ name }}!
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.helloName = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\nHello, ', opt_data.name, '!\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_var3(self):
        # variables with numerical addition
        node = self.get_compile_from_string("""{% macro add(num) %}
{{ num + 200 }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n', (opt_data.num + 200), '\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_var4(self):
        # variables with numerical addition to variable
        node = self.get_compile_from_string("""{% macro add(num, step) %}
{{ num + step }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n', (opt_data.num + opt_data.step), '\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_var5(self):
        # variables minus, power of,
        node = self.get_compile_from_string("""{% macro add(num, step) %}
{{ (num - step) ** 2 }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n', Math.pow((opt_data.num - opt_data.step), 2), '\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_var6(self):
        # variables floor division
        node = self.get_compile_from_string("""{% macro fd(n1, n2) %}
{{ Math.floor(n1 / n2) }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n', Math.floor((opt_data.num / opt_data.step)), '\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_var6(self):
        # variables minus, power of,
        node = self.get_compile_from_string("""{% macro add(num, step) %}
{{ num - (step ** 2) }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n', (opt_data.num - Math.pow(opt_data.step, 2)), '\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_var7(self):
        # variables + with autoescape on
        node = self.get_compile_from_string("""{% macro add(num, step) %}{{ num - (step ** 2) }}{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html", autoescape = True)

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(goog.string.htmlEscape(String((opt_data.num - Math.pow(opt_data.step, 2)))));
    if (!opt_sb) return output.toString();
};""")

    def test_var8(self):
        # variables + with autoescape and the escape filter
        node = self.get_compile_from_string("""{% macro add(num, step) %}{{ (num - (step ** 2)) | escape }}{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html", autoescape = True)

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(goog.string.htmlEscape(String((opt_data.num - Math.pow(opt_data.step, 2)))));
    if (!opt_sb) return output.toString();
};""")

    def test_var9(self):
        # variables -
        node = self.get_compile_from_string("""{% macro add(num) %}{{ -num + 20 }}{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html", autoescape = True)

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(goog.string.htmlEscape(String(((-opt_data.num) + 20))));
    if (!opt_sb) return output.toString();
};""")

    def test_var10(self):
        # variables +
        node = self.get_compile_from_string("""{% macro add(num) %}{{ +num + 20 }}{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html", autoescape = True)

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(goog.string.htmlEscape(String(((+opt_data.num) + 20))));
    if (!opt_sb) return output.toString();
};""")

    def test_var11(self):
        # variables not
        node = self.get_compile_from_string("""{% macro add(bool) %}{{ not bool }}{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html", autoescape = True)

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(goog.string.htmlEscape(String((!opt_data.bool))));
    if (!opt_sb) return output.toString();
};""")

    def test_var12(self):
        # variables with default values
        node = self.get_compile_from_string("""{% macro hello(name = 'World') -%}
Hello {{ name }}!
{%- endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb, opt_caller) {
    var defaults = {name: 'World'};
    for (var key in defaults) {
        if (!(key in opt_data)) {
            opt_data[key] = defaults[key];
        }
    }
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('Hello ', opt_data.name, '!');
    if (!opt_sb) return output.toString();
};""")

    def test_var13(self):
        # variables with default values
        node = self.get_compile_from_string("""{% macro hello(name, age = 30) -%}
{{ name }} is {{ age }}
{%- endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb, opt_caller) {
    var defaults = {age: 30};
    for (var key in defaults) {
        if (!(key in opt_data)) {
            opt_data[key] = defaults[key];
        }
    }
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(opt_data.name, ' is ', opt_data.age);
    if (!opt_sb) return output.toString();
};""")

    def test_var14(self):
        # variables with multiple default values
        node = self.get_compile_from_string("""{% macro hello(name = 'Michael', age = 30) -%}
{{ name }} is {{ age }}
{%- endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb, opt_caller) {
    var defaults = {name: 'Michael', age: 30};
    for (var key in defaults) {
        if (!(key in opt_data)) {
            opt_data[key] = defaults[key];
        }
    }
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(opt_data.name, ' is ', opt_data.age);
    if (!opt_sb) return output.toString();
};""")

    def test_for1(self):
        # test for loop
        node = self.get_compile_from_string("""{% macro fortest(data) %}
{% for item in data %}
  Item {{ item }}.
{% else %}
  No items.
{% endfor %}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
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
};""")

    def test_for2(self):
        # test loop.index0 variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.index0 }}{% endfor %}{% endmacro %}")
        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex);
    }
    if (!opt_sb) return output.toString();
};""")

    def test_for3(self):
        # test loop.index variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.index }}{% endfor %}{% endmacro %}")
        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append((itemIndex + 1));
    }
    if (!opt_sb) return output.toString();
};""")

    def test_for4(self):
        # test loop.revindex & loop.revindex0 variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.revindex }} - {{loop.revindex0 }}{% endfor %}{% endmacro %}")
        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append((itemListLen - itemIndex - 1), ' - ', (itemListLen - itemIndex));
    }
    if (!opt_sb) return output.toString();
};""")

    def test_for5(self):
        # test loop.length & loop.first & loop.last variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.length }} - {{loop.first }} - {{ loop.last }}{% endfor %}{% endmacro %}")
        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemListLen, ' - ', itemIndex == 0, ' - ', itemIndex == (itemListLen - 1));
    }
    if (!opt_sb) return output.toString();
};""")

    def test_for6(self):
        # test invalid loop access
        node = self.get_compile_from_string("{% namespace xxx %}{% macro fortest(data) %}{% for item in data %}{{ loop.missing }}{% endfor %}{% endmacro %}")
        self.assertRaises(
            AttributeError,
            jscompiler.generate, node, self.env, "for.html", "for.html")

    def test_for7(self):
        # test loop.index with other variable.
        node = self.get_compile_from_string("{% macro fortest(data, name) %}{% for item in data %}{{ loop.index }} - {{ name }}{% endfor %}{% endmacro %}")
        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append((itemIndex + 1), ' - ', opt_data.name);
    }
    if (!opt_sb) return output.toString();
};""")

    def test_for8(self):
        # test loop.index with other variable, with attribute
        node = self.get_compile_from_string("{% macro fortest(data, param) %}{% for item in data %}{{ loop.index }} - {{ param.name }}{% endfor %}{% endmacro %}")
        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append((itemIndex + 1), ' - ', opt_data.param.name);
    }
    if (!opt_sb) return output.toString();
};""")

    def test_for9(self):
        # bug report - need to rename nested for loop iterators.
        node = self.get_compile_from_string("""{% macro fortest(jobs) %}
{% for job in jobs %}
   {% for badge in job.badges %}
       {{ badge.name }}
   {% endfor %}
{% endfor %}
{% endmacro %}""")

        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n');
    var jobList = opt_data.jobs;
    var jobListLen = jobList.length;
    for (var jobIndex = 0; jobIndex < jobListLen; jobIndex++) {
        var jobData = jobList[jobIndex];
        output.append('\\n   ');
        var badgeList = jobData.badges;
        var badgeListLen = badgeList.length;
        for (var badgeIndex = 0; badgeIndex < badgeListLen; badgeIndex++) {
            var badgeData = badgeList[badgeIndex];
            output.append('\\n       ', badgeData.name, '\\n   ');
        }
        output.append('\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_for10(self):
        # test for in list loop
        node = self.get_compile_from_string("""{% macro forinlist(jobs) %}
{% for job in [1, 2, 3] %}
   {{ job }}
{% endfor %}
{% endmacro %}""")

        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.forinlist = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n');
    var jobList = [1, 2, 3];
    var jobListLen = jobList.length;
    for (var jobIndex = 0; jobIndex < jobListLen; jobIndex++) {
        var jobData = jobList[jobIndex];
        output.append('\\n   ', jobData, '\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_for11(self):
        # test for loop not producing extra namespace requirements
        node = self.get_compile_from_string("""{% namespace test %}{% macro forinlist(jobs) %}
{% for job in jobs %}{{ job.name }}{% endfor %}
{% endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('test');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');
test.forinlist = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n');
    var jobList = opt_data.jobs;
    var jobListLen = jobList.length;
    for (var jobIndex = 0; jobIndex < jobListLen; jobIndex++) {
        var jobData = jobList[jobIndex];
        output.append(jobData.name);
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_for12(self):
        # test for loop for conflicting variables, which doesn't happen
        node = self.get_compile_from_string("""{% namespace test %}{% macro forinlist(jobs, jobData) -%}
{% for job in jobs %}{{ job.name }} does {{ jobData }}{% endfor %}
{%- endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('test');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');
test.forinlist = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    var jobList = opt_data.jobs;
    var jobListLen = jobList.length;
    for (var jobIndex = 0; jobIndex < jobListLen; jobIndex++) {
        var jobData = jobList[jobIndex];
        output.append(jobData.name, ' does ', opt_data.jobData);
    }
    if (!opt_sb) return output.toString();
};""")

    def test_for13_confliction_variables_for_loop(self):
        # XXX - test for loop for conflicting variables. Here we have a
        # namespaced variable that gets required but conflicts with the
        # variable inside the loop that we created. If this is a problem
        # I will fix it, but it probable won't
        node = self.get_compile_from_string("""{% namespace test %}{% macro forinlist(jobs) -%}
{% for job in jobs %}{{ job.name }} does {{ jobData.name }}{% endfor %}
{%- endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('test');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');
test.forinlist = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    var jobList = opt_data.jobs;
    var jobListLen = jobList.length;
    for (var jobIndex = 0; jobIndex < jobListLen; jobIndex++) {
        var jobData = jobList[jobIndex];
        output.append(jobData.name, ' does ', jobData.name);
    }
    if (!opt_sb) return output.toString();
};""")

    def test_if1(self):
        # test if
        node = self.get_compile_from_string("""{% macro testif(option) %}{% if option %}{{ option }}{% endif %}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "if.html", "if.html")

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
};""")

    def test_if2(self):
        # test if / else
        node = self.get_compile_from_string("""{% macro iftest(option) %}
{% if option %}
Option set.
{% else %}
No option.
{% endif %}
{% endmacro %}
""")

        source_code = generateMacro(node, self.env, "if.html", "if.html")

        self.assertEqual(source_code, """test.iftest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n');
    if (opt_data.option) {
        output.append('\\nOption set.\\n');
    } else {
        output.append('\\nNo option.\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_if3(self):
        # test if ==
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num == 0 %}{{ num }}{% endif %}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "if.html", "if.html")

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    if (opt_data.num == 0) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
};""")

    def test_if4(self):
        # test if == and !=
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num != 0 and num == 2 %}{{ num }}{% endif %}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "if.html", "if.html")

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    if ((opt_data.num != 0 && opt_data.num == 2)) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
};""")

    def test_if5(self):
        # test if > and >= and < and <=
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num > 0 and num >= 1 and num < 2 and num <= 3 %}{{ num }}{% endif %}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "if.html", "if.html")

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    if ((((opt_data.num > 0 && opt_data.num >= 1) && opt_data.num < 2) && opt_data.num <= 3)) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
};""")

    def test_if6(self):
        # test if in
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num in [1, 2, 3] %}{{ num }}{% endif %}{% endmacro %}""")

        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            generateMacro, node, self.env, "if.html", "if.html")

    def test_if7(self):
        # test if in
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num not in [1, 2, 3] %}{{ num }}{% endif %}{% endmacro %}""")

        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            generateMacro, node, self.env, "if.html", "if.html")

    def test_if8(self):
        # test if > and >= and < and <=
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num + 1 == 2 %}{{ num }}{% endif %}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "if.html", "if.html")

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    if ((opt_data.num + 1) == 2) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
};""")

    def test_condexpr1(self):
        # test if
        node = self.get_compile_from_string("""{% macro testif(option) %}{{ option if option }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "condexpr.html", "condexpr.html")

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(opt_data.option ? opt_data.option : '');
    if (!opt_sb) return output.toString();
};""")

    def test_condexpr2(self):
        # test if / else
        node = self.get_compile_from_string("""{% macro iftest(option) %}
{{ 'Option set.' if option else 'No option.' }}
{% endmacro %}
""")

        source_code = generateMacro(node, self.env, "condexpr.html", "condexpr.html")

        self.assertEqual(source_code, """test.iftest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n', opt_data.option ? 'Option set.' : 'No option.', '\\n');
    if (!opt_sb) return output.toString();
};""")


    def test_set1(self):
        node = self.get_compile_from_string("""{% macro set1() %}{% set num = 2 %}{{ num }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "if.html", "if.html")

        self.assertEqual(source_code, """test.set1 = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    var num = 2;
    output.append(num);
    if (!opt_sb) return output.toString();
};""")

    def test_call_macro1(self):
        # call macro in same template, without arguments.
        node = self.get_compile_from_string("""{% namespace xxx %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}{{ xxx.testif() }}{% endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

xxx.testif = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
};

xxx.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    xxx.testif({}, output);
    if (!opt_sb) return output.toString();
};""")

    def test_call_macro2(self):
        # call macro in same template where the namespace contains
        # multiple dotted names.
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.testif() }}{% endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

xxx.ns1.testif = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
};

xxx.ns1.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    xxx.ns1.testif({}, output);
    if (!opt_sb) return output.toString();
};""")

    def test_call_macro3(self):
        # call macro passing in a argument
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.testif(option = true) }}{% endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

xxx.ns1.testif = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
};

xxx.ns1.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    xxx.ns1.testif({option: true}, output);
    if (!opt_sb) return output.toString();
};""")

    def test_call_macro3_multiple_arguments(self):
        # call macro passing in multiple arguments
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option, value) -%}
{% if option %}{{ option }}{% endif %}{{ value }}{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.testif(option = true, value = 3) }}{% endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

xxx.ns1.testif = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    output.append(opt_data.value);
    if (!opt_sb) return output.toString();
};

xxx.ns1.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    xxx.ns1.testif({option: true, value: 3}, output);
    if (!opt_sb) return output.toString();
};""")

    def test_call_macro4(self):
        # call macro passing parament, with extra output
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}Hello, {{ xxx.ns1.testif(option = true) }}!{% endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

xxx.ns1.testif = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
};

xxx.ns1.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('Hello, ');
    xxx.ns1.testif({option: true}, output);
    output.append('!');
    if (!opt_sb) return output.toString();
};""")

    def test_call_macro5(self):
        # call macro with positional arguments
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
testif(option) {
    if (option) return 'me';
    return 'you';
}

{% macro testcall() %}Hello, {{ testif(true) }}!{% endmacro %}""")

        source_code = jscompiler.generateClosure(node, self.env, "", "")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

testif(option) {
    if (option) return 'me';
    return 'you';
}

xxx.ns1.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('Hello, ', testif(true), '!');
    if (!opt_sb) return output.toString();
};""")

    def test_call_macro5_multiplepositional(self):
        # call macro with positional arguments
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
printName(name, age) {
    retuurn name + ' is ' + age;
}

{% macro testcall() %}{{ printName('michael', 31) }}!{% endmacro %}""")

        source_code = jscompiler.generateClosure(node, self.env, "", "")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

printName(name, age) {
    retuurn name + ' is ' + age;
}

xxx.ns1.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(printName('michael', 31), '!');
    if (!opt_sb) return output.toString();
};""")

    def test_call_macro5_positional_keyword(self):
        # We can't mix positional and keyword arguments in Java Script
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
testif(option) {
    if (option) return 'me';
    return 'you'
}

{% macro testcall() %}Hello, {{ testif(true, keyword = false) }}!{% endmacro %}""")

        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            jscompiler.generateClosure, node, self.env, "", "")

    def test_call_macro6(self):
        # call macro with dynamic keywrod arguments
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}Hello, {{ xxx.ns1.testif(**{option: true}) }}!{% endmacro %}""")

        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            jscompiler.generateClosure, node, self.env, "", "")

    def test_call_macro7(self):
        # call macro with string keyword
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro hello(name) -%}
Hello, {% if name %}{{ name }}{% else %}world{% endif %}!{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.hello(name = "Michael") }}{% endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

xxx.ns1.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('Hello, ');
    if (opt_data.name) {
        output.append(opt_data.name);
    } else {
        output.append('world');
    }
    output.append('!');
    if (!opt_sb) return output.toString();
};

xxx.ns1.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    xxx.ns1.hello({name: 'Michael'}, output);
    if (!opt_sb) return output.toString();
};""")

    def test_call_macro8(self):
        # call macro with parameter sub
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro hello(name) -%}
Hello, {% if name %}{{ name.first }}{% else %}world{% endif %}!{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.hello(name = {"first": "Michael"}) }}{% endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

xxx.ns1.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('Hello, ');
    if (opt_data.name) {
        output.append(opt_data.name.first);
    } else {
        output.append('world');
    }
    output.append('!');
    if (!opt_sb) return output.toString();
};

xxx.ns1.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    xxx.ns1.hello({name: {first: 'Michael'}}, output);
    if (!opt_sb) return output.toString();
};""")

    def test_call_macro9(self):
        # call macro with parameter sub, without quotes
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro hello(name) -%}
Hello, {% if name %}{{ name.first }}{% else %}world{% endif %}!{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.hello(name = {first: "Michael"}) }}{% endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

xxx.ns1.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('Hello, ');
    if (opt_data.name) {
        output.append(opt_data.name.first);
    } else {
        output.append('world');
    }
    output.append('!');
    if (!opt_sb) return output.toString();
};

xxx.ns1.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    xxx.ns1.hello({name: {first: 'Michael'}}, output);
    if (!opt_sb) return output.toString();
};""")

    def test_call_macro10(self):
        # call macro with parameter sub, key constains a dot.
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro hello(name) -%}
Hello, {% if name %}{{ name.first }}{% else %}world{% endif %}!{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.hello(name = {"first.name": "Michael"}) }}{% endmacro %}""")

        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            jscompiler.generateClosure, node, self.env, "f.html", "f.html")

    def test_call_macro11(self):
        # call macro with parameter sub, with invalid key
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro hello(name) -%}
Hello, {% if name %}{{ name.first }}{% else %}world{% endif %}!{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.hello(name = {first.name: "Michael"}) }}{% endmacro %}""")

        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            jscompiler.generateClosure, node, self.env, "f.html", "f.html")

    def test_call_macro12_special_for_loop_variables(self):
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro hello(index) -%}Hello, {{ index }}{% endmacro %}

{% macro testcall(menus) %}{% for menu in menus %}{{ xxx.ns1.hello(index = loop.index0) }}{% endfor %}{% endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

xxx.ns1.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('Hello, ', opt_data.index);
    if (!opt_sb) return output.toString();
};

xxx.ns1.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    var menuList = opt_data.menus;
    var menuListLen = menuList.length;
    for (var menuIndex = 0; menuIndex < menuListLen; menuIndex++) {
        var menuData = menuList[menuIndex];
        xxx.ns1.hello({index: menuIndex}, output);
    }
    if (!opt_sb) return output.toString();
};""")

    def test_callblock1(self):
        node = self.get_compile_from_string("""{% namespace tests %}
{% macro render_dialog(type) -%}
<div class="type">{{ caller() }}</div>
{%- endmacro %}

{% macro render(name) -%}
{% call tests.render_dialog(type = 'box') -%}
Hello {{ name }}!
{%- endcall %}
{%- endmacro %}
""")

        source_code = jscompiler.generateClosure(
            node, self.env, "cb.html", "cb.html")

        self.assertEqual(source_code, """goog.provide('tests');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

tests.render_dialog = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('<div class="type">');
    opt_caller({}, output);
    output.append('</div>');
    if (!opt_sb) return output.toString();
};

tests.render = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    func_caller = function(func_data, func_sb, func_caller) {
        var output = func_sb || new goog.string.StringBuffer();
        output.append('Hello ', opt_data.name, '!');
        if (!func_sb) return output.toString();
    };
    tests.render_dialog({type: 'box'}, output, func_caller);
    if (!opt_sb) return output.toString();
};""")

    def test_callblock2(self):
        node = self.get_compile_from_string("""{% macro list_users(users) -%}
<ul>
{% for user in users %}
<li>{{ caller(user = user) }}</li>
{% endfor %}
</ul>
{%- endmacro %}

{% macro users(users) -%}
{% call(user) list_users(users = users) -%}
Hello, {{ user }}!
{%- endcall %}
{%- endmacro %}
""")

        source_code = jscompiler.generateClosure(
            node, self.env, "cb.html", "cb.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
list_users = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('<ul>\\n');
    var userList = opt_data.users;
    var userListLen = userList.length;
    for (var userIndex = 0; userIndex < userListLen; userIndex++) {
        var userData = userList[userIndex];
        output.append('\\n<li>');
        opt_caller({user: userData}, output);
        output.append('</li>\\n');
    }
    output.append('\\n</ul>');
    if (!opt_sb) return output.toString();
};

users = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    func_caller = function(func_data, func_sb, func_caller) {
        var output = func_sb || new goog.string.StringBuffer();
        output.append('Hello, ', func_data.user, '!');
        if (!func_sb) return output.toString();
    };
    list_users({users: opt_data.users}, output, func_caller);
    if (!opt_sb) return output.toString();
};""")

    def test_callblock3(self):
        node = self.get_compile_from_string("""{% macro list_users(users) -%}
<ul>
{% for user in users %}
<li>{{ caller(user = user) }}</li>
{% endfor %}
</ul>
{%- endmacro %}

{% macro users(name, users, users2) -%}
{% call(user) list_users(users = users) -%}
Hello, {{ user }}!
{%- endcall %}
{% call(user) list_users(users = users2) -%}
Goodbye, {{ user }} from {{ name }}!
{%- endcall %}
{%- endmacro %}
""")

        source_code = jscompiler.generateClosure(
            node, self.env, "cb.html", "cb.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
list_users = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('<ul>\\n');
    var userList = opt_data.users;
    var userListLen = userList.length;
    for (var userIndex = 0; userIndex < userListLen; userIndex++) {
        var userData = userList[userIndex];
        output.append('\\n<li>');
        opt_caller({user: userData}, output);
        output.append('</li>\\n');
    }
    output.append('\\n</ul>');
    if (!opt_sb) return output.toString();
};

users = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    func_caller = function(func_data, func_sb, func_caller) {
        var output = func_sb || new goog.string.StringBuffer();
        output.append('Hello, ', func_data.user, '!');
        if (!func_sb) return output.toString();
    };
    list_users({users: opt_data.users}, output, func_caller);
    output.append('\\n');
    func_caller = function(func_data, func_sb, func_caller) {
        var output = func_sb || new goog.string.StringBuffer();
        output.append('Goodbye, ', func_data.user, ' from ', opt_data.name, '!');
        if (!func_sb) return output.toString();
    };
    list_users({users: opt_data.users2}, output, func_caller);
    if (!opt_sb) return output.toString();
};""")

    def test_callblock4(self):
        #
        node = self.get_compile_from_string("""{% macro list_users(users) -%}
<ul>
{% for user in users %}
<li>{{ caller() }}</li>
{% endfor %}
</ul>
{%- endmacro %}

{% macro users(name, users, users2) -%}
{% call(user = 'Anonymous') list_users(users = users) -%}
Hello, {{ user }}!
{%- endcall %}
{%- endmacro %}
""")

        source_code = jscompiler.generateClosure(
            node, self.env, "cb.html", "cb.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
list_users = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('<ul>\\n');
    var userList = opt_data.users;
    var userListLen = userList.length;
    for (var userIndex = 0; userIndex < userListLen; userIndex++) {
        var userData = userList[userIndex];
        output.append('\\n<li>');
        opt_caller({}, output);
        output.append('</li>\\n');
    }
    output.append('\\n</ul>');
    if (!opt_sb) return output.toString();
};

users = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    func_caller = function(func_data, func_sb, func_caller) {
        var defaults = {user: 'Anonymous'};
        for (var key in defaults) {
            if (!(key in func_data)) {
                func_data[key] = defaults[key];
            }
        }
        var output = func_sb || new goog.string.StringBuffer();
        output.append('Hello, ', func_data.user, '!');
        if (!func_sb) return output.toString();
    };
    list_users({users: opt_data.users}, output, func_caller);
    if (!opt_sb) return output.toString();
};""")

    def test_strip_html_whitespace(self):
        self.env.strip_html_whitespace = True

        node = self.get_compile_from_string("""// A comment

{% macro test_html(name, link) %}
    <h1>
        <a href="{{ link }}">
            {{ name }}
        </a>
    </h1>
{% endmacro %}
""")

        source_code = jscompiler.generateClosure(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
// A comment

test_html = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('<h1><a href="', opt_data.link, '">', opt_data.name, '</a></h1>');
    if (!opt_sb) return output.toString();
};""")

    def test_add_compiler_annotations(self):
        self.env.add_compiler_annotations = True

        node = self.get_compile_from_string("""// A comment

{% macro test_annotations(arg) %}{{ arg }}{% endmacro %}
""")

        source_code = jscompiler.generateClosure(
            node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
// A comment

/**
 * @param {Object.<string, *>=} opt_data
 * @param {goog.string.StringBuffer=} opt_sb
 * @param {Function=} opt_caller
 * @return {string|undefined}
 * @notypecheck
 */
test_annotations = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(opt_data.arg);
    if (!opt_sb) return output.toString();
};""")

    def test_recursive_macros_with_namespace(self):
        node = self.get_compile_from_string("""// A comment
{% namespace jinja2js %}
{% macro test_macro(item) %}
    <li>
        {{ item.title }}
        {% if item.children %}
            <ul>
                {% for child in item.children %}
                    {{ test_macro(child) }}
                {% endfor %}
            </ul>
        {% endif %}
    </li>
{% endmacro %}
""")

        source_code = jscompiler.generateClosure(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.provide('jinja2js');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');
// A comment

jinja2js.test_macro = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n    <li>\\n        ', opt_data.item.title, '\\n        ');
    if (opt_data.item.children) {
        output.append('\\n            <ul>\\n                ');
        var childList = opt_data.item.children;
        var childListLen = childList.length;
        for (var childIndex = 0; childIndex < childListLen; childIndex++) {
            var childData = childList[childIndex];
            output.append('\\n                    ', jinja2js.test_macro(childData), '\\n                ');
        }
        output.append('\\n            </ul>\\n        ');
    }
    output.append('\\n    </li>\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_calling_other_macros_with_implied_namespace(self):
        node = self.get_compile_from_string("""// A comment
{% namespace jinja2js %}
{% macro test_macro(item) %}
    <li>
        {{ item.title }}
        {% if item.related %}
            {{ test_related(item.related) }}
        {% endif %}
    </li>
{% endmacro %}
{% macro test_related(related) %}
    {{ related.name }}
{% endmacro %}
""")

        source_code = jscompiler.generateClosure(
            node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.provide('jinja2js');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');
// A comment

jinja2js.test_macro = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n    <li>\\n        ', opt_data.item.title, '\\n        ');
    if (opt_data.item.related) {
        output.append('\\n            ', jinja2js.test_related(opt_data.item.related), '\\n        ');
    }
    output.append('\\n    </li>\\n');
    if (!opt_sb) return output.toString();
};
jinja2js.test_related = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\n    ', opt_data.related.name, '\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_indentation_customization(self):
        self.env.js_indentation = '  '

        node = self.get_compile_from_string("""// A comment
{% macro test_indent(arg) %}<h1>Test</h1>{% endmacro %}
""")

        source_code = jscompiler.generateClosure(
            node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
// A comment
test_indent = function(opt_data, opt_sb, opt_caller) {
  var output = opt_sb || new goog.string.StringBuffer();
  output.append('<h1>Test</h1>');
  if (!opt_sb) return output.toString();
};""")

    def test_import1(self):
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% import 'test_import.jinja2' as forms %}

{% macro hello(name) %}{{ forms.input(name = 'test') }}{% endmacro %}""")

        source_code = jscompiler.generateClosure(
            node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');

goog.require('test.ns1');

xxx.ns1.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    test.ns1.input({name: 'test'}, output);
    if (!opt_sb) return output.toString();
};""")

    def test_filters1(self):
        # calling undefined filter
        node = self.get_compile_from_string("""{% macro filtertest(data) %}{{ data|missing_filter }}{% endmacro %}""")
        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            generateMacro, node, self.env, "filter.html", "filter.html")

    def test_filter_escape1(self):
        # escape filter
        node = self.get_compile_from_string("""{% macro filtertest(data) %}{{ data|escape }}{% endmacro %}""")
        source_code = generateMacro(node, self.env, "filter.html", "filter.html")

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(goog.string.htmlEscape(String(opt_data.data)));
    if (!opt_sb) return output.toString();
};""")

    def test_filter_escape2(self):
        # autoescape filter
        node = self.get_compile_from_string("""{% macro filtertest(data) %}{{ data }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "filter.html", "filter.html", autoescape = True)

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(goog.string.htmlEscape(String(opt_data.data)));
    if (!opt_sb) return output.toString();
};""")

    def test_filter_escape3(self):
        # autoescape with safe filter
        node = self.get_compile_from_string("""{% macro filtertest(data) %}{{ data|safe }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "filter.html", "filter.html", autoescape = True)

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(opt_data.data);
    if (!opt_sb) return output.toString();
};""")

    def test_filter_escape4(self):
        # autoescape with safe filter withg autoescape off
        node = self.get_compile_from_string("""{% macro filtertest(data) %}{{ data|safe }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "filter.html", "filter.html", autoescape = False)

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(opt_data.data);
    if (!opt_sb) return output.toString();
};""")

    def test_filter_default1(self):
        node = self.get_compile_from_string("""{% macro hello(name) %}{{ name|default('World') }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append((opt_data.name ? opt_data.name : 'World'));
    if (!opt_sb) return output.toString();
};""")

    def test_filter_default2(self):
        # same as previous but test keyword arguments to filters.
        node = self.get_compile_from_string("""{% macro hello(name) %}{{ name|default(default_value = 'World') }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append((opt_data.name ? opt_data.name : 'World'));
    if (!opt_sb) return output.toString();
};""")

    def test_filter_truncate1(self):
        node = self.get_compile_from_string("""{% macro trunc(s) %}{{ s|truncate(length = 280) }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.trunc = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(opt_data.s.substring(0, 280));
    if (!opt_sb) return output.toString();
};""")

    def test_filter_capitalize(self):
        # different in concat and stringbuilder modes
        node = self.get_compile_from_string("""{% macro trunc(s) %}{{ s|capitalize }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.trunc = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(opt_data.s.substring(0, 1).toUpperCase(), opt_data.s.substring(1));
    if (!opt_sb) return output.toString();
};""")

    def test_filter_round1(self):
        node = self.get_compile_from_string("""{% macro round(num) %}{{ num|round }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.round = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(Math.round(opt_data.num));
    if (!opt_sb) return output.toString();
};""")

    def test_filter_round2(self):
        node = self.get_compile_from_string("""{% macro round(num) %}{{ num|round(precision = 2) }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.round = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(Math.round(opt_data.num * 100) / 100);
    if (!opt_sb) return output.toString();
};""")

    def test_filter_round3(self):
        node = self.get_compile_from_string("""{% macro round(num, prec) %}{{ num|round(precision = prec) }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.round = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(Math.round(opt_data.num * Math.pow(10, opt_data.prec)) / Math.pow(10, opt_data.prec));
    if (!opt_sb) return output.toString();
};""")

    def test_filter_round4(self):
        node = self.get_compile_from_string("""{% macro round(num) %}{{ num|round(precision = 0) }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.round = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append(Math.round(opt_data.num));
    if (!opt_sb) return output.toString();
};""")

    def test_filter_round5(self):
        node = self.get_compile_from_string("""{% macro round(num) %}{{ num|round(precision = 0, method = 'ceil') }}{% endmacro %}""")

        self.assertRaises(
            TypeError, generateMacro, node, self.env, "f.html", "f.html")


class JSConcatCompilerTemplateTestCase(JSCompilerTestCase):

    def setUp(self):
        super(JSConcatCompilerTemplateTestCase, self).setUp()

        self.env = environment.create_environment(
            packages = ["pwt.jinja2js:test_templates"],
            writer = "pwt.jinja2js.jscompiler.Concat",
            )

    def test_const1(self):
        node = self.get_compile_from_string("""{% namespace testns.consts %}
{% macro hello() -%}
Hello, world!
{%- endmacro %}""")
        source_code = jscompiler.generate(node, self.env, "const.html", "const.html")

        self.assertEqual(source_code, """if (typeof testns == 'undefined') { var testns = {}; }\nif (typeof testns.consts == 'undefined') { testns.consts = {}; }

testns.consts.hello = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    output += 'Hello, world!';
    return output;
};""")

    def test_var1(self):
        node = self.get_compile_from_string("""{% macro hello(name) %}
{{ name }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var1.html", "var1.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    output += '\\n' + opt_data.name + '\\n';
    return output;
};""")

    def test_for13(self):
        # XXX - test for loop for conflicting variables. Here we have a
        # namespaced variable that gets required but conflicts with the
        # variable inside the loop that we created. If this is a problem
        # I will fix it, but it probable won't
        node = self.get_compile_from_string("""{% namespace test %}{% macro forinlist(jobs) -%}
{% for job in jobs %}{{ job.name }} does {{ jobData.name }}{% endfor %}
{%- endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """if (typeof test == 'undefined') { var test = {}; }
test.forinlist = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    var jobList = opt_data.jobs;
    var jobListLen = jobList.length;
    for (var jobIndex = 0; jobIndex < jobListLen; jobIndex++) {
        var jobData = jobList[jobIndex];
        output += jobData.name + ' does ' + jobData.name;
    }
    return output;
};""")

    def test_call_macro1(self):
        # call macro in same template, without arguments.
        node = self.get_compile_from_string("""{% namespace xxx %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}{{ xxx.testif() }}{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """if (typeof xxx == 'undefined') { var xxx = {}; }

xxx.testif = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    if (opt_data.option) {
        output += opt_data.option;
    }
    return output;
};

xxx.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    output += xxx.testif({});
    return output;
};""")

    def test_call_macro3(self): # Copied from above and modified
        # call macro passing in a argument
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.testif(option = true) }}{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """if (typeof xxx == 'undefined') { var xxx = {}; }
if (typeof xxx.ns1 == 'undefined') { xxx.ns1 = {}; }

xxx.ns1.testif = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    if (opt_data.option) {
        output += opt_data.option;
    }
    return output;
};

xxx.ns1.testcall = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    output += xxx.ns1.testif({option: true});
    return output;
};""")

    def test_callblock1(self):
        node = self.get_compile_from_string("""{% namespace tests %}
{% macro render_dialog(type) -%}
<div class="type">{{ caller() }}</div>
{%- endmacro %}

{% macro render(name) -%}
{% call tests.render_dialog(type = 'box') -%}
Hello {{ name }}!
{%- endcall %}
{%- endmacro %}
""")

        source_code = jscompiler.generate(node, self.env, "cb.html", "cb.html")

        self.assertEqual(source_code, """if (typeof tests == \'undefined\') { var tests = {}; }

tests.render_dialog = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    output += '<div class="type">' + opt_caller({}) + '</div>';
    return output;
};

tests.render = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    func_caller = function(func_data, func_sb, func_caller) {
        var output = '';
        output += 'Hello ' + opt_data.name + '!';
        return output;
    };
    output += tests.render_dialog({type: 'box'}, null, func_caller);
    return output;
};""")

    def test_filter_capitalize(self):
        # different in concat and stringbuilder modes
        node = self.get_compile_from_string("""{% macro trunc(s) %}{{ s|capitalize }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.trunc = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    output += opt_data.s.substring(0, 1).toUpperCase() + opt_data.s.substring(1);
    return output;
};""")

    def test_condexpr1(self):
        # test if
        node = self.get_compile_from_string("""{% macro testif(option) %}{{ option if option }}hello{% endmacro %}""")

        source_code = generateMacro(node, self.env, "condexpr.html", "condexpr.html")

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    output += (opt_data.option ? opt_data.option : '') + 'hello';
    return output;
};""")


class JSCompilerTemplateTestCaseOutput(JSCompilerTestCase):
    # Test the standard output so that if a developer needs to debug the
    # output then we can add comments and other information, keep the ordering
    # so that it is easier to do so.

    def test_comments1(self):
        node = self.get_compile_from_string("""/**
* This prints out hello world!
*/
{% macro hello() %}
Hello, world!
{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
/**
* This prints out hello world!
*/
hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\nHello, world!\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_comments_containing_variables(self):
        # Make sure that any comments in the template get output in a
        # consistent manner
        node = self.get_compile_from_string("""// This prints out hello {{ name }}!

{% macro hello(name) %}
Hello, {{ name }}!
{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
// This prints out hello !

hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\nHello, ', opt_data.name, '!\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_comments2(self):
        node = self.get_compile_from_string("""/**
 * This prints out hello world!
 */
{% macro hello(name) %}
Hello, {{ name.firstname }}!
{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
/**
 * This prints out hello world!
 */
hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\nHello, ', opt_data.name.firstname, '!\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_comments3(self):
        node = self.get_compile_from_string("""// ok
{% import 'test_import.jinja2' as forms %}
// ok 2
/**
 * This prints out hello world!
 */
{% macro hello(name) %}
Hello, {{ name.firstname }}!
{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
// ok
goog.require('test.ns1');
// ok 2
/**
 * This prints out hello world!
 */
hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\nHello, ', opt_data.name.firstname, '!\\n');
    if (!opt_sb) return output.toString();
};""")

    def test_comments4(self):
        # same as previous but put in new lines into templates.
        node = self.get_compile_from_string("""// ok

{% import 'test_import.jinja2' as forms %}

// ok 2

/**
 * This prints out hello world!
 */
{% macro hello(name) %}
Hello, {{ name.firstname }}!
{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('goog.string');
goog.require('goog.string.StringBuffer');
// ok

goog.require('test.ns1');

// ok 2

/**
 * This prints out hello world!
 */
hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\nHello, ', opt_data.name.firstname, '!\\n');
    if (!opt_sb) return output.toString();
};""")


class JSCompilerTemplateTestCaseOptimized(JSCompilerTemplateTestCase):
    # Test template output after passing it through Jinja2's optimizer.

    def get_compile_from_string(self, source, name = None, filename = None):
        node = super(JSCompilerTemplateTestCaseOptimized, self).get_compile_from_string(source, name, filename)
        node = jinja2.optimizer.optimize(node, self.env)

        return node


class JSCompilerTemplateTestCase(JSCompilerTemplateTestCase):

    def setUp(self):
        super(JSCompilerTemplateTestCase, self).setUp()

        self.env = jinja2.environment.Environment(
            extensions = ["pwt.jinja2js.jscompiler.Namespace"],
            loader = jinja2.PackageLoader("pwt.jinja2js", "test_templates")
            )


class JSConcatCompilerTemplateTestCaseOptimized(JSConcatCompilerTemplateTestCase):
    # Test template output after passing it through Jinja2's optimizer.

    def get_compile_from_string(self, source, name = None, filename = None):
        node = super(JSConcatCompilerTemplateTestCaseOptimized, self).get_compile_from_string(source, name, filename)
        node = jinja2.optimizer.optimize(node, self.env)

        return node


class SoyServer(unittest.TestCase):

    def get_app(self):
        return webtest.TestApp(
            wsgi.Resources(packages = "pwt.jinja2js:test_templates")
            )

    def test_soy1(self):
        app = self.get_app()
        self.assertRaises(webtest.AppError, app.get, "/missing.soy")

    def test_soy2(self):
        app = self.get_app()
        res = app.get("/example.jinja2")

    def test_concat_soy1(self):
        app = webtest.TestApp(
            wsgi.ConcatResources(packages = "pwt.jinja2js:test_templates")
            )
        res = app.get("/example.jinja2")

        self.assertEqual(res.body, """if (typeof example == 'undefined') { var example = {}; }


example.hello = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    output += '\\nHello, ' + opt_data.name + '!\\n';
    return output;
};""")

    def test_closure_soy1(self):
        app = webtest.TestApp(
            wsgi.ClosureResources(packages = "pwt.jinja2js:test_templates")
            )
        res = app.get("/example.jinja2")

        self.assertEqual(res.body, """goog.provide('example');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');


example.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\nHello, ', opt_data.name, '!\\n');
    if (!opt_sb) return output.toString();
};""")


class RealSoyServer(unittest.TestCase):

    def get_app(self):
        return webtest.TestApp(
            wsgi.Resources(
                packages = "pwt.jinja2js")
            )

    def test_soy1(self):
        app = self.get_app()
        res = app.get("/variables.jinja2")

    def test_soy2(self):
        app = self.get_app()
        res = app.get("/autoescaped.jinja2")


class CLInterfaceTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_cli1(self):
        output = StringIO()
        result = cli.main([], output)
        self.assertEqual(result, 1)

        self.assertEqual(os.listdir(self.tempdir), [])

    def test_cli2(self):
        output = StringIO()
        result = cli.main(["--outputPathFormat", "${INPUT_FILE_NAME_NO_EXT}.js"], output)
        self.assertEqual(result, 0)

        self.assertEqual(os.listdir(self.tempdir), [])

    def test_cli3(self):
        output = StringIO()
        result = cli.main([
            "--outputPathFormat", "%s/${INPUT_FILE_NAME_NO_EXT}.js" % self.tempdir,
            "%s/test_templates/example.jinja2" %(
                os.path.dirname(jscompiler.__file__))
            ], output)
        self.assertEqual(result, 0)

        self.assertEqual(os.listdir(self.tempdir), ["example.js"])

        self.assertEqual(
            open(os.path.join(self.tempdir, "example.js")).read(),
            """if (typeof example == 'undefined') { var example = {}; }


example.hello = function(opt_data, opt_sb, opt_caller) {
    var output = '';
    output += '\\nHello, ' + opt_data.name + '!\\n';
    return output;
};""")

    def test_cli4(self):
        # test using a different code style
        output = StringIO()
        result = cli.main([
            "--outputPathFormat", "%s/${INPUT_FILE_NAME_NO_EXT}.js" % self.tempdir,
            "--codeStyle", "stringbuilder",
            "%s/test_templates/example.jinja2" %(
                os.path.dirname(jscompiler.__file__))
            ], output)
        self.assertEqual(result, 0)

        self.assertEqual(os.listdir(self.tempdir), ["example.js"])

        self.assertEqual(
            open(os.path.join(self.tempdir, "example.js")).read(),
            """goog.provide('example');
goog.require('goog.string');
goog.require('goog.string.StringBuffer');


example.hello = function(opt_data, opt_sb, opt_caller) {
    var output = opt_sb || new goog.string.StringBuffer();
    output.append('\\nHello, ', opt_data.name, '!\\n');
    if (!opt_sb) return output.toString();
};""")

    # test the generation of different filenames

    def test_output1(self):
        self.assertEqual(
            cli.get_output_filename(
                "/tmp/${INPUT_FILE_NAME_NO_EXT}.js",
                "test.soy"),
            "/tmp/test.js")

    def test_output2(self):
        self.assertEqual(
            cli.get_output_filename(
                "/builddir/${INPUT_DIRECTORY}/${INPUT_FILE_NAME_NO_EXT}.js",
                "test.soy"),
            "/builddir//test.js")

    def test_output3(self):
        self.assertEqual(
            cli.get_output_filename(
                "/builddir/${INPUT_DIRECTORY}/${INPUT_FILE_NAME_NO_EXT}.js",
                "src/test.soy"),
            "/builddir/src/test.js")

    def test_output4(self):
        self.assertEqual(
            cli.get_output_filename(
                "/builddir/${INPUT_FILE_NAME_NO_EXT}.js",
                "src/test.soy"),
            "/builddir/test.js")

    def test_output5(self):
        self.assertEqual(
            cli.get_output_filename(
                "/builddir/${INPUT_FILE_NAME}.js",
                "src/test.soy"),
            "/builddir/test.soy.js")


class TestJinja2JSFunctionalTestSetup(unittest.TestCase):
    # Test that we haven't broken the application that serves the Java Script
    # test suite for pwt.jinja2js

    def test_testsuite_works1(self):
        jsapp = webtest.TestApp(
            app.main(
                packages = "pwt.jinja2js",
                )
            )

        self.assertEqual(jsapp.get("/").status_int, 200)


class RecipeTestCase(unittest.TestCase):

    def setUp(self):
        base = tempfile.mkdtemp("buildoutSetUp")
        self.base = os.path.realpath(base)

        self.cwd = os.getcwd()

    def tearDown(self):
        rmtree(self.base)

        os.chdir(self.cwd)

    def test_recipe(self):
        base = os.path.join(self.base, "_TEST_")
        os.mkdir(base)

        sample = base

        deggs = os.path.join(sample, "develop-eggs")
        os.mkdir(deggs)

        closure = os.path.abspath(
            os.path.join(
                app.__file__, "..", "..", "..", "..", "checkouts", "closure"))

        zc.buildout.testing.install_develop("setuptools", deggs)
        zc.buildout.testing.install_develop("zc.buildout", deggs)
        zc.buildout.testing.install_develop("pwt.jinja2js", deggs)
        zc.buildout.testing.install_develop("pwt.closure", deggs)
        zc.buildout.testing.install_develop("Jinja2", deggs)
        zc.buildout.testing.install_develop("WebOb", deggs)

        os.mkdir(os.path.join(sample, "media"))

        os.mkdir(os.path.join(sample, "soy"))
        open(os.path.join(sample, "soy", "test.jinja2"), "w").write("""
{% namespace app %}

{% macro hello(name) %}Hello {{ name }}{% endmacro %}
""")

        open(os.path.join(sample, "buildout.cfg"), "w").write("""
[buildout]
parts = deps.js

[deps.js]
recipe = pwt.jinja2js:dependency
paths =
    %(here)s/goog
    %(sample)s/media
    %(sample)s/soy

deps_js = %(sample)s/media/deps.js
""" % {"sample": sample, "here": os.path.dirname(app.__file__)})

        os.chdir(sample)
        config = [
            ("buildout", "log-level", "WARNING"),
            # trick bootstrap into putting the buildout develop egg
            # in the eggs dir.
            ("buildout", "develop-eggs-directory", deggs),
            ("buildout", "offline", "true"),
            ("buildout", "newest", "false"),
            ("buildout", "unzip", "true"),
            ]
        zc.buildout.buildout.Buildout(
            "buildout.cfg", config, user_defaults=False,
            ).bootstrap([])

        buildout = os.path.join(sample, "bin", "buildout")
        os.system(buildout)

        self.assertEqual(
            open(os.path.join(sample, "media", "deps.js")).read(),
            """goog.addDependency('base.js', ['goog'], []);
goog.addDependency('test.jinja2', ['app'], ['goog.string', 'goog.string.StringBuffer']);
""")

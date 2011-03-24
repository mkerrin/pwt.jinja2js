from cStringIO import StringIO
import os
import shutil
import tempfile
import unittest
import webtest

import soy_wsgi

import jinja2.compiler
import jinja2.nodes
import jinja2.optimizer
import jinja2.runtime

import jscompiler
import cli


def generateMacro(
        node, environment, name, filename, autoescape = False):
    generator = jscompiler.MacroCodeGenerator(environment, None, None)
    eval_ctx = jinja2.nodes.EvalContext(environment, name)
    eval_ctx.namespace = "test"
    eval_ctx.autoescape = autoescape
    generator.blockvisit(node.body, jscompiler.JSFrame(environment, eval_ctx))
    return generator.stream.getvalue()


class JSCompilerTestCase(unittest.TestCase):

    def setUp(self):
        super(JSCompilerTestCase, self).setUp()

        self.loader = jinja2.PackageLoader("pwt.jinja2js", "test_templates")
        self.env = jinja2.Environment(
            loader = self.loader,
            extensions = ["pwt.jinja2js.jscompiler.Namespace"],
            )

    def get_compile_from_string(self, source, name = None, filename = None):
        node = self.env._parse(source, name, filename)
        # node = jinja2.optimizer.optimize(node, self.env)

        return node


class JSCompilerTemplateTestCase(JSCompilerTestCase):

    def test_missing_namespace1(self):
        node = self.get_compile_from_string("""{% macro hello() %}
Hello, world!
{% endmacro %}""")
        source_code = jscompiler.generate(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('soy');
hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, world!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_const1(self):
        node = self.get_compile_from_string("""{% macro hello() %}
Hello, world!
{% endmacro %}""")
        source_code = generateMacro(node, self.env, "const.html", "const.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, world!\\n');
    if (!opt_sb) return output.toString();
}""")

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
        # variable is undeclared
        node = self.get_compile_from_string("""{% namespace test %}
{% macro hello() %}
{{ goog.color.names.aqua }}
{% endmacro %}
""")
        source_code = jscompiler.generate(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.provide('test');
goog.require('soy');


goog.require('goog.color.names');
test.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', goog.color.names.aqua, '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var1(self):
        node = self.get_compile_from_string("""{% macro hello(name) %}
{{ name }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var1.html", "var1.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', opt_data.name, '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var2(self):
        node = self.get_compile_from_string("""{% macro helloName(name) %}
Hello, {{ name }}!
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.helloName = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, ', opt_data.name, '!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var3(self):
        # variables with numerical addition
        node = self.get_compile_from_string("""{% macro add(num) %}
{{ num + 200 }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', (opt_data.num + 200), '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var4(self):
        # variables with numerical addition to variable
        node = self.get_compile_from_string("""{% macro add(num, step) %}
{{ num + step }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', (opt_data.num + opt_data.step), '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var5(self):
        # variables minus, power of, 
        node = self.get_compile_from_string("""{% macro add(num, step) %}
{{ (num - step) ** 2 }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', Math.pow((opt_data.num - opt_data.step), 2), '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var6(self):
        # variables floor division
        node = self.get_compile_from_string("""{% macro fd(n1, n2) %}
{{ Math.floor(n1 / n2) }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', Math.floor((opt_data.num / opt_data.step)), '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var6(self):
        # variables minus, power of, 
        node = self.get_compile_from_string("""{% macro add(num, step) %}
{{ num - (step ** 2) }}
{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html")

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', (opt_data.num - Math.pow(opt_data.step, 2)), '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var7(self):
        # variables + with autoescape on
        node = self.get_compile_from_string("""{% macro add(num, step) %}{{ num - (step ** 2) }}{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html", autoescape = True)

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml((opt_data.num - Math.pow(opt_data.step, 2))));
    if (!opt_sb) return output.toString();
}""")

    def test_var8(self):
        # variables + with autoescape and the escape filter
        node = self.get_compile_from_string("""{% macro add(num, step) %}{{ (num - (step ** 2)) | escape }}{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html", autoescape = True)

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml((opt_data.num - Math.pow(opt_data.step, 2))));
    if (!opt_sb) return output.toString();
}""")

    def test_var9(self):
        # variables -
        node = self.get_compile_from_string("""{% macro add(num) %}{{ -num + 20 }}{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html", autoescape = True)

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml(((-opt_data.num) + 20)));
    if (!opt_sb) return output.toString();
}""")

    def test_var10(self):
        # variables +
        node = self.get_compile_from_string("""{% macro add(num) %}{{ +num + 20 }}{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html", autoescape = True)

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml(((+opt_data.num) + 20)));
    if (!opt_sb) return output.toString();
}""")

    def test_var11(self):
        # variables not
        node = self.get_compile_from_string("""{% macro add(bool) %}{{ not bool }}{% endmacro %}
""")
        source_code = generateMacro(node, self.env, "var2.html", "var2.html", autoescape = True)

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml((!opt_data.bool)));
    if (!opt_sb) return output.toString();
}""")

    def test_for1(self):
        # test for loop
        node = self.get_compile_from_string("""{% namespace xxx %}
{% macro fortest(data) %}
{% for item in data %}
  Item {{ item }}.
{% else %}
  No items.
{% endfor %}
{% endmacro %}
""")
        source_code = jscompiler.generate(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');

xxx.fortest = function(opt_data, opt_sb) {
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

    def test_for2(self):
        # test loop.index0 variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.index0 }}{% endfor %}{% endmacro %}")
        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for3(self):
        # test loop.index variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.index }}{% endfor %}{% endmacro %}")
        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex + 1);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for4(self):
        # test loop.revindex & loop.revindex0 variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.revindex }} - {{loop.revindex0 }}{% endfor %}{% endmacro %}")
        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemListLen - itemIndex - 1, ' - ', itemListLen - itemIndex);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for5(self):
        # test loop.length & loop.first & loop.last variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.length }} - {{loop.first }} - {{ loop.last }}{% endfor %}{% endmacro %}")
        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemListLen, ' - ', itemIndex == 0, ' - ', itemIndex == (itemListLen - 1));
    }
    if (!opt_sb) return output.toString();
}""")

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

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex + 1, ' - ', opt_data.name);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for8(self):
        # test loop.index with other variable, with attribute
        node = self.get_compile_from_string("{% macro fortest(data, param) %}{% for item in data %}{{ loop.index }} - {{ param.name }}{% endfor %}{% endmacro %}")
        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex + 1, ' - ', opt_data.param.name);
    }
    if (!opt_sb) return output.toString();
}""")

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

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
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
}""")

    def test_for10(self):
        # test for in list loop
        node = self.get_compile_from_string("""{% macro forinlist(jobs) %}
{% for job in [1, 2, 3] %}
   {{ job }}
{% endfor %}
{% endmacro %}""")

        source_code = generateMacro(node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """test.forinlist = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n');
    var jobList = [1, 2, 3];
    var jobListLen = jobList.length;
    for (var jobIndex = 0; jobIndex < jobListLen; jobIndex++) {
        var jobData = jobList[jobIndex];
        output.append('\\n   ', jobData, '\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_for11(self):
        # test for loop not producing extra namespace requirements
        node = self.get_compile_from_string("""{% namespace test %}{% macro forinlist(jobs) %}
{% for job in jobs %}{{ job.name }}{% endfor %}
{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('test');
goog.require('soy');
test.forinlist = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n');
    var jobList = opt_data.jobs;
    var jobListLen = jobList.length;
    for (var jobIndex = 0; jobIndex < jobListLen; jobIndex++) {
        var jobData = jobList[jobIndex];
        output.append(jobData.name);
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_if1(self):
        # test if
        node = self.get_compile_from_string("""{% macro testif(option) %}{% if option %}{{ option }}{% endif %}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "if.html", "if.html")

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}""")

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

        self.assertEqual(source_code, """test.iftest = function(opt_data, opt_sb) {
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

    def test_if3(self):
        # test if ==
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num == 0 %}{{ num }}{% endif %}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "if.html", "if.html")

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.num == 0) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_if4(self):
        # test if == and !=
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num != 0 and num == 2 %}{{ num }}{% endif %}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "if.html", "if.html")

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if ((opt_data.num != 0 && opt_data.num == 2)) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_if5(self):
        # test if > and >= and < and <=
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num > 0 and num >= 1 and num < 2 and num <= 3 %}{{ num }}{% endif %}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "if.html", "if.html")

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if ((((opt_data.num > 0 && opt_data.num >= 1) && opt_data.num < 2) && opt_data.num <= 3)) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
}""")

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

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if ((opt_data.num + 1) == 2) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro1(self):
        # call macro in same template, without arguments.
        node = self.get_compile_from_string("""{% namespace xxx %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}{{ xxx.testif() }}{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');

xxx.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}

xxx.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.testif({}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro2(self):
        # call macro in same template where the namespace contains
        # multiple dotted names.
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.testif() }}{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');

xxx.ns1.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}

xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.ns1.testif({}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro3(self):
        # call macro passing in a argument
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.testif(option = true) }}{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');

xxx.ns1.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}

xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.ns1.testif({option: true}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro4(self):
        # call macro passing parament, with extra output
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}Hello, {{ xxx.ns1.testif(option = true) }}!{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, ".html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');

xxx.ns1.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}

xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('Hello, ');
    xxx.ns1.testif({option: true}, output);
    output.append('!');
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro5(self):
        # call macro with positional arguments
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}
{% macro testcall() %}Hello, {{ xxx.ns1.testif(true) }}!{% endmacro %}""")

        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            jscompiler.generate, node, self.env, "", "")

    def test_call_macro6(self):
        # call macro with dynamic keywrod arguments
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}Hello, {{ xxx.ns1.testif(**{option: true}) }}!{% endmacro %}""")

        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            jscompiler.generate, node, self.env, "", "")

    def test_call_macro7(self):
        # call macro with string keyword
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro hello(name) -%}
Hello, {% if name %}{{ name }}{% else %}world{% endif %}!{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.hello(name = "Michael") }}{% endmacro %}""")

        source_code = jscompiler.generate(
            node, self.env, "for.html", "for.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');

xxx.ns1.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('Hello, ');
    if (opt_data.name) {
        output.append(opt_data.name);
    } else {
        output.append('world');
    }
    output.append('!');
    if (!opt_sb) return output.toString();
}

xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.ns1.hello({name: 'Michael'}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro8(self):
        # call macro with parameter sub
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro hello(name) -%}
Hello, {% if name %}{{ name.first }}{% else %}world{% endif %}!{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.hello(name = {"first": "Michael"}) }}{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');

xxx.ns1.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('Hello, ');
    if (opt_data.name) {
        output.append(opt_data.name.first);
    } else {
        output.append('world');
    }
    output.append('!');
    if (!opt_sb) return output.toString();
}

xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.ns1.hello({name: {'first': 'Michael'}}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_import1(self):
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% import 'test_import.soy' as forms %}

{% macro hello(name) %}{{ forms.input(name = 'test') }}{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');

goog.require('test.ns1');

xxx.ns1.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    test.ns1.input({name: 'test'}, output);
    if (!opt_sb) return output.toString();
}""")

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

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml(opt_data.data));
    if (!opt_sb) return output.toString();
}""")

    def test_filter_escape2(self):
        # autoescape filter
        node = self.get_compile_from_string("""{% macro filtertest(data) %}{{ data }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "filter.html", "filter.html", autoescape = True)

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml(opt_data.data));
    if (!opt_sb) return output.toString();
}""")

    def test_filter_escape3(self):
        # autoescape with safe filter
        node = self.get_compile_from_string("""{% macro filtertest(data) %}{{ data|safe }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "filter.html", "filter.html", autoescape = True)

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(opt_data.data);
    if (!opt_sb) return output.toString();
}""")

    def test_filter_default1(self):
        node = self.get_compile_from_string("""{% macro hello(name) %}{{ name|default('World') }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(opt_data.name ? opt_data.name : 'World');
    if (!opt_sb) return output.toString();
}""")

    def test_filter_default2(self):
        # same as previous but test keyword arguments to filters.
        node = self.get_compile_from_string("""{% macro hello(name) %}{{ name|default(default_value = 'World') }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(opt_data.name ? opt_data.name : 'World');
    if (!opt_sb) return output.toString();
}""")

    def test_filter_truncate1(self):
        node = self.get_compile_from_string("""{% macro trunc(s) %}{{ s|truncate(length = 280) }}{% endmacro %}""")

        source_code = generateMacro(node, self.env, "f.html", "f.html")

        self.assertEqual(source_code, """test.trunc = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(opt_data.s.substring(0, 280));
    if (!opt_sb) return output.toString();
}""")


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

        self.assertEqual(source_code, """goog.require('soy');
/**
* This prints out hello world!
*/
hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, world!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_comments2(self):
        node = self.get_compile_from_string("""/**
 * This prints out hello world!
 */
{% macro hello(name) %}
Hello, {{ name.firstname }}!
{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('soy');
/**
 * This prints out hello world!
 */
hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, ', opt_data.name.firstname, '!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_comments3(self):
        node = self.get_compile_from_string("""// ok
{% import 'test_import.soy' as forms %}
// ok 2
/**
 * This prints out hello world!
 */
{% macro hello(name) %}
Hello, {{ name.firstname }}!
{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('soy');
// ok
goog.require('test.ns1');
// ok 2
/**
 * This prints out hello world!
 */
hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, ', opt_data.name.firstname, '!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_comments4(self):
        # same as previous but put in new lines into templates.
        node = self.get_compile_from_string("""// ok

{% import 'test_import.soy' as forms %}

// ok 2

/**
 * This prints out hello world!
 */
{% macro hello(name) %}
Hello, {{ name.firstname }}!
{% endmacro %}""")

        source_code = jscompiler.generate(node, self.env, "v.html", "v.html")

        self.assertEqual(source_code, """goog.require('soy');
// ok

goog.require('test.ns1');

// ok 2

/**
 * This prints out hello world!
 */
hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, ', opt_data.name.firstname, '!\\n');
    if (!opt_sb) return output.toString();
}""")


class JSCompilerTemplateTestCaseOptimized(JSCompilerTemplateTestCase):

    def get_compile_from_string(self, source, name = None, filename = None):
        node = super(JSCompilerTemplateTestCaseOptimized, self).get_compile_from_string(source, name, filename)
        node = jinja2.optimizer.optimize(node, self.env)

        return node


class SoyServer(unittest.TestCase):

    def get_app(self):
        return webtest.TestApp(
            soy_wsgi.Resources(
                url = "/soy/", packages = "pwt.jinja2js:test_templates"))

    def test_soy1(self):
        app = self.get_app()
        self.assertRaises(webtest.AppError, app.get, "/soy/missing.soy")

    def test_soy2(self):
        app = self.get_app()
        res = app.get("/soy/example.soy")


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
            "%s/test_templates/example.soy" % os.path.dirname(jscompiler.__file__)
            ], output)
        self.assertEqual(result, 0)

        self.assertEqual(os.listdir(self.tempdir), ["example.js"])

        self.assertEqual(
            open(os.path.join(self.tempdir, "example.js")).read(),
            """goog.provide('example');
goog.require('soy');


example.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, ', opt_data.name, '!\\n');
    if (!opt_sb) return output.toString();
}""")

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

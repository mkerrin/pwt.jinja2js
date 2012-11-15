goog.provide("runtests");

// We don't want to require the test templates when we are trying to test
// the concat version. So set a flag when we manually include all the
// test templates
if (typeof DONT_REQUIRE_TEST_TEMPLATES != 'undefined' &&
        DONT_REQUIRE_TEST_TEMPLATES) {
    goog.require("tests.variables");
    goog.require("tests.iftest");
    goog.require("tests.fortest");
    goog.require("tests.call");
    goog.require("tests.importtest");
    goog.require("tests.autoescaped");
    goog.require("tests.filters");
}

goog.require("goog.testing.TestCase");
goog.require("goog.testing.TestRunner");

// Manually setup the testcase and tests so that we can compile the tests
// with the closure compiler and test the output from the templates when we
// are compiled to a single file.
window.onload = function() {
    var testcase = new goog.testing.TestCase("variables.jinja2");

    testcase.add(new goog.testing.TestCase.Test("constvar", function() {
        assertEquals("Hello", tests.variables.constvar({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("var1", function() {
        assertEquals("Hello Michael", tests.variables.var1({name: "Michael"}));
    }));

    testcase.add(new goog.testing.TestCase.Test("var2_objectaccess", function() {
        assertEquals(
            "Hello Michael",
            tests.variables.var2_objectaccess({
                obj: {
                    "namevar": "Michael" // key needs to be quoted to work in compiled mode
                },
                name: "namevar"}));
    }));

    testcase.add(new goog.testing.TestCase.Test("var2_objectaccess2", function() {
        assertEquals(
            "Hello Michael",
            tests.variables.var2_objectaccess2({
                obj: {
                    "namevar": "Michael" // key needs to be quoted to work in compiled mode
                }}));
    }));

    testcase.add(new goog.testing.TestCase.Test("numadd1", function() {
        assertEquals("20", tests.variables.add1({num: 10}));
        assertEquals("30", tests.variables.add1({num: 20}));
    }))

    testcase.add(new goog.testing.TestCase.Test("numadd2", function() {
        assertEquals("14", tests.variables.add2({num: 10, step: 4}));
    }));

    testcase.add(new goog.testing.TestCase.Test("numsub1", function() {
        assertEquals("6", tests.variables.sub1({num: 10, step: 4}));
    }));

    testcase.add(new goog.testing.TestCase.Test("div1", function() {
        assertEquals("2", tests.variables.div1({num: 10, step: 5}));
        assertEquals("2.25", tests.variables.div1({num: 9, step: 4}));
    }));

    testcase.add(new goog.testing.TestCase.Test("floordiv1", function() {
        assertEquals("1", tests.variables.floordiv1({n1: 3, n2: 2}));
        assertEquals("3", tests.variables.floordiv1({n1: 19, n2: 5}));
    }));

    testcase.add(new goog.testing.TestCase.Test("pow1", function() {
        assertEquals("8", tests.variables.pow1({num: 2, power: 3}));
    }));

    testcase.add(new goog.testing.TestCase.Test("mod1", function() {
        assertEquals("1", tests.variables.mod1({n1: 3, n2: 2}));
        assertEquals("4", tests.variables.mod1({n1: 9, n2: 5}));
    }));

    testcase.add(new goog.testing.TestCase.Test("ordering1", function() {
        // (3 + 2) ** 2
        assertEquals("25", tests.variables.order1({n1: 3, n2: 2}));
        // 3 + (2 ** 2)
        assertEquals("7", tests.variables.order2({n1: 3, n2: 2}));
        // 7 + 3 * 4
        assertEquals("19", tests.variables.order3({n1: 7, n2: 3, n3: 4}));
        // (7 + 3) * 4
        assertEquals("40", tests.variables.order4({n1: 7, n2: 3, n3: 4}));
    }));

    testcase.add(new goog.testing.TestCase.Test("unaryminus1", function() {
        assertEquals("5", tests.variables.unaryminus1({num: 10}));
        assertEquals("10", tests.variables.unaryminus1({num: 5}));
    }));

    testcase.add(new goog.testing.TestCase.Test("unaryminus2", function() {
        assertEquals("25", tests.variables.unaryminus2({num: 10}));
        assertEquals("20", tests.variables.unaryminus2({num: 5}));
    }));

    testcase.add(new goog.testing.TestCase.Test("unarynot", function() {
        assertEquals("false", tests.variables.unarynot({bool: 1}));
        assertEquals("true", tests.variables.unarynot({bool: 0}));
    }));

    testcase.add(new goog.testing.TestCase.Test("defaultparam1", function() {
        assertEquals("Hello World!", tests.variables.defaultparam1({}));
        assertEquals("Hello Michael!", tests.variables.defaultparam1({name: "Michael"}));
    }));

    testcase.add(new goog.testing.TestCase.Test("defaultparam2", function() {
        assertEquals("Null", tests.variables.defaultparam2({}));
        assertEquals("Not null", tests.variables.defaultparam2({option: ""}));
        assertEquals("Null", tests.variables.defaultparam2({option: null}));
    }));

    testcase.add(new goog.testing.TestCase.Test("defaultparam3", function() {
        assertEquals("Hello Michael aged 30", tests.variables.defaultparam3({}));
        assertEquals("Hello Aengus aged 30", tests.variables.defaultparam3({name: "Aengus"}));
        assertEquals("Hello Aengus aged 25", tests.variables.defaultparam3({name: "Aengus", age: 25}));
    }));

    testcase.add(new goog.testing.TestCase.Test("assignment1", function() {
        assertEquals("1", tests.variables.assignment1());
    }));

    // QUnit.module("if.jinja2");

    // test with option
    testcase.add(new goog.testing.TestCase.Test("basicif", function() {
        assertEquals("No option set.", tests.iftest.basicif({}));
        assertEquals("No option set.", tests.iftest.basicif({option: false}));
        assertEquals("Option set.", tests.iftest.basicif({option: true}));
    }));

    // test with option.data
    testcase.add(new goog.testing.TestCase.Test("basicif2", function() {
        // undefined error as option is not passed into the if
        assertThrows(function() { tests.iftest.basicif2({}) });

        assertEquals("No option data set.", tests.iftest.basicif2({option: true}));
        assertEquals("Option data set.", tests.iftest.basicif2({option: {data: true}}));
    }));

    testcase.add(new goog.testing.TestCase.Test("basicif3", function() {
        assertEquals("XXX", tests.iftest.basicif3({option: "XXX"}));
        assertEquals("true", tests.iftest.basicif3({option: true}));
        assertEquals("", tests.iftest.basicif3({option: false}));
    }));

    testcase.add(new goog.testing.TestCase.Test("ifand1", function() {
        assertEquals("", tests.iftest.ifand1({}));
        assertEquals("", tests.iftest.ifand1({option: true, option2: false}));
        assertEquals("", tests.iftest.ifand1({option: false, option2: true}));
        assertEquals("", tests.iftest.ifand1({option: false, option2: false}));
        assertEquals("Equal", tests.iftest.ifand1({option: true, option2: true}));
    }));

    testcase.add(new goog.testing.TestCase.Test("ifor1", function() {
        assertEquals("", tests.iftest.ifor1({}), "");
        assertEquals("Equal", tests.iftest.ifor1({option: true, option2: false}));
        assertEquals("Equal", tests.iftest.ifor1({option: false, option2: true}));
        assertEquals("", tests.iftest.ifor1({option: false, option2: false}));
        assertEquals("Equal", tests.iftest.ifor1({option: true, option2: true}));
    }));

    testcase.add(new goog.testing.TestCase.Test("ifequal", function() {
        assertEquals("", tests.iftest.ifequal1({}));
        assertEquals("Equal", tests.iftest.ifequal1({option: 1}));
        assertEquals("", tests.iftest.ifequal1({option: 2}));

        assertEquals("Equal", tests.iftest.ifequal2({}));
        assertEquals("Equal", tests.iftest.ifequal2({option: null}));
        assertEquals("", tests.iftest.ifequal2({option: 1}));
    }));

    testcase.add(new goog.testing.TestCase.Test("conditionalif1", function() {
        assertEquals("True cond", tests.iftest.ifconditional1({cond: true}));
        assertEquals("False cond", tests.iftest.ifconditional1({cond: false}));

        // defaults to false
        assertEquals("False cond", tests.iftest.ifconditional1({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("conditionalif2", function() {
        assertEquals("True cond", tests.iftest.ifconditional2({cond: true}));
        assertEquals("", tests.iftest.ifconditional2({cond: false}));
    }));

    testcase.add(new goog.testing.TestCase.Test("conditionalif3", function() {
        assertEquals(
            "True cond",
            tests.iftest.ifconditional3({cond: true, defaultmsg: 'No'}));
        assertEquals("No", tests.iftest.ifconditional3({cond: false, defaultmsg: 'No'}));

        // XXX - leaving the default message undefined results in a undefined
        // string. Is this the correct behaviour?
        assertEquals("undefined", tests.iftest.ifconditional3({cond: false}));
    }));

    testcase.add(new goog.testing.TestCase.Test("conditionalif4", function() {
        assertEquals(
            "True statement.",
            tests.iftest.ifconditional4({cond: true, defaultmsg: 'No'}));

        assertEquals("No statement.", tests.iftest.ifconditional4({cond: false, defaultmsg: 'No'}));
    }));

    // QUnit.module("for.jinja2");

    testcase.add(new goog.testing.TestCase.Test("for1", function() {
        assertEquals("123", tests.fortest.for1({data: [1, 2, 3]}));
        assertEquals("", tests.fortest.for1({data: []}));
        assertThrows(function() { tests.fortest.for1({}); });
    }));

    testcase.add(new goog.testing.TestCase.Test("for2", function() {
        assertEquals("123", tests.fortest.for2({data: [1, 2, 3]}));
        assertEquals("Empty", tests.fortest.for2({data: []}));
    }))

    testcase.add(new goog.testing.TestCase.Test("forloop1", function() {
        assertEquals(
            "1 - 0<br/>2 - 1<br/>3 - 2<br/>",
            tests.fortest.forloop1({data: [5, 4, 3]})
        );
    }));

    testcase.add(new goog.testing.TestCase.Test("forloop2", function() {
        assertEquals(
            "Badge 1 Badge 2 Badge 3 Badge 1.1 Badge 2.1 ",
            tests.fortest.forloop2({
                jobs: [{badges: [{name: "Badge 1"}, {name: "Badge 2"}, {name: "Badge 3"}]},
                       {badges: [{name: "Badge 1.1"}, {name: "Badge 2.1"}]}
                      ]})
        );
    }));

    // QUnit.module("call macro");

    testcase.add(new goog.testing.TestCase.Test("call1", function() {
        assertEquals("I was called!", tests.call.call1({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("call2", function() {
        assertEquals("Michael was called!", tests.call.call2({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("call2_multipleArgs1", function() {
        assertEquals("Michael is 31!", tests.call.call_multipleArgs1({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("call2_specialvariables", function() {
        assertEquals(
            "012",
            tests.call.call_specialVariables({
                menus: ["one", "two", "three"]
            })
        );
    }));

    testcase.add(new goog.testing.TestCase.Test("call3", function() {
        assertEquals("Michael Kerrin", tests.call.call3({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("call_positional1", function() {
        assertEquals("Michael", tests.call.call_positional1({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("call_positional2", function() {
        assertEquals("Michael is 31", tests.call.call_positional2({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock1", function() {
        assertEquals('<div class="box">Hello, World!</div>', tests.call.render_dialog({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock2", function() {
        assertEquals(
            "<ul><li>Hello, User1!</li><li>Hello, User2!</li></ul>",
            tests.call.users({users: ["User1", "User2"]})
        );
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock3", function() {
        assertEquals(
            "<ul><li>Goodbye, User1!</li><li>Goodbye, User2!</li></ul>",
            tests.call.users2({users: ["User1", "User2"]})
        );
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock4", function() {
        assertEquals(
            "<ul><li>Hello User1!</li></ul><ul><li>Goodbye Joe from Me!</li></ul>",
            tests.call.users3({name: "Me", users: ["User1"], users_old: ["Joe"]})
        );
    }));

    // check default values

    testcase.add(new goog.testing.TestCase.Test("callblock5", function() {
        assertEquals(
            "<ul><li>Hi User1 from Me!</li></ul>",
            tests.call.users4({name: "Me", users: ["User1"]})
        );
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock5b", function() {
        assertEquals(
            "<ul><li>Hi User1 from Michael!</li></ul>",
            tests.call.users4({users: ["User1"]})
        );
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock6", function() {
        assertEquals(
            "<ul><li>Hi User1 from Michael!</li></ul>",
            tests.call.users5({users: ["User1"]})
        );

        // This template skips the user Michael 
        assertEquals(
            "<ul><li>Hi Anonymous from Michael!</li></ul>",
            tests.call.users5({users: ["Michael"]})
        );
        assertEquals(
            "<ul><li>Hi Michael2 from Michael!</li></ul>",
            tests.call.users5({users: ["Michael2"]})
        );
    }));

    // QUnit.module("import macros");

    testcase.add(new goog.testing.TestCase.Test("import1", function() {
        assertEquals("Hello, Michael!", tests.importtest.testcall({}));
    }));

    // QUnit.module("autoescape");

    testcase.add(new goog.testing.TestCase.Test("autoescapeoff", function() {
        assertEquals(
            "Hello <b>Michael</b>",
            tests.variables.var1({name: "<b>Michael</b>"})
        );
    }));

    testcase.add(new goog.testing.TestCase.Test("autoescapeon", function() {
        assertEquals(
            "Hello &lt;b&gt;Michael&lt;/b&gt;",
            tests.autoescaped.var1({name: "<b>Michael</b>"})
        );
    }));

    testcase.add(new goog.testing.TestCase.Test("autoescape safe", function() {
        assertEquals(
            "Hello <b>Michael</b>",
            tests.autoescaped.var2({name: "<b>Michael</b>"})
        );
    }));

    // QUnit.module("filters");

    testcase.add(new goog.testing.TestCase.Test("default1", function() {
        assertEquals("Hello, World", tests.filters.default1({}));
        assertEquals(
            "Hello, Michael",
            tests.filters.default1({name: "Michael"})
        );
    }));

    testcase.add(new goog.testing.TestCase.Test("truncate1", function() {
        assertEquals(
            "xxxxx",
            tests.filters.truncate1({s: "xxxxxxxxxx", length: 5})
        );
        assertEquals(
            "xxxxxxxxxx",
            tests.filters.truncate1({s: "xxxxxxxxxx", length: 20})
        );
    }));

    testcase.add(new goog.testing.TestCase.Test("capitalize", function() {
        assertEquals("Hello", tests.filters.capitalize({s: "hello"}));
        assertEquals("Hello", tests.filters.capitalize({s: "Hello"}));
        assertEquals("HELLO", tests.filters.capitalize({s: "HELLO"}));
    }));

    testcase.add(new goog.testing.TestCase.Test("last", function() {
        assertEquals("3", tests.filters.last({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("length", function() {
        assertEquals("4", tests.filters.len({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("replace1", function() {
        assertEquals("Goodbye World", tests.filters.replace1({}));
    }));

    testcase.add(new goog.testing.TestCase.Test("round1", function() {
        assertEquals("6", tests.filters.round1({num: 5.66, precision: 0}));
        assertEquals("5", tests.filters.round1({num: 5.49, precision: 0}));
    }));

    testcase.add(new goog.testing.TestCase.Test("round1 - precision", function() {
        assertEquals("5.66", tests.filters.round1({num: 5.66, precision: 2}));
        assertEquals("5.49", tests.filters.round1({num: 5.49, precision: 2}));
    }));

    // run the tests
    var tr = new goog.testing.TestRunner();
    tr.initialize(testcase);
    tr.execute();
};

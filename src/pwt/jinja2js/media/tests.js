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
    var testcase = new goog.testing.TestCase("variables.soy");

    testcase.add(new goog.testing.TestCase.Test("constvar", function() {
        assertEquals(tests.variables.constvar({}), "Hello");
    }));

    testcase.add(new goog.testing.TestCase.Test("var1", function() {
        assertEquals(tests.variables.var1({name: "Michael"}), "Hello Michael");
    }));

    testcase.add(new goog.testing.TestCase.Test("numadd1", function() {
        assertEquals(tests.variables.add1({num: 10}), "20");
        assertEquals(tests.variables.add1({num: 20}), "30");
    }))

    testcase.add(new goog.testing.TestCase.Test("numadd2", function() {
        assertEquals(tests.variables.add2({num: 10, step: 4}), "14");
    }));

    testcase.add(new goog.testing.TestCase.Test("numsub1", function() {
        assertEquals(tests.variables.sub1({num: 10, step: 4}), "6");
    }));

    testcase.add(new goog.testing.TestCase.Test("div1", function() {
        assertEquals(tests.variables.div1({num: 10, step: 5}), "2");
        assertEquals(tests.variables.div1({num: 9, step: 4}), "2.25");
    }));

    testcase.add(new goog.testing.TestCase.Test("floordiv1", function() {
        assertEquals(tests.variables.floordiv1({n1: 3, n2: 2}), "1");
        assertEquals(tests.variables.floordiv1({n1: 19, n2: 5}), "3");
    }));

    testcase.add(new goog.testing.TestCase.Test("pow1", function() {
        assertEquals(tests.variables.pow1({num: 2, power: 3}), "8");
    }));

    testcase.add(new goog.testing.TestCase.Test("mod1", function() {
        assertEquals(tests.variables.mod1({n1: 3, n2: 2}), "1");
        assertEquals(tests.variables.mod1({n1: 9, n2: 5}), "4");
    }));

    testcase.add(new goog.testing.TestCase.Test("ordering1", function() {
        // (3 + 2) ** 2
        assertEquals(tests.variables.order1({n1: 3, n2: 2}), "25");
        // 3 + (2 ** 2)
        assertEquals(tests.variables.order2({n1: 3, n2: 2}), "7");
        // 7 + 3 * 4
        assertEquals(tests.variables.order3({n1: 7, n2: 3, n3: 4}), "19");
        // (7 + 3) * 4
        assertEquals(tests.variables.order4({n1: 7, n2: 3, n3: 4}), "40");
    }));

    testcase.add(new goog.testing.TestCase.Test("unaryminus1", function() {
        assertEquals(tests.variables.unaryminus1({num: 10}), "5");
        assertEquals(tests.variables.unaryminus1({num: 5}), "10");
    }));

    testcase.add(new goog.testing.TestCase.Test("unaryminus2", function() {
        assertEquals(tests.variables.unaryminus2({num: 10}), "25");
        assertEquals(tests.variables.unaryminus2({num: 5}), "20");
    }));

    testcase.add(new goog.testing.TestCase.Test("unarynot", function() {
        assertEquals(tests.variables.unarynot({bool: 1}), "false");
        assertEquals(tests.variables.unarynot({bool: 0}), "true");
    }));

    testcase.add(new goog.testing.TestCase.Test("defaultparam1", function() {
        assertEquals(tests.variables.defaultparam1({}), "Hello World!");
        assertEquals(tests.variables.defaultparam1({name: "Michael"}), "Hello Michael!");
    }));

    testcase.add(new goog.testing.TestCase.Test("defaultparam2", function() {
        assertEquals(tests.variables.defaultparam2({}), "Null");
        assertEquals(tests.variables.defaultparam2({option: ""}), "Not null");
        assertEquals(tests.variables.defaultparam2({option: null}), "Null");
    }));

    testcase.add(new goog.testing.TestCase.Test("defaultparam3", function() {
        assertEquals(tests.variables.defaultparam3({}), "Hello Michael aged 30");
        assertEquals(tests.variables.defaultparam3({name: "Aengus"}), "Hello Aengus aged 30");
        assertEquals(tests.variables.defaultparam3({name: "Aengus", age: 25}), "Hello Aengus aged 25");
    }));

    // QUnit.module("if.soy");

    // test with option
    testcase.add(new goog.testing.TestCase.Test("basicif", function() {
        assertEquals(tests.iftest.basicif({}), "No option set.");
        assertEquals(tests.iftest.basicif({option: false}), "No option set.");
        assertEquals(tests.iftest.basicif({option: true}), "Option set.");
    }));

    // test with option.data
    testcase.add(new goog.testing.TestCase.Test("basicif2", function() {
        // undefined error as option is not passed into the if
        assertThrows(function() { tests.iftest.basicif2({}) });

        assertEquals(tests.iftest.basicif2({option: true}), "No option data set.");
        assertEquals(tests.iftest.basicif2({option: {data: true}}), "Option data set.");
    }));

    testcase.add(new goog.testing.TestCase.Test("basicif3", function() {
        assertEquals(tests.iftest.basicif3({option: "XXX"}), "XXX");
        assertEquals(tests.iftest.basicif3({option: true}), "true");
        assertEquals(tests.iftest.basicif3({option: false}), "");
    }));

    testcase.add(new goog.testing.TestCase.Test("ifand1", function() {
        assertEquals(tests.iftest.ifand1({}), "");
        assertEquals(tests.iftest.ifand1({option: true, option2: false}), "");
        assertEquals(tests.iftest.ifand1({option: false, option2: true}), "");
        assertEquals(tests.iftest.ifand1({option: false, option2: false}), "");
        assertEquals(tests.iftest.ifand1({option: true, option2: true}), "Equal");
    }));

    testcase.add(new goog.testing.TestCase.Test("ifor1", function() {
        assertEquals(tests.iftest.ifor1({}), "");
        assertEquals(tests.iftest.ifor1({option: true, option2: false}), "Equal");
        assertEquals(tests.iftest.ifor1({option: false, option2: true}), "Equal");
        assertEquals(tests.iftest.ifor1({option: false, option2: false}), "");
        assertEquals(tests.iftest.ifor1({option: true, option2: true}), "Equal");
    }));

    testcase.add(new goog.testing.TestCase.Test("ifequal", function() {
        assertEquals(tests.iftest.ifequal1({}), "");
        assertEquals(tests.iftest.ifequal1({option: 1}), "Equal");
        assertEquals(tests.iftest.ifequal1({option: 2}), "");

        assertEquals(tests.iftest.ifequal2({}), "Equal");
        assertEquals(tests.iftest.ifequal2({option: null}), "Equal");
        assertEquals(tests.iftest.ifequal2({option: 1}), "");
    }));

    // QUnit.module("for.soy");

    testcase.add(new goog.testing.TestCase.Test("for1", function() {
        assertEquals(tests.fortest.for1({data: [1, 2, 3]}), "123");
        assertEquals(tests.fortest.for1({data: []}), "");
        assertThrows(function() { tests.fortest.for1({}); });
    }));

    testcase.add(new goog.testing.TestCase.Test("for2", function() {
        assertEquals(tests.fortest.for2({data: [1, 2, 3]}), "123");
        assertEquals(tests.fortest.for2({data: []}), "Empty");
    }))

    testcase.add(new goog.testing.TestCase.Test("forloop1", function() {
        assertEquals(tests.fortest.forloop1({data: [5, 4, 3]}), "1 - 0<br/>2 - 1<br/>3 - 2<br/>");
    }));

    testcase.add(new goog.testing.TestCase.Test("forloop2", function() {
        assertEquals(tests.fortest.forloop2({
            jobs: [{badges: [{name: "Badge 1"}, {name: "Badge 2"}, {name: "Badge 3"}]},
                   {badges: [{name: "Badge 1.1"}, {name: "Badge 2.1"}]}
                  ]}), "Badge 1 Badge 2 Badge 3 Badge 1.1 Badge 2.1 ");
    }));

    // QUnit.module("call macro");

    testcase.add(new goog.testing.TestCase.Test("call1", function() {
        assertEquals(tests.call.call1({}), "I was called!");
    }));

    testcase.add(new goog.testing.TestCase.Test("call2", function() {
        assertEquals(tests.call.call2({}), "Michael was called!");
    }));

    testcase.add(new goog.testing.TestCase.Test("call3", function() {
        assertEquals(tests.call.call3({}), "Michael Kerrin");
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock1", function() {
        assertEquals(tests.call.render_dialog({}), '<div class="box">Hello, World!</div>');
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock2", function() {
        assertEquals(tests.call.users({users: ["User1", "User2"]}), "<ul><li>Hello, User1!</li><li>Hello, User2!</li></ul>");
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock3", function() {
        assertEquals(tests.call.users2({users: ["User1", "User2"]}), "<ul><li>Goodbye, User1!</li><li>Goodbye, User2!</li></ul>");
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock4", function() {
        assertEquals(tests.call.users3({name: "Me", users: ["User1"], users_old: ["Joe"]}), "<ul><li>Hello User1!</li></ul><ul><li>Goodbye Joe from Me!</li></ul>");
    }));

    // check default values

    testcase.add(new goog.testing.TestCase.Test("callblock5", function() {
        assertEquals(tests.call.users4({name: "Me", users: ["User1"]}), "<ul><li>Hi User1 from Me!</li></ul>");
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock5b", function() {
        assertEquals(tests.call.users4({users: ["User1"]}), "<ul><li>Hi User1 from Michael!</li></ul>");
    }));

    testcase.add(new goog.testing.TestCase.Test("callblock6", function() {
        assertEquals(tests.call.users5({users: ["User1"]}), "<ul><li>Hi User1 from Michael!</li></ul>");

        // This template skips the user Michael 
        assertEquals(tests.call.users5({users: ["Michael"]}), "<ul><li>Hi Anonymous from Michael!</li></ul>");
        assertEquals(tests.call.users5({users: ["Michael2"]}), "<ul><li>Hi Michael2 from Michael!</li></ul>");
    }));

    // QUnit.module("import macros");

    testcase.add(new goog.testing.TestCase.Test("import1", function() {
        assertEquals(tests.importtest.testcall({}), "Hello, Michael!");
    }));

    // QUnit.module("autoescape");

    testcase.add(new goog.testing.TestCase.Test("autoescapeoff", function() {
        assertEquals(tests.variables.var1({name: "<b>Michael</b>"}), "Hello <b>Michael</b>");
    }));

    testcase.add(new goog.testing.TestCase.Test("autoescapeon", function() {
        assertEquals(tests.autoescaped.var1({name: "<b>Michael</b>"}), "Hello &lt;b&gt;Michael&lt;/b&gt;");
    }));

    testcase.add(new goog.testing.TestCase.Test("autoescape safe", function() {
        assertEquals(tests.autoescaped.var2({name: "<b>Michael</b>"}), "Hello <b>Michael</b>");
    }));

    // QUnit.module("filters");

    testcase.add(new goog.testing.TestCase.Test("default1", function() {
        assertEquals(tests.filters.default1({}), "Hello, World");
        assertEquals(tests.filters.default1({name: "Michael"}), "Hello, Michael");
    }));

    testcase.add(new goog.testing.TestCase.Test("truncate1", function() {
        assertEquals(tests.filters.truncate1({s: "xxxxxxxxxx", length: 5}), "xxxxx");
        assertEquals(tests.filters.truncate1({s: "xxxxxxxxxx", length: 20}), "xxxxxxxxxx");
    }));

    testcase.add(new goog.testing.TestCase.Test("capitalize", function() {
        assertEquals(tests.filters.capitalize({s: "hello"}), "Hello");
        assertEquals(tests.filters.capitalize({s: "Hello"}), "Hello");
        assertEquals(tests.filters.capitalize({s: "HELLO"}), "HELLO");
    }));

    testcase.add(new goog.testing.TestCase.Test("last", function() {
        assertEquals(tests.filters.last({}), "3");
    }));

    testcase.add(new goog.testing.TestCase.Test("length", function() {
        assertEquals(tests.filters.len({}), "4");
    }));

    testcase.add(new goog.testing.TestCase.Test("replace1", function() {
        assertEquals(tests.filters.replace1({}), "Goodbye World");
    }));

    testcase.add(new goog.testing.TestCase.Test("round1", function() {
        assertEquals(tests.filters.round1({num: 5.66, precision: 0}), "6");
        assertEquals(tests.filters.round1({num: 5.49, precision: 0}), "5");
    }));

    testcase.add(new goog.testing.TestCase.Test("round1 - precision", function() {
        assertEquals(tests.filters.round1({num: 5.66, precision: 2}), "5.66");
        assertEquals(tests.filters.round1({num: 5.49, precision: 2}), "5.49");
    }));

    // run the tests
    var tr = new goog.testing.TestRunner();
    tr.initialize(testcase);
    tr.execute();
};

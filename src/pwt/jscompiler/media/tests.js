goog.provide("tests");

goog.require("tests.variables");
goog.require("tests.iftest");
goog.require("tests.fortest");
goog.require("tests.call");
goog.require("tests.importtest");

window.onload = function() {
    QUnit.module("variables.soy");

    QUnit.test("constvar", function() {
            QUnit.equal(tests.variables.constvar({}), "Hello");
        });

    QUnit.test("var1", function() {
            QUnit.equal(tests.variables.var1({name: "Michael"}), "Hello Michael");
        });

    QUnit.test("numadd1", function() {
            QUnit.equal(tests.variables.add1({num: 10}), "20");
            QUnit.equal(tests.variables.add1({num: 20}), "30");
        });

    QUnit.test("numadd2", function() {
            QUnit.equal(tests.variables.add2({num: 10, step: 4}), "14");
        });

    QUnit.test("numsub1", function() {
            QUnit.equal(tests.variables.sub1({num: 10, step: 4}), "6");
        });

    QUnit.test("div1", function() {
            QUnit.equal(tests.variables.div1({num: 10, step: 5}), "2");
            QUnit.equal(tests.variables.div1({num: 9, step: 4}), "2.25");
        });    

    QUnit.test("floordiv1", function() {
            QUnit.equal(tests.variables.floordiv1({n1: 3, n2: 2}), "1");
            QUnit.equal(tests.variables.floordiv1({n1: 19, n2: 5}), "3");
        });

    QUnit.test("pow1", function() {
            QUnit.equal(tests.variables.pow1({num: 2, power: 3}), "8");
        });

    QUnit.test("mod1", function() {
            QUnit.equal(tests.variables.mod1({n1: 3, n2: 2}), "1");
            QUnit.equal(tests.variables.mod1({n1: 9, n2: 5}), "4");
        });

    QUnit.test("ordering1", function() {
            // (3 + 2) ** 2
            QUnit.equal(tests.variables.order1({n1: 3, n2: 2}), "25");
            // 3 + (2 ** 2)
            QUnit.equal(tests.variables.order2({n1: 3, n2: 2}), "7");
            // 7 + 3 * 4
            QUnit.equal(tests.variables.order3({n1: 7, n2: 3, n3: 4}), "19");
            // (7 + 3) * 4
            QUnit.equal(tests.variables.order4({n1: 7, n2: 3, n3: 4}), "40");
        });

    QUnit.module("if.soy");

    // test with option
    QUnit.test("basicif", function() {
            QUnit.equal(tests.iftest.basicif({}), "No option set.");
            QUnit.equal(tests.iftest.basicif({option: false}), "No option set.");
            QUnit.equal(tests.iftest.basicif({option: true}), "Option set.");
        });

    // test with option.data
    QUnit.test("basicif2", function() {
            // undefined error as option is not passed into the if
            QUnit.raises(function() { tests.iftest.basicif2({}) });

            QUnit.equal(tests.iftest.basicif2({option: true}), "No option data set.");
            QUnit.equal(tests.iftest.basicif2({option: {data: true}}), "Option data set.");
        });

    QUnit.test("basicif3", function() {
            QUnit.equal(tests.iftest.basicif3({option: "XXX"}), "XXX");
            QUnit.equal(tests.iftest.basicif3({option: true}), "true");
            QUnit.equal(tests.iftest.basicif3({option: false}), "");
        });

    QUnit.test("ifand1", function() {
            QUnit.equal(tests.iftest.ifand1({}), "");
            QUnit.equal(tests.iftest.ifand1({option: true, option2: false}), "");
            QUnit.equal(tests.iftest.ifand1({option: false, option2: true}), "");
            QUnit.equal(tests.iftest.ifand1({option: false, option2: false}), "");
            QUnit.equal(tests.iftest.ifand1({option: true, option2: true}), "Equal");
        });

    QUnit.test("ifor1", function() {
            QUnit.equal(tests.iftest.ifor1({}), "");
            QUnit.equal(tests.iftest.ifor1({option: true, option2: false}), "Equal");
            QUnit.equal(tests.iftest.ifor1({option: false, option2: true}), "Equal");
            QUnit.equal(tests.iftest.ifor1({option: false, option2: false}), "");
            QUnit.equal(tests.iftest.ifor1({option: true, option2: true}), "Equal");
        });

    QUnit.test("ifequal", function() {
            QUnit.equal(tests.iftest.ifequal1({}), "");
            QUnit.equal(tests.iftest.ifequal1({option: 1}), "Equal");
            QUnit.equal(tests.iftest.ifequal1({option: 2}), "");

            QUnit.equal(tests.iftest.ifequal2({}), "Equal");
            QUnit.equal(tests.iftest.ifequal2({option: null}), "Equal");
            QUnit.equal(tests.iftest.ifequal2({option: 1}), "");
        });

    QUnit.module("for.soy");

    QUnit.test("for1", function() {
            QUnit.equal(tests.fortest.for1({data: [1, 2, 3]}), "123");
            QUnit.equal(tests.fortest.for1({data: []}), "");
            QUnit.raises(function() { tests.fortest.for1({}); });
        });

    QUnit.test("for2", function() {
            QUnit.equal(tests.fortest.for2({data: [1, 2, 3]}), "123");
            QUnit.equal(tests.fortest.for2({data: []}), "Empty");
        });

    QUnit.test("forloop1", function() {
            QUnit.equal(tests.fortest.forloop1({data: [5, 4, 3]}), "1 - 0<br/>2 - 1<br/>3 - 2<br/>");
        });

    QUnit.test("forloop2", function() {
            QUnit.equal(tests.fortest.forloop2({
                        jobs: [{badges: [{name: "Badge 1"}, {name: "Badge 2"}, {name: "Badge 3"}]},
                               {badges: [{name: "Badge 1.1"}, {name: "Badge 2.1"}]}
                               ]}), "Badge 1 Badge 2 Badge 3 Badge 1.1 Badge 2.1 ");
        });

    QUnit.module("call macro");

    QUnit.test("call1", function() {
            QUnit.equal(tests.call.call1({}), "I was called!");
        });

    QUnit.test("call2", function() {
            QUnit.equal(tests.call.call2({}), "Michael was called!");
        });

    QUnit.test("call3", function() {
            QUnit.equal(tests.call.call3({}), "Michael Kerrin");
        });

    QUnit.module("import macros");

    QUnit.test("import1", function() {
            QUnit.equal(tests.importtest.testcall({}), "Hello, Michael!");
        });
};

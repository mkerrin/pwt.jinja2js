goog.provide("tests");

goog.require("tests.iftest");
goog.require("tests.fortest");
goog.require("tests.call");
goog.require("tests.importtest");

$(document).ready(function() {
        module("if.soy");

        // test with option
        test("basicif", function() {
                equals(tests.iftest.basicif({}), "No option set.");
                equals(tests.iftest.basicif({option: false}), "No option set.");
                equals(tests.iftest.basicif({option: true}), "Option set.");
            });

        // test with option.data
        test("basicif2", function() {
                // undefined error as option is not passed into the if
                raises(function() { tests.iftest.basicif2({}) });

                equals(tests.iftest.basicif2({option: true}), "No option data set.");
                equals(tests.iftest.basicif2({option: {data: true}}), "Option data set.");
            });

        test("basicif3", function() {
                equals(tests.iftest.basicif3({option: "XXX"}), "XXX");
                equals(tests.iftest.basicif3({option: true}), "true");
                equals(tests.iftest.basicif3({option: false}), "");
            });

        test("ifand1", function() {
                equals(tests.iftest.ifand1({}), "");
                equals(tests.iftest.ifand1({option: true, option2: false}), "");
                equals(tests.iftest.ifand1({option: false, option2: true}), "");
                equals(tests.iftest.ifand1({option: false, option2: false}), "");
                equals(tests.iftest.ifand1({option: true, option2: true}), "Equal");
            });

        test("ifor1", function() {
                equals(tests.iftest.ifor1({}), "");
                equals(tests.iftest.ifor1({option: true, option2: false}), "Equal");
                equals(tests.iftest.ifor1({option: false, option2: true}), "Equal");
                equals(tests.iftest.ifor1({option: false, option2: false}), "");
                equals(tests.iftest.ifor1({option: true, option2: true}), "Equal");
            });

        test("ifequal", function() {
                equals(tests.iftest.ifequal1({}), "");
                equals(tests.iftest.ifequal1({option: 1}), "Equal");
                equals(tests.iftest.ifequal1({option: 2}), "");

                equals(tests.iftest.ifequal2({}), "Equal");
                equals(tests.iftest.ifequal2({option: null}), "Equal");
                equals(tests.iftest.ifequal2({option: 1}), "");
            });

        module("for.soy");

        test("for1", function() {
                equals(tests.fortest.for1({data: [1, 2, 3]}), "123");
                equals(tests.fortest.for1({data: []}), "");
                raises(function() { tests.fortest.for1({}); });
            });

        test("for2", function() {
                equals(tests.fortest.for2({data: [1, 2, 3]}), "123");
                equals(tests.fortest.for2({data: []}), "Empty");
            });

        test("forloop1", function() {
                equals(tests.fortest.forloop1({data: [5, 4, 3]}), "1 - 0<br/>2 - 1<br/>3 - 2<br/>");
            });

        module("call macro");

        test("call1", function() {
                equals(tests.call.call1({}), "I was called!");
            });

        test("call2", function() {
                equals(tests.call.call2({}), "Michael was called!");
            });

        module("import macros");

        test("import1", function() {
                equals(tests.importtest.testcall({}), "Hello, Michael!");
            });
    });

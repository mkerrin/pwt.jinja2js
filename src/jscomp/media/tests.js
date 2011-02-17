// goog.require("");

goog.importScript_("/soy/if.soy");
goog.importScript_("/soy/for.soy");

$(document).ready(function() {
        module("if.soy");

        // test with option
        test("basicif", function() {
                equals(tests.if.basicif({}), "No option set.");
                equals(tests.if.basicif({option: false}), "No option set.");
                equals(tests.if.basicif({option: true}), "Option set.");
            });

        // test with option.data
        test("basicif2", function() {
                equals(tests.if.basicif2({}), "No option data set.");
                equals(tests.if.basicif2({option: true}), "No option data set.");
                equals(tests.if.basicif2({option: {data: true}}), "Option data set.");
            });

        test("basicif3", function() {
                equals(tests.if.basicif3({option: "XXX"}), "XXX");
                equals(tests.if.basicif3({option: true}), "true");
                equals(tests.if.basicif3({option: false}), "");
            });

        test("ifand1", function() {
                equals(tests.if.ifand1({}), "");
                equals(tests.if.ifand1({option: true, option2: false}), "");
                equals(tests.if.ifand1({option: false, option2: true}), "");
                equals(tests.if.ifand1({option: false, option2: false}), "");
                equals(tests.if.ifand1({option: true, option2: true}), "Equal");
            });

        test("ifor1", function() {
                equals(tests.if.ifor1({}), "");
                equals(tests.if.ifor1({option: true, option2: false}), "Equal");
                equals(tests.if.ifor1({option: false, option2: true}), "Equal");
                equals(tests.if.ifor1({option: false, option2: false}), "");
                equals(tests.if.ifor1({option: true, option2: true}), "Equal");
            });

        test("ifequal", function() {
                equals(tests.if.ifequal1({}), "");
                equals(tests.if.ifequal1({option: 1}), "Equal");
                equals(tests.if.ifequal1({option: 2}), "");

                equals(tests.if.ifequal2({}), "Equal");
                equals(tests.if.ifequal2({option: null}), "Equal");
                equals(tests.if.ifequal2({option: 1}), "");
            });

        module("for.soy");

        test("for1", function() {
                equals(tests.for.for1({data: [1, 2, 3]}), "123");
                equals(tests.for.for1({data: []}), "");
                raises(function() { tests.for.for1({}); });
            });

        test("for2", function() {
                equals(tests.for.for2({data: [1, 2, 3]}), "123");
                equals(tests.for.for2({data: []}), "Empty");
            });

        test("forloop1", function() {
                equals(tests.for.forloop1({data: [5, 4, 3]}), "1 - 0<br/>2 - 1<br/>3 - 2<br/>");
            });
    });

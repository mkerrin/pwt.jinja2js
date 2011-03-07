About
=====

This is an extension to the Jinja2 template engine to compile Jinja2 compatible
templates to JavaScript which can be served and used within a JavaScript heavy
web application. The generated JavaScript can also be minimized using your
favourite JavaScript compressor.

Install and test
================

In order to get started with this project and to see what it can do:

 * git clone git@github.com:mkerrin/pwt.jscompiler.git
 * cd pwt.jscompiler
 * python bootstrap
 * ./bin/buildout

Testing
=======

To run the tests run

 * ./bin/test -v

To run a basic server in order to run the JavaScript tests.

 * ./bin/serve --reload

To run the JavaScript tests open a browser and load the urls

 * http://localhost:8000/tests.html

 * http://localhost:8000/tests_compiled.html

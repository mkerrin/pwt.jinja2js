About
=====

This is an extension to the Jinja2 template engine to compile Jinja2 compatible
templates to JavaScript which can be served and used within a JavaScript heavy
web application. The generated JavaScript can also be minimized using your
favourite JavaScript compressor.

Install and test
================

In order to get started with this project and to see what it can do:

$ git clone git@github.com:mkerrin/pwt.jscompiler.git
$ cd pwt.jscompiler
$ python bootstrap
$ ./bin/buildout

At some point the build will break. Open the file
**eggs/Jinja2-2.5.5-py2.6.egg/jinja2/nodes.py** and comment out the last
line. This will fix this issue.

Testing
=======

To run the tests run

$ ./bin/test -v

To run a basic server in order to run the JavaScript tests.

$ ./bin/serve --reload

Then go to http://localhost:8000/ in your browser in order to run the JavaScript
tests.

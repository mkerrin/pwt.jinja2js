Usage
+++++

There are 3 different ways of including 


WSGI
====

pwt.jinja2js contains a WSGI middleware layer in
``pwt.jinja2js.wsgi.Resources`` that produces the output that can be used
to dynamically convert the templates to JavaScript. This is handy for
development where we can refresh the page to pull in any made to the template.

It can be referenced through any any `Paste Deployment`_ configuration via the
`egg:pwt.jinja2js`. paste.app_factory.

This WSGI application can take the following arguments:

 * `packages` - list of Python packages to find templates.

 * `autoescape` - (Default: False) boolean indicating whether to autoescape all variables in your templates.

 * `writer` - full Python class path to the class that writes the Java Script.

.. _Paste Deployment: http://pythonpaste.org/deploy/


Command line interface
======================

A console script, called ``jinja2js`` is distributed with the package. This is
a command line interface to the tool. It takes a list of filenames which it
compiles to JavaScript saving the output of it file to the filename generated
by the ``--outputPathFormat`` template.

The script is invoked like so::

    jinja2js [options] --outputPathFormat format <file1> <file2> ...

The list of arguments to the script are:

+--------------------+----------------------------------------------------+
| Argument           | Description                                        |
+====================+====================================================+
| --outputPathFormat | A format string that specifies how to build the    |
|                    | path to each output file. You can include literal  |
|                    | characters as well as the following $variables:    |
|                    | ${INPUT_FILE_NAME}, ${INPUT_FILE_NAME_NO_EXT}, and |
|                    | ${INPUT_DIRECTORY}.                                |
+--------------------+----------------------------------------------------+
| --codeStyle        | The code style ot use when generating JS code.     |
|                    | Either `stringbuilder` or `concat` styles.         |
+--------------------+----------------------------------------------------+
| --packages         | List of packages to look for template files.       |
+--------------------+----------------------------------------------------+


pwt.recipe.closurebuilder
=========================

If you use `pwt.recipe.closurebuilder`_ then there is a extension to this
in `pwt.jinja2js.recipe` that will automatically compile your templates into
a temporary file, and then include this files as part of your applications
Java Script dependency and then to compile the Java Script down into a small
Java Script file.

.. _pwt.recipe.closurebuilder: http://pypi.python.org/pypi/pwt.recipe.closurebuilder/
.. _closurebuilder: http://code.google.com/closure/library/docs/closurebuilder.html

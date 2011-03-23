Usage
+++++

There are X different ways of including 


WSGI
====

pwt.jinja2js contains a WSGI middleware layer in
``pwt.jinja2js.soy_wsgi.Resources`` that produces the output that can be used
to dynamically convert the templates to JavaScript. This is handy for
development where we can refresh the page to pull in any made to the template.


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
| --packages         | List of packages to look for template files.       |
+--------------------+----------------------------------------------------+


pwt.recipe.closurebuilder
=========================

TODO

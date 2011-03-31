Compatibility with Jinja2
+++++++++++++++++++++++++

Not all your Jinja2 templates will compile nicely to JavaScript and some
will complain loudly that some features are missing.

The following features of Jinja2 will *NOT* be supported:

 * extends

 * blocks

The following filters are supported in pwt.jinja2js:

 * default
 * truncate
 * capitalize
 * last
 * length
 * replace

None of the other filters supported by Jinja2 are currently support but that
might change in the future.

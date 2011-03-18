Usage
+++++

There are X different ways of including 


WSGI
====

pwt.jinja2js contains a WSGI middleware layer in
``pwt.jinja2js.soy_wsgi.Resources`` that produces the output that can be used
to dynamically convert the templates to JavaScript. This is handy for
development where we can refresh the page to pull in any made to the template.

About
=====

pwt.jinja2js is an extension to the Jinja2 template engine that compiles
valid Jinja2 templates containing macros to JavaScript. The JavaScript output
can be included via script tags or can be added to the applications JavaScript.

Nutshell
--------

Here a small example of a Jinja template::

     {% namespace ns1 %}

     {% macro printusers(users) %}
     <ul>
     {% for user in users %}
         <li><a href="{{ user.url }}">{{ user.username }}</a></li>
     {% endfor %}
     </ul>
     {% endmacro %}


Which after running through the pwt.jinja2js compiler we need up the
following JavaScript::

     if (typeof ns1 == 'undefined') { var ns1 = {}; }

     ns1.printusers = function(opt_data, opt_sb, opt_caller) {
        var output = '';
        output += '\n<ul>\n';
        var userList = opt_data.users;
        var userListLen = userList.length;
        for (var userIndex = 0; userIndex < userListLen; userIndex++) {
            var userData = userList[userIndex];
            output += '\n   <li><a href="' + userData.url + '">' + userData.username + '</a></li>\n';
        }
        output += '\n</ul>\n';
        return output;
     }

By slipping a switch we can produce Java Script that takes advantage of
`Closure Library'_

     goog.provide('ns1');

     goog.require('soy');

     ns1.printusers = function(opt_data, opt_sb) {
        var output = opt_sb || new soy.StringBuilder();
        output.append('\n<ul>\n');
        var userList = opt_data.users;
        var userListLen = userList.length;
        for (var userIndex = 0; userIndex < userListLen; userIndex++) {
            var userData = userList[userIndex];
            output.append('\n   <li><a href="', userData.url, '">', userData.username, '</a></li>\n');
        }
        output.append('\n</ul>\n');
        if (!opt_sb) return output.toString();
     }


Install and test
================

In order to get started with this project and to see what it can do:

 * git clone git@github.com:mkerrin/pwt.jinja2js.git
 * cd pwt.jinja2js
 * python bootstrap
 * ./bin/buildout

Testing
=======

To run the tests run

 * ./bin/test -v

To run a basic server in order to run the JavaScript tests.

 * ./bin/serve --reload

To run the JavaScript tests open a browser and load the url::

  http://localhost:8000/

There is links to two test suites from there.

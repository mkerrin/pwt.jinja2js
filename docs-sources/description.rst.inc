pwt.jinja2js is an extension to the Jinja2 template engine that compiles
valid Jinja2 templates containing macros to Java Script. The Java Script output
can be included via script tags or can be added to the applications Java Script.

It works by mapping each macro in a Jinja2 template to a Java Script function
that when called passing in all parameters to the macro as a Java Script object
returns a string representing output of the template. For example using the
tool we can convert the following template:

.. sourcecode:: html+jinja

   {% namespace ns1 %}

   {% macro printusers(users) %}
   <ul>
   {% for user in users %}
       <li><a href="{{ user.url }}">{{ user.username }}</a></li>
   {% endfor %}
   </ul>
   {% endmacro %}

to produce the following Java Script to be included in your application:

.. sourcecode:: javascript

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
`Closure Library`_ and produces the following:

.. sourcecode:: javascript
   
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

Now we can call the macro like so:

.. sourcecode:: javascript

   document.write(ns1.printusers({users: [
         {username: "michael", url: "#user/michael"},
         {username: "johndoe", url: "#user/johndoe"}
        ]})
      );

to produce:

.. sourcecode:: html

   <ul>
       <li><a href="#user/michael">michael</a></li>
       <li><a href="#user/johndoe">johndoe</a></li>
   </ul>

.. _Closure Library: http://code.google.com/closure/library/

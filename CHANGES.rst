=======
CHANGES
=======

0.7.4
-----

- Remove dependency on the pwt.recipe.closurebuilder and use the pwt.closure
  package instead.

- Add support for inline conditional expressions

- Add support for aliasing function calls

- Automatically inject compiler annotations for Closure compiler

- Add support for stripping white-space from text nodes within macros

- Rewrite calls to local macros to include the namespace

- Allow the amount of indentation to be customized

0.7.3
-----

0.7.2
-----

- Compatibility changes to the dependency and compile recipes of
  `pwt.recipe.closurebuilder`

- Fix WSGI server to work under a sub name space on a server.

0.7.2
-----

- Changes to the pwt.recipe.closurebuilder recipe. This generates all content
  on import so that we are in a position to generate configuration information.

0.7.1
-----

- Start to use closure library directly in the generated JS. No need for the
  `soyutils_usegoog.js` Java Script utility file.

0.7.0
-----

- Compile the Java Script with closure compiler and get the tests to pass.

- Error checks and more consistency when passing dictionaries to an other
  Java Script template.

0.6
---

- Implemented default values for macros.

- Implemented the `round` filter.

0.5.1
-----

- More metadata for package.

0.5
---

- Initial release.

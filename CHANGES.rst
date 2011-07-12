=======
CHANGES
=======

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

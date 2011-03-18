"""
pwt.jinja2js is an extension to the Jinja2 template engine that compiles
valid Jinja2 templates containing macros to JavaScript. The JavaScript output
can be included via script tags or can be added to the applications JavaScript.
"""
from setuptools import find_packages, setup

setup(
    name = "pwt.jscompiler",
    author = "Michael Kerrin",
    author_email = "michael.kerrin@gmail.com",
    license = "BSD",
    description = __doc__,
    long_description = open("README.rst").read(),

    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        # "Programming Language :: Python :: 3",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML"
    ],

    packages = find_packages("src"),
    package_dir = {"": "src"},

    install_requires = ["setuptools",
                        "pwt.recipe.closurebuilder",
                        "WebOb",
                        "MarkupSafe",
                        "Jinja2",
                        ],
    extras_require = {
        "test": [
            "pwt.recipe.closurebuilder[test]",
            "WebTest",
            ],
        },

    entry_points = """
[nose.plugins]
test-suites = pwt.jscompiler.nose_test_suites:Suites

[zc.buildout]
dependency = pwt.jscompiler.recipe:Deps

[paste.app_factory]
main = pwt.jscompiler.soy_wsgi:Resources
""",

    include_package_data = True,
    zip_safe = False,
    )

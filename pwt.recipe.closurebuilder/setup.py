from setuptools import find_packages, setup

setup(
    name = "pwt.recipe.closurebuilder",
    author = "Michael Kerrin",
    author_email = "michael.kerrin@gmail.com",

    packages = find_packages("src"),
    package_dir = {"": "src"},

    install_requires = ["setuptools",
                        "zc.buildout",
                        ],
    extras_require = {
        "test": ["zope.testing"],
        },

    entry_points = """
[zc.buildout]
dependency = pwt.recipe.closurebuilder:Deps
compile = pwt.recipe.closurebuilder:Compile
""",

    include_package_data = True,
    zip_safe = False,

    test_suite = "pwt.recipe.closurebuilder.tests.test_suite",
    )

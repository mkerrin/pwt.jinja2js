from setuptools import find_packages, setup

setup(
    name = "pwt.jscompiler",
    author = "Michael Kerrin",
    author_email = "michael.kerrin@gmail.com",

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
""",

    include_package_data = True,
    zip_safe = False,
    )

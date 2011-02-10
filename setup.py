from setuptools import find_packages, setup

setup(
    name = "jscomp",
    author = "Michael Kerrin",
    author_email = "michael.kerrin@gmail.com",

    packages = find_packages("src"),
    package_dir = {"": "src"},

    install_requires = ["setuptools",
                        "WebOb",
                        "Jinja",
                        ],

    include_package_data = True,
    zip_safe = False,
    )

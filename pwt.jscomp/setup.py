from setuptools import find_packages, setup

setup(
    name = "pwt.jscomp",
    author = "Michael Kerrin",
    author_email = "michael.kerrin@gmail.com",

    packages = find_packages("src"),
    package_dir = {"": "src"},
    namespace_packages = ["pwt"],

    install_requires = ["setuptools"],

    include_package_data = True,
    zip_safe = False,
    )

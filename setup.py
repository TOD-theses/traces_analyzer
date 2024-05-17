"""Python setup.py for traces_analyzer package"""

import io
import os
from setuptools import find_packages, setup  # type: ignore


def read(*paths, **kwargs):
    """Read the contents of a text file safely.
    >>> read("traces_analyzer", "VERSION")
    '0.1.0'
    >>> read("README.md")
    ...
    """

    content = ""
    with io.open(
        os.path.join(os.path.dirname(__file__), *paths),
        encoding=kwargs.get("encoding", "utf8"),
    ) as open_file:
        content = open_file.read().strip()
    return content


def read_requirements(path):
    return [
        line.strip()
        for line in read(path).split("\n")
        if not line.startswith(('"', "#", "-", "git+"))
    ]


setup(
    name="traces_analyzer",
    version=read("traces_analyzer", "VERSION"),
    description="Analyze ethereum traces",
    url="https://github.com/TOD-theses/traces_analyzer/",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="TOD-theses",
    packages=find_packages(exclude=["tests", ".github"]),
    install_requires=read_requirements("requirements.txt"),
    entry_points={
        "console_scripts": ["traces_analyzer = traces_analyzer.__main__:main"]
    },
    extras_require={"test": read_requirements("requirements-test.txt")},
)

"""
setup.py

This file defines the metadata, dependencies, and configuration for packaging, distributing,
and installing the Python SCADA system project. It uses setuptools to specify project details
such as name, version, author, description, required Python version, and dependencies.

Usage:
    - Build a source distribution:    python setup.py sdist
    - Install the package locally:    pip install .
    - Specify dependencies in requirements.txt

For more information, see:
    https://setuptools.pypa.io/en/latest/userguide/index.html
"""
from setuptools import setup, find_packages

def read_requirements(filename="requirements.txt"):
    """Read requirements from a file, ignoring BOM and comments."""
    with open(filename, encoding="utf-8-sig") as f:
        # 'utf-8-sig' automatically removes BOM if present
        lines = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]
    return lines


setup(
    name="openscada_lite",
    version="0.1.0",
    description="Python SCADA system",
    author="Daniel Fernandez Boada",
    author_email="boadadf@yahoo.com",
    url="https://github.com/boadadf/python-scada",
    package_dir={"": "src"},
    packages=find_packages(
        where="src", include=["openscada_lite*", "openscada_lite.*"]
    ),
    install_requires=read_requirements(),
    python_requires=">=3.9",
    include_package_data=True,
    zip_safe=False,
)

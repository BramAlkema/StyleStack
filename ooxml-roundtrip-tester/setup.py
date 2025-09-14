"""Setup script for OOXML Round-Trip Testing Utility."""

from setuptools import setup, find_packages
from pathlib import Path

# Read version from package
exec(open("ooxml_tester/__init__.py").read())

# Read requirements
requirements = []
requirements_file = Path("requirements.txt")
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read README for long description
readme_file = Path("README.md")
long_description = ""
if readme_file.exists():
    with open(readme_file, encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="ooxml-roundtrip-tester",
    version=__version__,
    author=__author__,
    description=__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ooxml-tester=ooxml_tester.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
        "Topic :: Text Processing :: Markup :: XML",
    ],
)
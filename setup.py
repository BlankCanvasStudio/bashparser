#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bashparser",
    version="0.13",
    author="Spencer Stingley",
    author_email="sstingle@usc.edu",
    description="A framework for manipulating and analysing bash scripts",
    long_description="A framework for manipulating and analysing bash scripts",
    long_description_content_type="text/markdown",
    url="https://github.com/BlankCanvasStudio/bashparse",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'unroll = bashparser.unroll:main',
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires = '>=3.6',
    install_requires=['bashlex'],
    test_suite='nose.collector',
    tests_require=['nose'],
)
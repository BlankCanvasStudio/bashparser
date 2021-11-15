#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bashparse",
    version="0.1",
    author="YOU",
    author_email="sstingle@usc.edu",
    description="A tool for analysing and deobfuscating bash scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BlankCanvasStudio/bashparse",
    packages=setuptools.find_packages(),
    # entry_points={
    #     'console_scripts': [
    #         # migrating to pdb prefixes
    #         'script-name = module.foo.bar:main',
    #     ]
    # },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires = '>=3.6',
    install_requires=['bashlex'],
    test_suite='nose.collector',
    tests_require=['nose'],
)
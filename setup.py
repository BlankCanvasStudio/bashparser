#!/usr/bin/env python

from setuptools import setup

setup(name='bashparse',
      version='1.0',
      # list folders, not files
      packages=['bashparse',
                'bashparse.test'],
      # scripts=['bashparse/bin/bashparse_script.py'],
      # package_data={'bashparse': ['data/bashparse_data.txt']},
      )

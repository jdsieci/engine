

import os
try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup

def read(fname):
  return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup()
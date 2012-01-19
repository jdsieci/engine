#!/usr/bin/env python
#
# Copyright 2011 JDSieci
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import os
import sys
try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup

kwargs = {}

def read(fname):
  return open(os.path.join(os.path.dirname(__file__), fname)).read()

major, minor = sys.version_info[:2]
if major >= 3:
  kwargs["use_2to3"] = True


setup(name="engine",
      version = "0.1.0",
      author = "JDSieci",
      author_email = "biuro@jdsieci.pl",
      description = "Enchanced ",
      long_description = read('README'),
      license = "http://www.apache.org/licenses/LICENSE-2.0",
      package_dir = {'engine':'engine'},
      package_data = {'engine':['session/*.sql']},
      packages = ['engine'],
      requires = ['tornado (>=2.1.1)', 'daemon', 'setproctitle'],
      install_requires = ['tornado>=2.1.1', 'daemon', 'setproctitle'],
      scripts = [],
      **kwargs
     )
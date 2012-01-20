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

#import distribute_setup
#distribute_setup.use_setuptools()

from setuptools import setup

kwargs = {}

def read(fname):
  return open(os.path.join(os.path.dirname(__file__), fname)).read()

major, minor = sys.version_info[:2]
if major >= 3:
  kwargs["use_2to3"] = True
else:
  import distribute_setup
  distribute_setup.use_setuptools()
  

from setuptools import setup

setup(name="engine",
      version = "0.1.0.dev",
      author = "JDSieci",
      author_email = "biuro@jdsieci.pl",
      url = 'http://www.jdsieci.pl',
      description = "Enchanced Tornado",
      long_description = read('README'),
      license = "http://www.apache.org/licenses/LICENSE-2.0",
      #namespace_packages = ['engine'], 
      packages = ['engine'],
      package_dir = {'engine': 'engine'},
      package_data = {'engine': ['session/*.sql']},
      install_requires = ['tornado>=2.1.1', 'daemon', 'setproctitle'],
      extras_requires = {'database': ['psycopg2', 'MySQLdb']},
      test_suite = 'tests',
      **kwargs
     )
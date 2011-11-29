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
'''
Database pool classes
'''

#TODO: wsteczna zgodnosci z tornado.database
#TODO: wykozystanie db-api
#TODO: wywalenie sqlalchemy

#TODO: dzialajaca pula polaczen, jedna dla roznych silnikow per aplikacja
class Pool(object):
  _count = 0
  def __init__(self):
    pass
  
  def get(self):
    self._count += 1 
    pass
  
  def put(self):
    self._count -= 1 
    return self._count
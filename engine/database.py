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
class Connection(object):
  def __init__(self,driver,*args,**kwargs):
    self._allowed_drivers()
    if driver.lower() in self._allowed.keys():
      self._db = self._allowed[driver].connect(*args,**kwargs)
    
  def _allowed_drivers(self):
    self._allowed={}
    try:
      import psycopg2
      self._allowed['pgsql']=psycopg2
    except ImportError:
      pass
    try:
      import MySQLdb
      self._allowed['mysql']=MySQLdb
    except ImportError:
      pass    
    try:
      import sqlite3
      self._allowed['sqlite']=sqlite3
    except ImportError:
      pass    

  def __getattr__(self,attr):
    return getattr(self._db, attr)
  def __repr__(self):
    return repr(self._db) 
  def close(self):
    pass
  
   
class Pool(object):
  _connections=dict()
  def __init__(self,minconn, maxconn, *args, **kwargs):
    pass
  
  def getconn(self,key=None):
    if self._connections.has_key(key):
      return self._connections[key]
    else:
      self._connections[key]
  
  def putconn(self,connection=None,key=None,close=False):
    return self._count
  
  def closeall(self):
    pass
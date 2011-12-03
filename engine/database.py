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
DB-API 2.0 Compilant database wrapper, for MySQL (MySQLdb),
PostgreSQL (psycopg2) and SQLite (sqlite3).
Implemented single connection Pool for application process.
'''

#TODO: wsteczna zgodnosci z tornado.database
#TODO: wykozystanie db-api
#TODO: wywalenie sqlalchemy

#TODO: dzialajaca pula polaczen, jedna dla roznych silnikow per aplikacja


import re

_allowed_drivers={}
_basecursors={}
try:
  import psycopg2
  _allowed_drivers['pgsql']=psycopg2
  import psycopg2.extensions
  _basecursors['pgsql']=psycopg2.extensions.cursor
except ImportError:
  pass
try:
  import MySQLdb
  _allowed_drivers['mysql']=MySQLdb
  import MySQLdb.cursors
  _basecursors['mysql']=MySQLdb.cursors.Cursor
except ImportError:
  pass
try:
  import sqlite3
  _allowed_drivers['sqlite']=sqlite3
  _basecursors['sqlite']=sqlite3.Cursor
except ImportError:
  pass


class Connection(object):
  pool=None
  dsn=None
  def __init__(self,driver,pool=None,*args,**kwargs):
    global _allowed_drivers
    global _basecursors
    self.pool = None
    if driver.lower() in _allowed_drivers.keys():
      self._db = _allowed_drivers[driver].connect(*args,**kwargs)
      self.driver=driver.lower()
      self._basecursor=_basecursors[driver]

  def __del__(self):
    self.close()

  def __getattr__(self,attr):
    return getattr(self._db, attr)

  def __repr__(self):
    return repr(self._db)

  def _cursor_factory(self):
    basecursor=self._basecursor
    if self.driver == 'sqlite':
      requery=re.compile('%\((\w+)?\)s')
      class Cursor(basecursor):
        def execute(self,query,parameters=None):
          return super(basecursor,self).execute(self._translate(query,parameters),parameters)

        def _translate(self,query,params):
          if type(params) is dict:
            return requery.sub(r':\1',query)
          else:
            return query.replace('%s','?')

    if self.driver == 'sqlite':
      class Cursor(basecursor):
        def execute(self,query,parameters=None):
          return super(basecursor,self).execute(self._translate(query,parameters),parameters)
        def _translate(self,query):
          return query
    return Cursor

  def cursor(self):
    if self.driver == 'pgsql':
      return self._db.cursor(cursor_factory=self._cursor_factory())
    return self._db.cursor(self._cursor_factory())

  def close(self,):
    if self.pool is not None:
      self.pool.delcon()
    if getattr(self, "_db", None) is not None:
      self._db.close()
      self._db = None

class Pool(object):
  _connections=dict()
  def __init__(self,maxconn,**kwargs):
    self.maxconn = maxconn
    self.per_drivermaxconn = {}
    
  def getconn(self,key=None):
    """key = default None, should be DSN"""
    if key not in self._connections.keys():
      self._connections[key] = Connection()
    return self._connections[key]

  def putconn(self,connection=None,key=None,close=False):
    pass
  def delcon(self,key=None,connection=None):
    pass
  def closeall(self):
    for con in self._connections.itervalues():
      con.close()
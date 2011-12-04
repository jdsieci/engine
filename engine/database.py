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
  import MySQLdb.constants
  import MySQLdb.converters
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
  def __init__(self,pool=None,driver,**kwargs):
    global _allowed_drivers
    global _basecursors
    self.pool = pool
    self.host = host
    self.database = database
    self.max_idle_time = max_idle_time
    if driver.lower() in _allowed_drivers.keys():
      self._db = _allowed_drivers[driver].connect(**kwargs)
      self.driver=driver.lower()
      self._basecursor=_basecursors[driver]

  def __del__(self):
    self.close()

  def __getattr__(self,attr):
    return getattr(self._db, attr)

  def __repr__(self):
    return repr(self._db)

  def _connect_mysql(self):
    self.host = host
    self.database = database
    self.max_idle_time = max_idle_time

    args = dict(use_unicode=True, charset="utf8",
                db=self.database, init_command='SET time_zone = "+0:00"',
                sql_mode="TRADITIONAL")
    if user is not None:
      args["user"] = user
    if password is not None:
      args["passwd"] = password

    # We accept a path to a MySQL socket file or a host(:port) string
    if "/" in host:
      args["unix_socket"] = host
    else:
      self.socket = None
      pair = host.split(":")
      if len(pair) == 2:
        args["host"] = pair[0]
        args["port"] = int(pair[1])
      else:
        args["host"] = host
        args["port"] = 3306
    self._db = None
    self._db_args = args
    self._last_use_time = time.time()
    try:
      self.reconnect()
    except Exception:
      logging.error("Cannot connect to MySQL on %s", self.host,
                    exc_info=True)
  
  def _connect_pgsql(self):
    pass
  
  def _connect_sqlite(self):
    pass

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
  
  def reconnect(self):
    """Closes the existing database connection and re-opens it."""
    connect=getattr(self,'_connect'+self.driver)
    self.close()
    connect()
    self._db.autocommit(False)


class Pool(object):
  """Class managing all database connections, should be one per application process"""
  _connections=dict()
  
  def __init__(self,maxconn,**kwargs):
    global _allowed_drivers
    self.maxconn = maxconn
    self._weights=dict.fromkeys(_allowed_drivers.keys(),1)
    self._loads=dict.fromkeys(_allowed_drivers.keys(),0)
    
  def _calculate_weight(self,driver=None):
    if driver == None:
    else:
      
  
  def _connect(self):
    pass
      
  def getconn(self,driver,):
    """dsn = default None, should be DSN"""
    if dsn not in self._connections.keys():
      self._connections[dsn] = Connection(pool=self,driver=)
    self._loads
    return self._connections[dsn]

  def putconn(self,connection=None,dsn=None,close=False):
    pass
  def delcon(self,key=None,connection=None):
    pass
  def closeall(self):
    for con in self._connections.itervalues():
      con.close()
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

DSN formats:
  driver://[user[:password]@]hostname[:port]/dbname
  driver://[user[:password]@]unix_socket:dbname
  driver://absolute_path_to_database
Exceptions:
  sqlite://:memory:

Query parameter markers:
  All connections use 'format' and 'pyformat'
'''

#TODO: wsteczna zgodnosci z tornado.database
#TODO: wykozystanie db-api 2.0

#TODO: dzialajaca pula polaczen, jedna dla roznych silnikow per aplikacja


import re
import logging
import time
import math
import itertools

from tornado.ioloop import PeriodicCallback

__ALLOWED_DRIVERS={}
__BASECURSORS={}
try:
  import psycopg2
  __ALLOWED_DRIVERS['pgsql']=psycopg2
  import psycopg2.extensions
  __BASECURSORS['pgsql']=psycopg2.extensions.cursor
except ImportError:
  pass
try:
  import MySQLdb
  __ALLOWED_DRIVERS['mysql']=MySQLdb
  import MySQLdb.cursors
  import MySQLdb.constants
  import MySQLdb.converters
  __BASECURSORS['mysql']=MySQLdb.cursors.Cursor
except ImportError:
  pass
try:
  import sqlite3
  __ALLOWED_DRIVERS['sqlite']=sqlite3
  __BASECURSORS['sqlite']=sqlite3.Cursor
except ImportError:
  pass
#try:
#  import pyodbc
#  _ALLOWED_DRIVERS['odbc']=pyodbc
#  _BASECURSORS['odbc']=pyodbc.Cursor
#except ImportError:
#  pass

#Internal CONSTANTS
__DSNRE=re.compile(r'''(?P<exception>sqlite)://:memory:|
                     (?P<driver>\w+?)://  # driver
                     (?:(?:(?P<user>\w+?)(?::(?P<password>\w+?))?@)?  # user and password pattern
                     (?:(?P<host>[\w\.]+?)(?::(?P<port>\d+))?/|(?P<unix_socket>/\w+(?:/?\w+)*):)  # host patterns
                     (?P<dbname>\w+)|(?P<path>/\w+(?:/?\w+)*)) # database patterns''', re.I | re.L | re.X)

__QUERYRE = re.compile('%\((\w+)?\)s')

class Connection(object):

  def __init__(self,dsn,**kwargs):
    try:
      (exception,driver,user,password,host,port,unix_socket,dbname,path) = __DSNRE.match(dsn).groups()
    except AttributeError:
      raise
    self._dsn = dsn
    if not exception:
      self.host = host
      self.port = port
      self.unix_socket = unix_socket
      self.path = path
      self.database = dbname
      self.password = password
      self.user = user
    elif exception == 'sqlite':
      self.driver = exception
      self.path = ':memory:'

    #Optional params
    try: self.max_idle_time = kwargs['max_idle_time']
    except KeyError: self.max_idle_time = 7*3600      # default 7 hours
    try: self.autocommit = kwargs['autocommit']
    except KeyError:  self.autocommit = False

    try: connect = kwargs['connect']
    except KeyError: connect = True

    self._last_use_time = time.time()

    if driver.lower() in __ALLOWED_DRIVERS.keys():
      if connect:
        self.reconnect()
      self.driver=driver.lower()
      self._basecursor=__BASECURSORS[driver]
      self._cursor = self._cursor_factory()

  def __del__(self):
    self.close()

  def __getattr__(self,attr):
    return getattr(self._db, attr)

  def __repr__(self):
    return repr(self._db)

  def _ensure_connected(self):
    if (self._db is None or (time.time() - self._last_use_time > self.max_idle_time)):
      self.reconnect()
      self._last_use_time = time.time()

  #connection methods, driver specific attributes
  def _connect_mysql(self):
    if not self._db_args:
      args = dict(use_unicode=True, charset="utf8",
                db=self.database,
                sql_mode="TRADITIONAL")
      if self.user is not None:
        args["user"] = self.user
      if self.password is not None:
        args["passwd"] = self.password

      # We accept a path to a MySQL socket file or a host(:port) string
      if self.unix_socket:
        args["unix_socket"] = self.unix_socket
      else:
        args["host"] = self.host
        args["port"] = self.port if self.port else 3306
      self._db = None
      self._db_args = args

    try:
      self._db = MySQLdb.connect(**self._db_args)
      self._db.autocommit(self.autocommit)
    except Exception:
      logging.error("Cannot connect to MySQL on %s", self.host if self.host else self.unix_socket,
                    exc_info=True)

  def _connect_pgsql(self):
    if not self._db_args:
      args=dict(database=self.database)
      if self.user is not None:
        args["user"] = self.user
      if self.password is not None:
        args["password"] = self.password
      if self.unix_socket:
        args["host"] = self.unix_socket
      else:
        args["host"] = self.host
        args["port"] = self.port if self.port else 5432
      self._db = None
      self._db_args = args
      
    try:
      self._db = psycopg2.connect(**self._db_args)
      self._db.autocommit = self.autocommit
    except Exception:
      logging.error("Cannot connect to PostgeSQL on %s", self.host if self.host else self.unix_socket,
                    exc_info=True)

  def _connect_sqlite(self):
    if not self._db_args:
      args = dict(database=self.path)
      self._db = None
      self._db_args = args
    try:
      self._db = sqlite3.connect(**self._db_args)
      self._db.autocommit(self.autocommit)
    except Exception:
      logging.error("Cannot connect to SQLite on %s", self.path,
                    exc_info=True)

  #def _cursor_factory(self):
  #  basecursor=self._basecursor
  #  if self.driver == 'sqlite':
  #    requery=re.compile('%\((\w+)?\)s')
  #    class Cursor(basecursor):
  #      def execute(self,query,parameters=None):
  #        return super(basecursor,self).execute(self._translate(query,parameters),parameters)
  #
  #      def _translate(self,query,params):
  #        if type(params) is dict:
  #          return requery.sub(r':\1',query)
  #        else:
  #          return query.replace('%s','?')
  #  else:
  #    class Cursor(cursor):
  #      def execute(self,query,parameters=None):
  #        return super(basecursor,self).execute(self._translate(query,parameters),parameters)
  #      
  #      def _translate(self,query,params):
  #        return query
  #  return Cursor
  def _cursor_factory(self):
    if self.driver == 'sqlite':
      class Cursor(_Cursor):
        def _translate(self,query,params):
          if type(params) is dict:
            return __QUERYRE.sub(r':\1',query)
          else:
            return query.replace('%s','?')
    else:
      class Cursor(_Cursor):
        def _translate(self,query,params):
          return query
    return Cursor
  
  @property
  def connected(self):
    return self._db is not None
  @property
  def dsn(self):
    return self._dsn

  def cursor(self):
    return self._cursor_factory()((self._db.cursor()))

  def close(self):
    if getattr(self, "_db", None) is not None:
      self._db.close()
      self._db = None

  def reconnect(self):
    """Closes the existing database connection and re-opens it."""
    connect=getattr(self,'_connect'+self.driver)
    self.close()
    connect()


class _Cursor(object):
  """Cursor wrapper class.
  """
  def __init__(self,cursor):
    self._cursor=cursor

  def __getattr__(self,attr):
    return getattr(self._cursor, attr)

  def __repr__(self):
    return repr(self._cursor)
  
  def __del__(self):
    self.close()

  def _translate(self,query,params):
    raise """Overrride that"""
    
  def execute(self,query,parameters=None):
    return self._cursor.execute(self._translate(query,parameters),parameters)
  
  def iter(self):
    column_names = self.column_names()
    for row in self._cursor:
      yield Row(zip(column_names,row))
            
  def column_names(self):
    return [d[0] for d in self._cursor.description]
  
  def fetchone(self):
    row = self._cursor.fetchone()
    if row is not None:
      return Row(zip(self.column_names(),row))
    else:
      return None
    
  def fetchmany(self,*args,**kwargs):
    rowlist=self._cursor.fetchmany(*args,**kwargs)
    column_names=self.column_names()
    return [Row(itertools.izip(column_names,row)) for row in rowlist]
  
  def fetchall(self):
    column_names=self.column_names()
    return [Row(itertools.izip(column_names,row)) for row in self._cursor.fetchall()]  

  def close(self):
    if getattr(self, "_cursor", None) is not None:
      self._cursor.close()
      self._cursor = None

    
class Row(dict):
  """A dict that allows for object-like property access syntax"""
  def __getattr__(self,name):
    try:
      return self[name]
    except KeyError:
      raise AttributeError(name)


class ConnectionPool(object):
  """A connection pool that manages connections
  """
  def __init__(self,dsn,mincon=1,maxcon=1,pool=None,**kwargs):
    self._mincon=mincon
    self._maxcon=maxcon
    self._dsn=dsn
    self._pool=pool
    self._connections=[]
    self._in_use=[]
    for i in range(mincon):
      self._connect()
    #Optional params
    try: cleanup_timeout = kwargs['cleanup_timeout']
    except KeyError: cleanup_timeout = 2*3600       #default 2 hours

    self._cleaner = PeriodicCallback(self._clean_pool,cleanup_timeout*1000)
    self._cleaner.start()

  def _connect(self):
    if self.count > self._maxcon:
      raise PoolError('connection pool exausted')
    self._connections.append(Connection(self._dsn))

  def _clean_pool(self):
    while self._connections:
      con = self._connections.pop()
      con.close()

  def getconn(self):
    self._connect()
    try:
      connection = self._connections.pop()
      self._in_use.append(connection)
    except IndexError:
      return None
    return connection

  def putconn(self,connection,close=False):
    try:
      self._in_use.remove(connection)
    except ValueError:
      pass
    if close or (self.count + 1 > self.maxcon):
      connection.close()
    else:
      self._connections.append(connection)

  @property
  def count(self):
    return len(self._connections) + len(self._in_use)
  @property
  def maxcon(self):
    return self._maxcon

  def setmaxcon(self,maxcon):
    if maxcon >0:
      self._maxcon = maxcon
    else:
      raise ValueError

class Pool(object):
  """Class managing all database connections, should be one per application process"""

  def __init__(self,maxpools=None,
               maxconn=None,
               maxconn_timeout=1,
               weight_timeout=10):
    self.maxpools = maxpools or 30
    self.maxconn = maxconn if maxconn or maxconn >= maxpools else (maxpools*10)
    self._gets=dict()
    self._previous_gets=dict()
    self._connections=dict()
    self._weight_timeout=weight_timeout
    self._weight_locked=False
    #Periodic callbacks for cleaning and weight calculation
    if maxconn_timeout > 0:
      self._dsn_maxcon = PeriodicCallback(self._dsn_maxcon_calculator,maxconn_timeout*1000)
      self._maxconn.start()
    if weight_timeout > 0:
      self._weight = PeriodicCallback(self._weight_calculator,weight_timeout*1000)
      self._weight.start()


  @staticmethod
  def instance(maxconn=200,**kwargs):
    """Returns a global Pool instance.
    """
    if not hasattr(Pool,'_instance'):
      Pool._instance = Pool(maxconn,**kwargs)
    return Pool._instance

  @staticmethod
  def initialized():
    """Returns true if singleton instance has been created"""
    return hasattr(Pool,'_instance')

  def _weight_calculator(self):
    self._weight_locked=True
    for dsn in self._gets.iterkeys():
      try:
        delta = self._gets[dsn] - self._previous_gets[dsn]
      except KeyError:
        delta = 0
      self._weight[dsn]=math.log(delta/self._weight_timeout+1)+1
    self._previous_gets = self._gets.copy()
    self._weight_locked=False

  def _dsn_maxcon_calculator(self):
    calculated_max_conn_count = 0
    con_count={}
    for dsn in self._connections.iterkeys():
      con_count[dsn]= self._conn_count(dsn)
      calculated_max_conn_count +=con_count[dsn]
    adjustment = (.0+self.maxconn)/calculated_max_conn_count
    for (dsn,conn) in con_count.iteritems():
      con_count[dsn]=math.floor(conn*adjustment)
      self._connections[dsn].setmaxcon(con_count[dsn])

  def _conn_count(self,dsn):
    con_count=1.0*self._weight[dsn]*self.maxconn/self.dsn_count
    return con_count

  def _createpool(self,dsn):
    if self.dsn_count < self.maxpools:
      self._connections[dsn] = ConnectionPool(dsn,pool=self)
      self._gets[dsn]=0
      self._weight[dsn]=1
    else:
      raise PoolError('Pool of pools exeeded')
  
  @property
  def count(self):
    """Returns Connections global count"""
    counter=0
    for pool in self._connections.itervalues():
      counter+=pool.count
    return counter

  @property
  def dsn_count(self):
    """Returns ConnectionPools count"""
    return len(self._connections)
  
  @property
  def gets(self):
    """Returns global count of getconn invocation, counted from Pool init"""
    count=0
    for dsn in self._gets.itervalues():
      count+=dsn
    return count

  def getconn(self,dsn):
    """Gets connection from specific ConnectionPool"""
    if dsn not in self._connections.keys():
      self._createpool(dsn)
    else:
      raise
    self._gets[dsn]+=1
    return self._connections[dsn].getconn()

  def putconn(self,dsn,connection,close=False):
    self._connections[dsn].putconn(connection,close)

  def delcon(self,dsn=None,connection=None):
    self._connections[dsn].close()
    del self._connections[dsn]
    del self._weight[dsn]
    del self._gets[dsn]

  def closeall(self):
    for pool in self._connections.itervalues():
      pool.close()

class PoolError(Exception):
  pass
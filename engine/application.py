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
Created on 12-09-2011

@author: tofik
domyslne wykorzystanie:

class Application(engine.application.BaseApplication):
  def __init__(self):
    handlers=[]
    settings={}
    super(Application,self).__init__(handlers,**settings)
'''
import tornado.web
from tornado.options import define,options
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
import session
import os
#build-in options
define('sessionsecret',default=None,help='Session secret password')
define('cookiesecret',default='u_must_change_it')
define('debug',default=False,type=bool)
define('port',default=8888,type=int)
define('address',default='')
define('workers',default=os.sysconf("SC_NPROCESSORS_ONLN"),type=int,help='Quantity of worker processes, running more than %i is not recommended' % (os.sysconf("SC_NPROCESSORS_ONLN")*2))

class SimpleApplication(tornado.web.Application):
  def __init__(self,handlers, **settings):
    self.name=self.__class__.__name__.lower()
    super(SimpleApplication,self).__init__(handlers, **settings)
    

class BaseApplication(SimpleApplication):
  '''BaseApplication tornado.web.Application with DirectorySessionStorage'''
  settings = None
  #name = 'baseapp'
  _dbpool = {}
  def __init__(self,handlers,**kwds):
    settings=kwds
    settings['session_secret'] = options.sessionsecret
    settings['cookie_secret'] = options.cookiesecret
    self.session_manager = session.SessionManager(session.DirectorySessionStorage,session_dir='/tmp/tornado-session',secret=options.sessionsecret)
    super(BaseApplication,self).__init__(handlers, **settings)
  

class DatabaseApplication(SimpleApplication):
  """Application with database engine handling
  Not Fully Implemented Yet!
  """
  def __init__(self,handlers,**settings):
    define('poolsize',default=10,type=int)
    settings['session_secret'] = options.sessionsecret
    settings['cookie_secret'] = options.cookiesecret
    self.session_manager = session.SessionManager(session.DirectorySessionStorage,)
    super(BaseApplication,self).__init__(handlers, **settings)
  @property
  def dbpool(self,dsn):
    """manage dbsessions returns SQLA session object"""
    if self.settings['pool'] > len(self._dbpool):
      self.__createsession(dsn)
    return self._dbpool[dsn]
  
  def __createsession(self,dsn):
    """Creates client database session"""
    engine=create_engine(options.dbengine+"://"+options.user+":"+options.dbadminpass+"@"+options.dbhost+':'+options.dbport+"/"+options.dbname)
    session = scoped_session(sessionmaker(autoflush=True, transactional=True, bind=engine))
    db.create_all(bind=engine)
    self.dbpool[client] = (session,0)
    self.dbpool[client] = (self.dbpool[client][0],self.dbpool[client][1]+1)
    return True
  
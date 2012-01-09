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
import session
import database
import os
#build-in options
define('sessionsecret',default=None,help='Session secret password')
define('cookiesecret',default='u_must_change_it')
define('debug',default=False,type=bool)
define('port',default=8888,type=int)
define('address',default='')

class SimpleApplication(tornado.web.Application):
  """Equivalent to tornado.web.Application, for clean inheritance"""
  def __init__(self,handlers, **settings):
    self.name=self.__class__.__name__.lower()
    super(SimpleApplication,self).__init__(handlers, **settings)
    

class BaseApplication(SimpleApplication):
  '''BaseApplication tornado.web.Application with DirectorySessionStorage'''
  settings = None
  #name = 'baseapp'
  def __init__(self,handlers,**settings):
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
    self.pool = database.Pool.instance()
    self.session_manager = session.SessionManager(session.DatabaseSessionStorage,self.pool,secret=options.sessionsecret)
    super(BaseApplication,self).__init__(handlers, **settings)

  def db(self,dsn):
    """returns database pool instance"""
    return self.pool.getconn(dsn)

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
Sessions for tornado
Based on: http://caines.ca/blog/programming/sessions-in-tornado/

Multiple storage added

Usage:
In your application script,
    settings["session_secret"] = 'some secret password!!'
    settings["session_dir"] = 'sessions'  # the directory to store sessions in
    application.session_manager = session.SessionManager(session.DirectorySessionStorage,settings["session_secret"], settings["session_dir"])

In your RequestHandler (probably in __init__),
    self.session = session.Session(self.application.session_manager, self)

After that, you can use it like this (in get(), post(), etc):
    self.session['blah'] = 1234
    self.save()
    blah = self.session['blah']

    etc.


the basic session mechanism is this:
* take some data, pickle it, store it somewhere.
* assign an id to it. run that id through a HMAC (NOT just a hash function) to prevent tampering.
* put the id and HMAC output in a cookie.
* when you get a request, load the id, verify the HMAC. if it matches, load the data from wherever you put it and depickle it.


'''

#import pickle
import cPickle as pickle #poprawka wydajnosci
import os.path
import hmac
import hashlib
import uuid
from tornado.options import define, options
from tornado.ioloop import PeriodicCallback
import pkgutil
import time



define('session_dsn', default=None,metavar='driver://[user[:password]@]hostname[:port]/dbname',help='DSN for database session storage')
define('session_lifetime',default=1800,metavar='1800',help='Session life time in seconds, default 30m')





class _Session(dict):
  """ A Session is basically a dict with a session_id and an hmac_digest string to verify access rights """
  def __init__(self, session_id, hmac_digest,lifetime = 0,storage = None):
    self.session_id = session_id
    self.hmac_digest = hmac_digest
    self.lifetime = lifetime
    self.storage = storage
    self.closed = False
  
  def __repr__(self):
    r = object.__repr__(self)
    return '%s;session_id: %s, hmac_digest: %s,closed: %s, items: %s>' % (r.rstrip('>'),self.session_id,self.hmac_digest,self.closed,dict.__repr__(self))
  
  def __getitem__(self,key):
    self._is_closed()
    if self.storage is not None:
      self.update(self.storage.get(self.session_id,self.hmac_digest,self.lifetime))
    return dict.__getitem__(self,key)
  
  def __setitem__(self,key,value):
    self._is_closed()
    if self.storage is not None:
      self.update(self.storage.get(self.session_id,self.hmac_digest,self.lifetime))
      dict.__setitem__(self,key,value)
      self.storage.set(self)
    else:
      dict.__setitem__(self,key,value)
      
  def __delitem__(self,key):
    self._is_closed()
    if self.storage is not None:
      self.update(self.storage.get(self.session_id,self.hmac_digest,self.lifetime))
      dict.__delitem__(self,key)
      self.storage.set(self)
    else:
      dict.__delitem__(self,key)

  def __getattr__(self,name):
    try:
      return self[name]
    except KeyError:
      raise AttributeError(name)
  
  def _is_closed(self):
    if self.closed:
      raise InvalidSessionException('Session closed')

  def sync(self):
    self.update(self.storage.get(self.session_id,self.hmac_digest,self.lifetime))
    self.storage.set(self)

  def close(self):
    self.storage = None
    self.closed = True
  
  def __del__(self):
    if not self.closed:
      self.close()


class BaseSessionStorage(object):
  """Dummy sessionstorage. All session storages have to inherit from that class"""
  def __init__(self, secret):
    self.secret = secret

  def get(self, session_id = None, hmac_digest = None):
    """Gets session from strage. Needs to be implemented in child class.
    Keyword arguments:
    session_id -- session identyfier
    hmac_digest -- hmac authetication string
    It must retrun _Session object
    """
    raise InvalidSessionException('Need to be implemented')

  def set(self, session):
    """ Puts session to storage. Needs to be implemented in child class.
    It must retrun _Session object
    """
    raise InvalidSessionException('Need to be implemented')
  
  def delete(self,session):
    """Deletes session from storage.Needs to be implemented in child class.
    It must retrun _Session object
    """
    raise InvalidSessionException('Need to be implemented')

  def expired(self):
    """Cleans up expired sessions from storage.Needs to be implemented in child class.
    It must retrun _Session object
    """
    raise InvalidSessionException('Need to be implemented')

  def _generate_session(self,session_id=None,hmac_digest=None):
    if session_id == None:
      session_should_exist = False
      session_id = self._generate_uid()
      hmac_digest = self._get_hmac_digest(session_id)
    else:
      session_should_exist = True
      session_id = session_id
      hmac_digest = hmac_digest   # keyed-Hash Message Authentication Code

    # make sure the HMAC digest we generate matches the given one, to validate
    expected_hmac_digest = self._get_hmac_digest(session_id)

    if hmac_digest != expected_hmac_digest:
      raise InvalidSessionException('Wrong hmac_digest')
    return (session_should_exist, expected_hmac_digest, session_id, hmac_digest)

  def _get_hmac_digest(self, session_id):
    return hmac.new(session_id, self.secret, hashlib.sha1).hexdigest()

  def _generate_uid(self):
    base = hashlib.md5( self.secret + str(uuid.uuid4()) )
    return base.hexdigest()



class DirectorySessionStorage(BaseSessionStorage):
  """ DirectorySessionStorage handles the cookie and file read/writes for a Session """
  def __init__(self, session_dir = '', **kwargs):
    super(DirectorySessionStorage,self).__init__(**kwargs)

    # figure out where to store the session file
    if session_dir == '':
      session_dir = os.path.join(os.path.dirname(__file__), 'sessions')
    self.session_dir = session_dir


  def _read(self, session_id):
    session_path = self._get_session_path(session_id)
    try :
      data = pickle.load(open(session_path))
      if type(data) == type({}):
        return data
      else:
        return {}
    except IOError:
      return {}

  def get(self, session_id = None, hmac_digest = None, lifetime = options.session_lifetime):

    (session_should_exist, expected_hmac_digest, session_id, hmac_digest) = self._generate_session(session_id, hmac_digest)
    # create the session object
    session = _Session(session_id, hmac_digest,lifetime)

    # read the session file, if this is a pre-existing session
    if session_should_exist:
      data = self._read(session_id)
      for i, j in data.iteritems():
        session[i] = j

    return session

  def _get_session_path(self, session_id):
    return os.path.join(self.session_dir, 'SESSION' + str(session_id))

  def set(self, session):
    session_path = self._get_session_path(session.session_id)
    session_file = open(session_path, 'wb')
    pickle.dump(dict(session.items()), session_file)
    session_file.close()
    
  def delete(self,session):
    session_path = self._get_session_path(session.session_id)
    os.remove(session_path)
  
  def expired(self):
    for session_id in os.listdir(self.session_dir):
      session_path = self._get_session_path(session_id)
      if os.stat(session_path).st_mtime < time.time()+options.session_lifetime:
        os.remove(session_path)

import database
class DatabaseSessionStorage(BaseSessionStorage):
  """SessionStorage using database"""
  def __init__(self,pool,**kwargs):
    super(DatabaseSessionStorage,self).__init__(**kwargs)
    self.pool = pool
    self.connection = self.pool.get(options.session_dsn)
    self._create_tables()

  def _create_tables(self):
    script = pkgutil.get_data(__name__,'session/%s.sql' % self.connection.driver)
    cursor = self.connection.cursor()
    cursor.executescript(script)

  def _read(self, session_id,lifetime):
    cursor = self.connection.execute("SELECT * FROM session WHERE session_id=%s AND expires > NOW() + '%s'",(session_id,lifetime))
    try :
      data = pickle.loads(cursor.fetchone().content)
      if type(data) == type({}):
        return data
      else:
        return {}
    except AttributeError:
      return {}
    finally:
      self.connection.commit()

  def get(self,session_id=None,hmac_digest=None, lifetime = options.session_lifetime):
    (session_should_exist, expected_hmac_digest, session_id, hmac_digest) = self._generate_session(session_id, hmac_digest)

    session = _Session(session_id, hmac_digest,lifetime,self)
    if session_should_exist:
      data = self._read(session_id,lifetime)
      for i, j in data.iteritems():
        session[i] = j
    return session
  def set(self,session):
    pickled = pickle.dumps(dict(session.items()))
    try:
      try:
        self.connection.execute('''INSERT INTO session
         VALUES(%(session_id)s,NOW() + '%(lifetime)s',%(content)s)''',{'session_id': session.session_id,
                                                                   'lifetime': session.lifetime,
                                                                   'content': pickled})
      except database.IntegrityError:
        self.connection.execute('''UPDATE session SET content = %(content)s,
         expires = NOW() + '%(lifetime)s' 
         WHERE session_id = %(session_id)s''',{'session_id': session.session_id,
                                               'lifetime': session.lifetime,
                                               'content': pickled})
    except database.Error, e:
      print e
      self.connection.rollback()
    else:
      self.connection.commit()
  
  def delete(self,session):
    session.close()
    try:
      self.connection.execute('DELETE FROM session WHERE session_id = %s',(session.session_id,))
    except database.Error, e:
      print e
      self.connection.rollback()
    else:
      self.connection.commit()
  
  def expired(self):
    """Cleans up expired sessions"""
    try:
      cursor = self.connection.execute('DELETE FROM session WHERE expires < NOW()')
      return cursor.rowcount
    except database.Error, e:
      self.connection.rollback()
    else:
      self.connection.commit()
  
  def close(self):
    self.connection.commit()
    self.pool.put(self.connection)
    self.connection=None
    self.pool=None
    

#TODO: zaimplementowac memcache
try:
  import memcache

  class MemcacheSessionStorage(BaseSessionStorage):
    def __init__(self, session_dir = '', **kwargs):
      super(DirectorySessionStorage,self).__init__(**kwargs)

    def get(self, session_id = None, hmac_digest = None, lifetime = options.session_lifetime):

      (session_should_exist, expected_hmac_digest, session_id, hmac_digest) = self._generate_session(session_id, hmac_digest)

      # create the session object
      session = _Session(session_id, hmac_digest,lifetime,self)

      # read the session file, if this is a pre-existing session
      if session_should_exist:
        data = self._read(session_id)
        for i, j in data.iteritems():
          session[i] = j
      return session

    def set(self, session):
      pass

except ImportError:
  pass

class SessionManager(object):
  """ A SessionManager is specifically for use in Tornado, using Tornado's cookies """
  def __init__(self,sessionstorage,**kwargs):
    self.sessionstorage=sessionstorage(**kwargs)
    self._cleaner = PeriodicCallback(self._cleanup,options.session_lifetime*500)
    self._cleaner.start()

  def _cleanup(self):
    self._expired()
  
  def _expired(self):
    self.sessionstorage.expired()
    

  def get(self, requestHandler = None):
    if requestHandler == None:
      return self.sessionstorage.get()
    else:
      session_id = requestHandler.get_secure_cookie("session_id")
      hmac_digest = requestHandler.get_secure_cookie("hmac_digest")
      return self.sessionstorage.get(session_id, hmac_digest)


  def set(self, requestHandler, session):
    requestHandler.set_secure_cookie("session_id", session.session_id)
    requestHandler.set_secure_cookie("hmac_digest", session.hmac_digest)
    return self.sessionstorage.set(session)
  
  def delete(self,requestHandler,session):
    requestHandler.clear_cookie('session_id')
    requestHandler.clear_cookie('hmac_digest')
    return self.sessionstorage.delete(session)
    del session

class Session(_Session):
  """ A TornadoSession is a Session object for use in Tornado """
  def __init__(self, tornado_session_manager, request_handler):
    self.session_manager = tornado_session_manager
    self.request_handler = request_handler
    # get the session object's data and transfer it to this session item
    try:
      plain_session = tornado_session_manager.get(request_handler)
    except InvalidSessionException:
      plain_session = tornado_session_manager.get()

    for i, j in plain_session.iteritems():
      self[i] = j
    self.session_id = plain_session.session_id
    self.hmac_digest = plain_session.hmac_digest
    self.lifetime = plain_session.lifetime
  
  def save(self):
    self.session_manager.set(self.request_handler, self)
    self.close()
  
  def delete(self):
    request_handler = self.request_handler
    self.close()
    self.session_manager.delete(request_handler, self)
  
  def close(self):
    self.session_manager = None
    self.request_handler = None
    super(_Session,self).close()
    
class InvalidSessionException(Exception):
  pass

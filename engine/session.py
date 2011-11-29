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


class _Session(dict):
  """ A Session is basically a dict with a session_id and an hmac_digest string to verify access rights """
  def __init__(self, session_id, hmac_digest):
    self.session_id = session_id
    self.hmac_digest = hmac_digest



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
        
  def get(self, session_id = None, hmac_digest = None):
    # set up the session state (create it from scratch, or from parameters
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
      raise InvalidSessionException()        

    # create the session object
    session = _Session(session_id, hmac_digest)

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

#TODO: wywalenie sqlalchemy i uzycie wewnetrznego sterownika
try:
  import sqlalchemy
      
  class AlchemySessionStorage(BaseSessionStorage):
    """SessionStorage using database via SQLAlchemy as session store"""
    def __init__(self,db,**kwargs):
      super(AlchemySessionStorage,self).__init__(**kwargs)
      self.db=db
    
    def get(self,session_id=None,hmac_digest=None):
      pass
    
    def set(self,session):
      pass

except ImportError:
  pass
             
class SessionManager(object):
  """ A SessionManager is specifically for use in Tornado, using Tornado's cookies """
  def __init__(self,sessionstorage,**kwargs):
    self.sessionstorage=sessionstorage(**kwargs)

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
            
            
    
  def save(self):
    self.session_manager.set(self.request_handler, self)
        
class InvalidSessionException(Exception):        
  pass

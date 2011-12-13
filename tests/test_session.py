
import pytest
import sys
import os.path
#print sys.path
from engine.session import *
class TestBaseStorage:
  def test_base(self):
    from engine import session
    storage = BaseSessionStorage('')
    session_id = storage._generate_uid() 
    hmac = storage._get_hmac_digest(session_id)
    ses = session._Session(session_id,hmac)
    with pytest.raises(InvalidSessionException):
      storage.get()
    with pytest.raises(InvalidSessionException):
      storage.set(ses)
      
class TestDirectoryStorage:
  def test_get_empty(self,tmpdir):
    storage = DirectorySessionStorage(tmpdir,secret='')
    session = storage.get()
    assert hasattr(session,'session_id') and hasattr(session,'hmac_digest')

  def test_set_session(self,tmpdir):
    storage = DirectorySessionStorage(str(tmpdir),secret='')
    session = storage.get()
    storage.set(session)
    assert os.path.isfile(os.path.join(str(tmpdir), 'SESSION' + str(session.session_id)))
    
  def test_get_full(self,tmpdir):
    storage = DirectorySessionStorage(str(tmpdir),secret='')
    session = storage.get()
    storage.set(session)
    session2 = storage.get(session.session_id,session.hmac_digest)
    assert session2 == session

  
class TestDatabaseStorage:
  
  def test_get_empty(self,tmpdir):
    storage = DatabaseSessionStorage(self.connection,secret='')
    session = self.storage.get()
    assert hasattr(session,'session_id') and hasattr(session,'hmac_digest')

  def test_set_session(self,tmpdir):
    storage = DatabaseSessionStorage(self.connection,secret='')
    session = self.storage.get()
    self.storage.set(session)
    assert os.path.isfile(os.path.join(self.connection, 'SESSION' + str(session.session_id)))
    
  def test_get_full(self,tmpdir):
    storage = DatabaseSessionStorage(self.connection,secret='')
    session = self.storage.get()
    self.storage.set(session)
    session2 = self.storage.get(session.session_id,session.hmac_digest)
    assert session2 == session
    
  

import base
import sys
import os.path
import shutil
import tempfile
from engine.session import *
from tornado.options import options


class testBaseStorage(base.TestCase):
  def test_base(self):
    from engine import session
    storage = session.BaseSessionStorage('')
    session_id = storage._generate_uid() 
    hmac = storage._get_hmac_digest(session_id)
    ses = session._Session(session_id,hmac)
    self.assertRaises(InvalidSessionException, storage.get)
    self.assertRaises(InvalidSessionException, storage.set,ses)
      
class testDirectoryStorage(base.TestCase):
  
  @classmethod
  def setUpClass(cls):
    cls.tmpdir = tempfile.mkdtemp()

  @classmethod
  def tearDownClass(cls):
    shutil.rmtree(cls.tmpdir)
  
  def setUp(self):
    self.storage = DirectorySessionStorage(self.tmpdir,secret='')
    
  def test_get_empty(self):
    session = self.storage.get()
    self.assertTrue(hasattr(session,'session_id') and hasattr(session,'hmac_digest') and len(session) == 0)

  def test_set_session(self):
    session = self.storage.get()
    self.storage.set(session)
    self.assertTrue(os.path.isfile(os.path.join(str(self.tmpdir), 'SESSION' + str(session.session_id))))
    
  def test_get_full(self):
    session = self.storage.get()
    self.storage.set(session)
    session2 = self.storage.get(session.session_id, session.hmac_digest)
    self.assertEqual(session2, session)


from engine import database

@base.skipIf('pgsql' not in database.usableDrivers(), 'Required driver not installed')
class TestDatabaseStorage(base.TestCase):
  
  @classmethod
  def setUpClass(cls):
    cls.pool = database.Pool.instance(10)
    cls.tmpdir = tempfile.mkdtemp()
    options.session_dsn = 'pgsql://postgres@localhost/testdb'
  
  @classmethod
  def tearDownClass(cls):
    cls.pool.close()
    shutil.rmtree(cls.tmpdir)
  
  def setUp(self):
    self.storage = DatabaseSessionStorage(self.pool,secret='')
    
  def tearDown(self):
    del self.storage

  def test_get_empty(self):
    session = self.storage.get()
    self.assertTrue(hasattr(session,'session_id') and hasattr(session,'hmac_digest'))

  def test_set_session(self):
    session = self.storage.get()
    self.storage.set(session)
    connection = self.pool.get(options.session_dsn)
    row = connection.execute('SELECT * from session WHERE session_id = %s',(session.session_id,)).fetchone()
    connection.commit()
    self.assertEqual(str(row.session_id), str(session.session_id))

  def test_get_full(self):
    session = self.storage.get()
    self.storage.set(session)
    session2 = self.storage.get(session.session_id, session.hmac_digest)
    self.assertEqual(session2, session)
    
  
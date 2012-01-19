
import base
import sys
from engine import database
import sqlite3
import tempfile
import shutil


class testConnection(base.TestCase):
  
  @classmethod
  def setUpClass(cls):
    cls.tmpdir = tempfile.mkdtemp()

  @classmethod
  def tearDownClass(cls):
    shutil.rmtree(cls.tmpdir)
  
  def setUp(self):
    self.connection = database.connect('sqlite://%s/%s' % (self.tmpdir, 'test.db'))
    self.sqlitecon = sqlite3.connect('%s/%s' % (self.tmpdir, 'test.db')) 
  
  def test_connect(self):
    connection = database.connect('sqlite://:memory:')
    self.assertIsInstance(connection, database.Connection)
    
  def test_transaction(self):
    self.connection.execute("create table recipe(name, ingredients)")
    self.connection.execute("""
      insert into recipe (name, ingredients) values ('broccoli stew', 'broccoli peppers cheese tomatoes');
      """)
    self.assertEqual(len(self.sqlitecon.execute('SELECT * FROM recipe').fetchall()), 0)
    self.connection.commit()
    self.assertNotEqual(len(self.sqlitecon.execute('SELECT * FROM recipe').fetchall()), 0)
  
  def test_invalidDriver(self):
    with self.assertRaisesRegexp(database.InterfaceError, 'this_is_wrong_driver'):
      database.connect('this_is_wrong_driver://user:password@localhost/database')
    
    
    

class testConnectionPool(base.TestCase):
  def setUp(self):
    import sqlite3
    self.maxcon = 10
    self.mincon = 5
    self.dsn = 'sqlite://:memory:'
    self.pool = database.ConnectionPool(self.dsn,self.mincon,self.maxcon)
    
  def test_mincon(self):
    self.assertEqual(self.pool.count, self.mincon)
  
  def test_maxcon(self):
    for i in range(self.maxcon):
      connection=self.pool.get()
      del connection
    self.assertEqual(self.pool.count, self.maxcon)
    self.assertEqual(self.pool.in_use, self.maxcon)
    self.assertEqual(self.pool.available, 0)
    self.assertRaises(database.PoolError, self.pool.get)
  
  def test_put(self):
    connection=[]
    for i in range(self.maxcon):
      connection.append(self.pool.get())
    self.assertEqual(self.pool.count, self.maxcon)
    self.assertEqual(self.pool.in_use, self.maxcon)
    self.assertEqual(self.pool.available, 0)
    for c in connection:
      self.pool.put(c)
      print c 
    self.assertEqual(self.pool.count, self.maxcon)
    self.assertEqual(self.pool.in_use, 0)
    self.assertEqual(self.pool.available, self.maxcon)


class testPool(base.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.tmpdir = tempfile.mkdtemp()
    cls.maxdsn = 10
    cls.dsn = []
    for i in range(10):
      cls.dsn.append('sqlite://%s/%s.db' % (cls.tmpdir, i))

  @classmethod
  def tearDownClass(cls):
    shutil.rmtree(cls.tmpdir)
    
  def setUp(self):
    self.pool = database.Pool.instance(self.maxdsn)
  
  def test_single_instance(self):
    pool = database.Pool.instance()
    self.assertEqual(self.pool, pool)
    self.assertNotEqual(pool.dsn_count, 0)
  
  def test_get(self):
    connection = self.pool.get(self.dsn[0])
    self.assertIsInstance(connection, database.Connection)
    
  def test_put(self):
    pass
  
  def test_maxdsn(self):
    self.assertNotEqual(self.pool.gets, 0)
    for d in self.dsn:
      self.pool.get(d)
    with self.assertRaisesRegexp(database.PoolError,'Pool of pools exeeded'):
      self.pool.get('sqlite://%s/%s' % (self.tmpdir, '10.db'))

def suite():
  suite = base.TestSuite()
  suite.addTest(base.makeSuite(testConnection))
  suite.addTest(base.makeSuite(testConnectionPool))
  suite.addTest(base.makeSuite(testPool))
  return suite

if __name__ == '__main__':
  base.TextTestRunner(verbosity=2).run(suite())
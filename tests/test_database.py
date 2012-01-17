
import unittest
import sys
from engine import database
import sqlite3

class testConnection(unittest.TestCase):
  
  def setUp(self):
    self.connnection = database.connect('sqlite://:memory:')
    self.sqlitecon = sqlite3.connect(':memory:') 
  
  def test_connect(self):
    connection = database.connect('sqlite://:memory:')
    
  def test_transaction(self):
    self.connnection.execute('')
    

class testConnectionPool(unittest.TestCase):
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
    self.assertEqual(self.pool.count, self.maxcon)
    self.assertEqual(self.pool.in_use, 0)
    self.assertEqual(self.pool.available, self.maxcon)


def suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(testConnection))
  suite.addTest(unittest.makeSuite(testConnectionPool))
  return suite

if __name__ == '__main__':
  unittest.TextTestRunner(verbosity=2).run(suite())
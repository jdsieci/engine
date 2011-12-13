#import pytest
import sys
from engine import database

class TestConnectionPool:
  disabled = True
  def setup_class(cls):
    cls.pool = database.Pool()
    cls.count = 0
  def test_get_connection(self):
    Session = self.pool.get()
    assert issubclass(Session,AlchemySession)
  def test_release_connection(self):
    connection = self.pool.get()
    self.pool.put(connection)
    
class TestPool:
  disabled = True
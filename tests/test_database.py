#import pytest
import sys
from engine import database

class TestPool:
  disabled = not sys.modules.has_key('sqlalchemy')
  def setup_class(cls):
    cls.pool = database.Pool()
    cls.count = 0
  @classmethod
  def test_get_connection(cls):
    connection = cls.pool.get()
    cls.count += 1
    pass
  @classmethod
  def test_release_connection(cls):
    concount = cls.pool.put()
    cls.count -= 1
    assert concount == cls.count 
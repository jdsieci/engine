
import pytest
import sys
#print sys.path
from engine.session import *
class TestStorage:
  def test_base(self):
    session = BaseSessionStorage('')
    with pytest.raises(InvalidSessionException):
      session.get()
      session.set()
  def test_directory(self):
    pass
  @pytest.mark.skipif("not sys.modules.has_key('sqlalchemy')")
  def test_alchemy(self):
    session = AlchemySessionStorage()
    
  
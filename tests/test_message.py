import base
from engine import message
import json

#class KnownValues(base.TestCase):
#  
#  def 

class TestMessage(base.TestCase):

  def test_str(self):
    """Message str is correct JSON string"""
    m = message.Message('')
    json.loads(str(m))

  def test_repr(self):
    """Message repr is Message()"""
    m = message.Message('')
    m2 = eval(m.__repr__())
    self.assertEqual(type(m),type(m2))
    
  def test_MessageVersion(self):
    """Verifies message version deffinition in module"""
    #self.assertTrue(hasattr(message,MESSAGE_VERSION))
    self.assertIs(type(message.MESSAGE_VERSION),int)
    
  def test_hasHeader(self):
    m = message.Message('')
    self.assertTrue(hasattr(m.header))

  def test_hasBody(self):
    m = message.Message('')
    self.assertTrue(hasattr(m.body))

class CorrectPayload(base.TestCase):
  
  def test_PayloadDict(self):
    """Dict as payload"""
    ref = json.dumps({})
    m = message.Message({})
    self.assertEqual(m.payload,ref)

  def test_PayloadList(self):
    """List as payload"""
    ref = json.dumps([])
    m = message.Message([])
    self.assertEqual(m.payload,ref)

  def test_PayloadTuple(self):
    """tuple as payload"""
    ref = json.dumps(tuple())
    m = message.Message(tuple())
    self.assertEqual(m.payload,ref)
    
  def test_PayloadString(self):
    """String as payload"""
    ref = json.dumps('')
    m = message.Message('')
    self.assertEqual(m.payload,ref)

class MessageBadInput(base.TestCase):
  
  def test_emptyInput(self):
    """Message type=normal payload can't be empty (None)"""
    self.assertRaises(message.PayloadError,message.Message())
    
  def test_nonEmptyControl(self):
    """Message type=control can't have payload"""
    self.assertRaises(message.PayloadError,message.Message(type='control',payload=''))
    
  def test_unsupportedType(self):
    """Wrong payload type"""
    self.assertRaises(message.PayloadValueError,message.Message(object()))
  
  def test_UUIDmodification(self):
    """MessageID has to be ro"""
    m = message.Message('')
    with self.assertRaises(AttributeError):
      m.msgid = ''

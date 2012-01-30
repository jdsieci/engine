'''
Created on 30-01-2012

@author: tofik
'''

import json

MESSAGE_VERSION = 1

class Message(dict):

  def __init__(self,payload=None,type='normal'):
    super(dict,self).__init__()
    self['header'] = { 'msgid': None,
                       'type': type,
                       'version': MESSAGE_VERSION
                     }
    self['body'] = None
  
  def __getattr__(self, name):
    try:
      return self[name]
    except KeyError:
      raise AttributeError(name)

  
  
  
class MessageError(Exception): pass
class PayloadError(MessageError): pass
class PayloadValueError(PayloadError): pass
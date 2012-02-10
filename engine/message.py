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
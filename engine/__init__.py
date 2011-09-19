
from tornado import options
import logging
import ssl

#Setting up default options
__default_options = (
                     dict(name='config',default='./engine.conf',metavar='./engine.conf',help='Path to configuration file'),
                     dict(name='cacerts',default=None,help='Path to CA SSL certificates, concateneted to one file'),
                     dict(name='cert',default=None,help='Path to server SSL certificate file'),
                     dict(name='key',default=None,help='Path to server private key file'),
                     dict(name='certreq',default=ssl.CERT_NONE,type=int,metavar='%i|%i|%i' % (ssl.CERT_NONE,ssl.CERT_OPTIONAL,ssl.CERT_REQUIRED),help="""Specifies whether a certificate is required from the other side of the connection,
                                   and whether it will be validated if provided. It must be one of the three values CERT_NONE (certificates ignored),
                                   CERT_OPTIONAL (not required, but validated if provided), or CERT_REQUIRED (required and validated).
                                   CERT_NONE=0
                                   CERT_OPTIONAL=1
                                   CERT_REQUIRED=2"""),
                     dict(name='sslver',default=ssl.PROTOCOL_SSLv3,type=int,help="Protocol version, DON'T CHANGE THIS")
                  )

for opt in __default_options:
  try:
    options.define(**opt)
    logging.info('Option %s not defined using default' % opt['name'])
  except options.Error:
    pass

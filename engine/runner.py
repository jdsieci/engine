'''
Created on 22-07-2011

@author: tofik
'''

import os
import sys
import logging
import signal
import grp
import pwd
#from daemon import pidlockfile
import daemon
#import lockfile
import tornado.options
from tornado.options import define, options
import setproctitle
import multiprocessing
import time

import server

define('foreground',default=False,type=bool,help='')
define('chroot',default=None,help='')
define('workdir',default='.',help='')
define('pidfile',default=None,help='')
define('user',default=None,help='')
define('group',default=None,help='')


#sys.argv[0] = 'ceda'

#loadconfig()

#TODO: zrobic zapis do logu z wykorzystaniem tornado.options.enable_pretty_logging()
#context = daemon.DaemonContext(working_directory=options.workdir,
#                               pidfile=options.pidfile and options.pidfile or None,
#                               detach_process=not options.foreground,
#                               uid=options.user and pwd.getpwnam(options.user).pw_uid or None,
#                               gid=options.group and grp.getgrnam(options.group).gr_gid or None,
#                               stdout=sys.stdout,
#                               stderr=sys.stderr
#                              )
#TODO: obsluga sygnalow, przeladowanie konfiguracji !!!
#context.signal_map = {signal.SIGTERM: stopworkers,
#                      signal.SIGINT: stopworkers,
#                      signal.SIGCHLD: watchdog,
#                      signal.SIGHUP: reload                       
#                     }

#with context:
#  runworkers()

class Worker(multiprocessing.Process):
  _application = None
  ssl_options = None
  _context = daemon.DaemonContext()

  def __init__(self,application,
               no_keep_alive=False,
               io_loop=None,
               xheaders=False,
               ssl_options=None,
               server = server.HTTPServer,
               **kwargs):
    self._application = application
    self.xheaders = xheaders
    self.io_loop = io_loop
    self.ssl_options = ssl_options
    self.server = server
    super(Worker,self).__init__(**kwargs)
    
  def run(self):
    setproctitle.setproctitle(self.name)
    server = self.server(self._application,
                         self.ssl_options)
    try:
      server.listen(self.port,self.address)
      tornado.ioloop.IOLoop.instance().start()
    except IOError,e:
      print e.message
      exit(0)
    return 0

  def listen(self,port,address):
    self.port = port
    self.address = address
  
  def reload(self):
    tornado.options.parse_command_line()
    try:
      tornado.options.parse_config_file(options.config)
    except IOError, e:
      print e.strerror + ': ' + options.config
      print 'Using defaults'
    tornado.options.parse_command_line()
    tornado.options.enable_pretty_logging()
    if options.debug:
      print 'Debug Enabled'
      options.foreground=True


class Runner(object):
  _workers=[]
  _starting=True
  _closing=False
  def __init__(self,application,worker=Worker):
    self.application = application
    self.worker = worker
    context = daemon.DaemonContext(working_directory=options.workdir,
                                   pidfile=options.pidfile and options.pidfile or None,
                                   detach_process=not options.foreground,
                                   uid=options.user and pwd.getpwnam(options.user).pw_uid or None,
                                   gid=options.group and grp.getgrnam(options.group).gr_gid or None,
                                   stdout=sys.stdout,
                                   stderr=sys.stderr
                                  )
    context.signal_map = {signal.SIGTERM: self._stop,
                      signal.SIGINT: self._stop,
                      signal.SIGCHLD: self._watchdog,
                      signal.SIGHUP: self._reload                       
                     }
    self._context = context
    setproctitle.setproctitle(application.name)
    
  def createworkers(self):
    for w in range(options.workers):
      port = options.port + w
      worker = self.worker(self.application,
                           ssl_options={
                                        'certfile': options.cert,
                                        'keyfile': options.key,
                                        'ca_certs': options.cacerts,
                                        'ssl_cersion': options.sslver,
                                        'cert_req': options.certreq},
                           name = 'worker%d' % port
                          )
      worker.listen(port,options.address)
      self._workers.append(worker)
  def loadconfig(self):
    tornado.options.parse_command_line()
    try:
      tornado.options.parse_config_file(options.config)
    except IOError, e:
      print e.strerror + ': ' + options.config
      print 'Using defaults'
    tornado.options.parse_command_line()
    tornado.options.enable_pretty_logging()
    if options.debug:
      print 'Debug Enabled'
      options.foreground=True
      
  def start(self):
    try:
      self._context.open()
    except:
      pass
    self.createworkers()
    logging.info('Main proccess started PID: %d' % os.getpid())
    for worker in self._workers:
      worker.start()
      logging.info('Worker started PID: %d, listen on port: %d' % (worker.pid,worker.port))
    self._starting=False
    self._loop()
  
  def execute(self):
    self.loadconfig()
    #self.createworkers()
    self.start()
    
  def _loop(self):
    while True:
      time.sleep(1)
  
  def _stop(self,signal,frame):
    self._closing=True
    logging.info('Signal %d recived PID: %d' % (signal,os.getpid()))
    logging.info('Stopping workers')
    for worker in self._workers:
      try:
        worker.terminate()
      except:
        pass
    exit(0)
  def _watchdog(self,signal,frame):
    for worker in self._workers:
      if not worker.is_alive():
        logging.info('Signal SIGCHLD recived worker "%s" died' % worker.name)
    if(self._starting or self._closing):
      exit(0)
  def _reload(self,signal,frame):
    logging.info('Signal SIGHUP recived please restart to reload')

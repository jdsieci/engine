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
Created on 22-07-2011

@author: tofik
'''

import os
import sys
import logging
import signal
import grp
import pwd
import daemon
import tornado.options
from tornado.options import define, options
import setproctitle
import multiprocessing
import time

import server

define('foreground', default=False, type=bool, help='')
define('chroot', default=None, help='')
define('workdir', default='.', help='')
define('pidfile', default=None, help='')
define('user', default=None, help='')
define('group', default=None, help='')
define('logfile', default=None, help='Path to logfile default stdout')
define('workers', default=os.sysconf("SC_NPROCESSORS_ONLN"), type=int, help='Quantity of worker processes, running more than %i is not recommended' % (os.sysconf("SC_NPROCESSORS_ONLN") * 2))


#TODO: obsluga sygnalow, przeladowanie konfiguracji !!!
#context.signal_map = {signal.SIGTERM: stopworkers,
#                      signal.SIGINT: stopworkers,
#                      signal.SIGCHLD: watchdog,
#                      signal.SIGHUP: reload
#                     }

#with context:
#  runworkers()

class Worker(multiprocessing.Process):
  """Worker class"""
  _application = None
  ssl_options = None
  _context = daemon.DaemonContext()

  def __init__(self, application,
               no_keep_alive=False,
               io_loop=None,
               xheaders=False,
               ssl_options=None,
               server=server.HTTPServer,
               **kwargs):
    self._application = application
    self.xheaders = xheaders
    self.io_loop = io_loop or tornado.ioloop.IOLoop.instance().start()
    self.ssl_options = ssl_options
    self.server = server
    super(Worker, self).__init__(**kwargs)

  def run(self):
    """Starts Tornado compatible worker"""
    setproctitle.setproctitle(self.name)
    server = self.server(self._application,
                         self.ssl_options)
    try:
      server.listen(self.port, self.address)
      self.io_loop.start()
    except IOError, e:
      print e.message
      exit(0)
    return 0

  def listen(self, port, address):
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
      options.foreground = True


class Runner(object):
  """Runner class"""
  _workers = []
  _starting = True
  _closing = False

  def __init__(self, application, worker=Worker):
    self.application = application
    self.worker = worker
    context = daemon.DaemonContext(working_directory=options.workdir,
                                   pidfile=options.pidfile and options.pidfile or None,
                                   detach_process=not options.foreground,
                                   uid=options.user and pwd.getpwnam(options.user).pw_uid or None,
                                   gid=options.group and grp.getgrnam(options.group).gr_gid or None,
                                   stdout=options.stdout,
                                   stderr=options.stderr
                                  )
    context.signal_map = {signal.SIGTERM: self._stop,
                      signal.SIGINT: self._stop,
                      signal.SIGCHLD: self._watchdog,
                      signal.SIGHUP: self._reload
                     }
    self._context = context
    setproctitle.setproctitle(application.name)

  def createworkers(self):
    """Creates Worker class subprocesses"""
    for w in range(options.workers):
      port = options.port + w
      worker = self.worker(self.application,
                           ssl_options={
                                        'certfile': options.cert,
                                        'keyfile': options.key,
                                        'ca_certs': options.cacerts,
                                        'ssl_cersion': options.sslver,
                                        'cert_req': options.certreq},
                           name='worker%d' % port
                          )
      worker.listen(port, options.address)
      self._workers.append(worker)

  def loadconfig(self):
    """Loads config from commandline and config file"""
    tornado.options.parse_command_line()
    try:
      tornado.options.parse_config_file(options.config)
    except IOError, e:
      logging.debug(e.strerror + ': ' + options.config)
      logging.debug('Using defaults')
    tornado.options.parse_command_line()
    tornado.options.enable_pretty_logging()
    if options.debug:
      print 'Debug Enabled'
      options.foreground = True
      options.stderr = sys.stderr
      options.out = sys.stdout
    else:
      options.err = open(options.logfile, 'a', False)
      options.out = open(options.logfile, 'a', False)

  def start(self):
    """Starts main proccess and workers"""
    try:
      self._context.open()
    except:
      pass
    self.createworkers()
    logging.info('Main proccess started PID: %d' % os.getpid())
    for worker in self._workers:
      worker.start()
      logging.info('Worker started PID: %d, listen on port: %d' % (worker.pid, worker.port))
    self._starting = False
    self._loop()

  def execute(self):
    """Equivalent to
    Runner.loadconfig()
    Runner.start()
    """
    self.loadconfig()
    #self.createworkers()
    self.start()

  def _loop(self):
    while True:
      time.sleep(1)

  def _stop(self, signal, frame):
    self._closing = True
    logging.info('Signal %d recived PID: %d' % (signal, os.getpid()))
    logging.info('Stopping workers')
    for worker in self._workers:
      try:
        worker.terminate()
      except:
        pass
    exit(0)

  def _watchdog(self, signal, frame):
    for worker in self._workers:
      if not worker.is_alive():
        logging.info('Signal SIGCHLD recived worker "%s" died' % worker.name)
    if(self._starting or self._closing):
      exit(0)

  def _reload(self, signal, frame):
    logging.info('Signal SIGHUP recived please restart to reload')

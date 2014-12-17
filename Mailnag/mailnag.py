#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# mailnag.py
#
# Copyright 2011 - 2014 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2011 Leighton Earl <leighton.earl@gmx.com>
# Copyright 2011 Ralf Hersel <ralf.hersel@gmx.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
#

from gi.repository import GObject, GLib
from dbus.mainloop.glib import DBusGMainLoop
import threading
import argparse
import logging
import logging.handlers
import os
import signal

from common.config import cfg_exists
from common.dist_cfg import APP_VERSION
from common.utils import set_procname, shutdown_existing_instance
from common.subproc import terminate_subprocesses
from common.exceptions import InvalidOperationException
from daemon.mailnagdaemon import MailnagDaemon

PROGNAME = 'mailnagd'

LOG_LEVEL = logging.DEBUG
LOG_FORMAT = '%(levelname)s (%(asctime)s): %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def cleanup(daemon):
	event = threading.Event()
	def thread():
		if daemon != None:
			daemon.dispose()
		
		terminate_subprocesses(timeout = 3.0)
		event.set()
		
	threading.Thread(target = thread).start()
	event.wait(10.0)
	
	if not event.is_set():
		logging.warning('Cleanup takes too long. Enforcing termination.')
		os._exit(os.EX_SOFTWARE)
	
	if threading.active_count() > 1:
		logging.warning('There are still active threads. Enforcing termination.')
		os._exit(os.EX_SOFTWARE)


def get_args():
	parser = argparse.ArgumentParser(prog=PROGNAME)
	parser.add_argument('-q', '--quiet', action = 'store_true', 
		help = "don't print log messages to stdout")
	parser.add_argument('-v', '--version', action = 'version',
		version = 'Mailnag %s' % APP_VERSION)
	parser.add_argument('-f', '--foreground', action = 'store_true',
		help = "don't run mailnagd in daemon mode")
	
	return parser.parse_args()


def init_logging(enable_stdout = True):
	logging.basicConfig(
		format = LOG_FORMAT,
		datefmt = LOG_DATE_FORMAT,
		level = LOG_LEVEL)
	
	logger = logging.getLogger('')
	
	syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
	syslog_handler.setLevel(LOG_LEVEL)
	syslog_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
	
	stdout_handler = logger.handlers[0]
	
	logger.addHandler(syslog_handler)
	
	if not enable_stdout:
		logger.removeHandler(stdout_handler)	


def sigterm_handler(mainloop):
	if mainloop != None:
		mainloop.quit()


def main():
	mainloop = GLib.MainLoop()
	daemon = None
	
	set_procname(PROGNAME)
	GObject.threads_init()
	DBusGMainLoop(set_as_default = True)
	GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGTERM, 
		sigterm_handler, mainloop)
	
	# Get commandline arguments
	args = get_args()
	
	# Shut down an (possibly) already running Mailnag daemon
	# (must be called before instantiation of the DBUSService).
	shutdown_existing_instance()
	
	# Note: don't start logging before an existing Mailnag 
	# instance has been shut down completely (will corrupt logfile).
	init_logging(not args.quiet)
	
	try:
		if not cfg_exists():
			logging.critical(
				"Cannot find configuration file. " + \
				"Please run mailnag-config first.")
			exit(1)
		
		def fatal_error_hdlr(ex):
			# Note: don't raise an exception 
			# (e.g InvalidOperationException) 
			# in the error handler.
			mainloop.quit()
			
		def shutdown_request_hdlr():
			if not mainloop.is_running():
				raise InvalidOperationException(
					"Mainloop is not running")
			mainloop.quit()
		
		daemon = MailnagDaemon(
			fatal_error_hdlr, 
			shutdown_request_hdlr)
		
		daemon.init()
				
		# start mainloop for DBus communication
		mainloop.run()
	
	except KeyboardInterrupt:
		pass # ctrl+c pressed
	finally:
		logging.info('Shutting down...')
		cleanup(daemon)


if __name__ == '__main__': main()

#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# mailnag.py
#
# Copyright 2011 - 2013 Patrick Ulbrich <zulu99@gmx.net>
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
import time
import signal

from common.config import read_cfg, cfg_exists, cfg_folder
from common.utils import set_procname, is_online, shutdown_existing_instance
from common.accounts import AccountList
from common.plugins import Plugin, HookRegistry, MailnagController
from common.subproc import terminate_subprocesses
from daemon.mailchecker import MailChecker
from daemon.idlers import IdlerRunner

PROGNAME = 'mailnagd'

LOG_LEVEL = logging.DEBUG
LOG_FORMAT = '%(levelname)s (%(asctime)s): %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

mainloop = None
idlrunner = None
plugins = []
hook_registry = HookRegistry()
start_thread = None
poll_thread = None
poll_thread_stop = threading.Event()


# Mailnag controller implementation passed to plugins
class MailnagController_Impl(MailnagController):
	def __init__(self, hookreg):
		MailnagController.__init__(self, hookreg)
	
	
	def shutdown(self):
		if mainloop != None:
			mainloop.quit()
			return True
		else:
			return False
	
	
	def check_for_mails(self):
		if (mailchecker != None): #and (non_idle_accounts != None):
		#	TODO mailchecker.check(non_idle_accounts)
			return True
		else:
			return False
	
	
def read_config():
	if not cfg_exists():
		return None
	else:
		return read_cfg()


def wait_for_inet_connection():
	if not is_online():
		logging.info('Waiting for internet connection...')
		while not is_online():
			time.sleep(5)


def cleanup():
	event = threading.Event()
	def thread():
		# clean up resources
		if (start_thread != None) and (start_thread.is_alive()):
			start_thread.join()
			logging.info('Starter thread exited successfully.')

		if (poll_thread != None) and (poll_thread.is_alive()):
			poll_thread_stop.set()
			poll_thread.join()
			logging.info('Polling thread exited successfully.')
	
		if idlrunner != None:
			idlrunner.dispose()

		# Clear vars used in the MailnagController 
		# so plugins can't perform unwanted calls to 
		# shutdown() or check_for_mail() 
		# when being disabled on shut down.
		mainloop = None
		mailchecker = None
	
		unload_plugins()
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
	parser.add_argument('--quiet', action = 'store_true', 
		help = "don't print log messages to stdout")
	
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


def sigterm_handler(data):
	if mainloop != None:
		mainloop.quit()


def load_plugins(cfg, hookreg):
	global plugins
	controller = MailnagController_Impl(hookreg)
	
	enabled_lst = cfg.get('core', 'enabled_plugins').split(',')
	enabled_lst = filter(lambda s: s != '', map(lambda s: s.strip(), enabled_lst))
	plugins = Plugin.load_plugins(cfg, controller, enabled_lst)
	
	for p in plugins:
		try:
			p.enable()
			logging.info("Successfully enabled plugin '%s'." % p.get_modname())
		except:
			logging.error("Failed to enable plugin '%s'." % p.get_modname())


def unload_plugins():
	if len(plugins) > 0:
		err = False
		
		for p in plugins:
			try:
				p.disable()
			except:
				err = True
				logging.error("Failed to disable plugin '%s'." % p.get_modname())
		
		if not err:
			logging.info('Plugins disabled successfully.')


def main():
	global mainloop, start_thread
	
	set_procname(PROGNAME)
	GObject.threads_init()
	DBusGMainLoop(set_as_default = True)
	GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGTERM, 
		sigterm_handler, None)
	
	# Get commandline arguments
	args = get_args()
	
	# shut down an (possibly) already running Mailnag daemon
	# (must be called before instantiation of the DBUSService).
	shutdown_existing_instance()
	
	# Note: don't start logging before an existing Mailnag 
	# instance has been shut down completely (will corrupt logfile).
	init_logging(not args.quiet)
	
	try:
		cfg = read_config()
		
		if cfg == None:
			logging.critical('Cannot find configuration file. Please run mailnag-config first.')
			exit(1)
		
		wait_for_inet_connection()
		
		load_plugins(cfg, hook_registry)
				
		# start checking for mails asynchronously 
		start_thread = threading.Thread(target = start, args = (cfg, hook_registry, ))
		start_thread.start()
		
		# start mainloop for DBus communication
		mainloop = GObject.MainLoop()
		mainloop.run()
	
	except KeyboardInterrupt:
		pass # ctrl+c pressed
	finally:
		logging.info('Shutting down...')
		cleanup()


def start(cfg, hookreg):
	global poll_thread, idlrunner
	
	try:
		accounts = AccountList()
		accounts.load_from_cfg(cfg, enabled_only = True)
		
		mailchecker = MailChecker(cfg, hookreg)
		
		# immediate check, check *all* accounts
		try:		
			mailchecker.check(accounts)
		except:
			logging.exception('Caught an exception.')
		
		idle_accounts = filter(lambda acc: acc.imap and acc.idle, accounts)
		non_idle_accounts = filter(lambda acc: (not acc.imap) or (acc.imap and not acc.idle), accounts)
	
		# start polling thread for POP3 accounts and
		# IMAP accounts without idle support
		if len(non_idle_accounts) > 0:
			check_interval = int(cfg.get('core', 'check_interval'))
		
			def poll_func():
				try:
					while True:
						poll_thread_stop.wait(timeout = 60.0 * check_interval)
						if poll_thread_stop.is_set():
							break
					
						mailchecker.check(non_idle_accounts)
				except:
					logging.exception('Caught an exception.')
		
			poll_thread = threading.Thread(target = poll_func)
			poll_thread.start()
		
	
		# start idler threads for IMAP accounts with idle support
		if len(idle_accounts) > 0:
			def sync_func(account):
				try:
					mailchecker.check([account])
				except:
					logging.exception('Caught an exception.')

		
			idlrunner = IdlerRunner(idle_accounts, sync_func)
			idlrunner.run()
	except:
		logging.exception('Caught an exception.')
		mainloop.quit()
		

if __name__ == '__main__': main()

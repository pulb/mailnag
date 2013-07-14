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
import time
import signal
import traceback

from common.config import read_cfg, cfg_exists, cfg_folder
from common.utils import set_procname, is_online, shutdown_existing_instance
from common.accountlist import AccountList
from common.plugins import Plugin, HookRegistry, MailnagController
from daemon.mailchecker import MailChecker
from daemon.idlers import Idlers

mainloop = None
idlers = None
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
		print 'Waiting for internet connection...'
		while not is_online():
			time.sleep(5)


def cleanup():
	# clean up resources
	if (start_thread != None) and (start_thread.is_alive()):
		start_thread.join()
		print "Starter thread exited successfully"

	if (poll_thread != None) and (poll_thread.is_alive()):
		poll_thread_stop.set()
		poll_thread.join()
		print "Polling thread exited successfully"
	
	if idlers != None:
		idlers.dispose()

	# Clear vars used in the MailnagController 
	# so plugins can't perform unwanted calls to 
	# shutdown() or check_for_mail() 
	# when being disabled on shut down.
	mainloop = None
	mailchecker = None
	
	unload_plugins()


def sig_handler(signum, frame):
	if mainloop != None:
		mainloop.quit()


def load_plugins(cfg, hookreg):
	global plugins
	controller = MailnagController_Impl(hookreg)
	
	enabled_lst = cfg.get('general', 'enabled_plugins').split(',')
	enabled_lst = filter(lambda s: s != '', map(lambda s: s.strip(), enabled_lst))
	plugins = Plugin.load_plugins(cfg, controller, enabled_lst)
	
	for p in plugins:
		try:
			p.enable()
			print "Successfully enabled plugin '%s'" % p.get_modname()
		except:
			print "Failed to enable plugin '%s'" % p.get_modname()


def unload_plugins():
	if len(plugins) > 0:
		err = False
		
		for p in plugins:
			try:
				p.disable()
			except:
				err = True
				print "Failed to disable plugin '%s'" % p.get_modname()
		
		if not err:
			print "Plugins disabled successfully"


def main():
	global mainloop, start_thread
	
	set_procname("mailnag")
	
	GObject.threads_init()
	DBusGMainLoop(set_as_default = True)
	signal.signal(signal.SIGTERM, sig_handler)
	
	# shut down an (possibly) already running Mailnag daemon
	# (must be called before instantiation of the DBUSService).
	shutdown_existing_instance()
	
	try:
		cfg = read_config()
		
		if (cfg == None):
			print 'Error: Cannot find configuration file. Please run mailnag_config first.'
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
		print "Shutting down..."
		cleanup()


def start(cfg, hookreg):
	global poll_thread, idlers
	
	try:
		accounts = AccountList()
		accounts.load_from_cfg(cfg, enabled_only = True)
		
		mailchecker = MailChecker(cfg, hookreg)
		
		# immediate check, check *all* accounts
		try:		
			mailchecker.check(accounts)
		except:
			traceback.print_exc()
		
		idle_accounts = filter(lambda acc: acc.imap and acc.idle, accounts)
		non_idle_accounts = filter(lambda acc: (not acc.imap) or (acc.imap and not acc.idle), accounts)
	
		# start polling thread for POP3 accounts and
		# IMAP accounts without idle support
		if len(non_idle_accounts) > 0:
			check_interval = int(cfg.get('general', 'check_interval'))
		
			def poll_func():
				try:
					while (True):
						poll_thread_stop.wait(timeout = 60.0 * check_interval)
						if poll_thread_stop.is_set():
							break
					
						mailchecker.check(non_idle_accounts)
				except:
					traceback.print_exc()
		
			poll_thread = threading.Thread(target = poll_func)
			poll_thread.start()
		
	
		# start idler threads for IMAP accounts with idle support
		if len(idle_accounts) > 0:
			def sync_func(account):
				try:
					mailchecker.check([account])
				except:
					traceback.print_exc()

		
			idlers = Idlers(idle_accounts, sync_func)
			idlers.run()
	except:
		traceback.print_exc()
		mainloop.quit()
		

if __name__ == '__main__': main()

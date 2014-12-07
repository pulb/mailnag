#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# mailnagdaemon.py
#
# Copyright 2014 Patrick Ulbrich <zulu99@gmx.net>
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

import threading
import logging

from common.accounts import AccountList
from daemon.mailchecker import MailChecker
from daemon.mails import Memorizer
from daemon.idlers import IdlerRunner
from common.plugins import Plugin, HookRegistry, HookTypes, MailnagController
from common.exceptions import InvalidOperationException
from common.config import read_cfg
from common.utils import try_call


class MailnagDaemon:
	def __init__(self, fatal_error_handler = None, shutdown_request_handler = None):
		self._cfg = None
		self._fatal_error_handler = fatal_error_handler
		self._shutdown_request_handler = shutdown_request_handler
		self._plugins = []
		self._hookreg = None
		self._accounts = None
		self._mailchecker = None
		self._start_thread = None
		self._poll_thread = None
		self._poll_thread_stop = threading.Event()
		self._idlrunner = None
		# Lock ensures that init() and dispose() 
		# are non-reentrant.
		self._lock = threading.Lock()
		# Flag indicating complete 
		# daemon initialization.
		self._initialized = False
		self._disposed = False
	
	
	# Initializes the daemon and starts checking threads.
	def init(self):			
		with self._lock:
			if self._disposed:
				raise InvalidOperationException("Daemon has been disposed")
		
			if self._initialized:
				raise InvalidOperationException("Daemon has already been initialized")
			
			self._cfg = read_cfg()
			self._accounts = AccountList()
			self._accounts.load_from_cfg(self._cfg, enabled_only = True)
			self._hookreg = HookRegistry()

			memorizer = Memorizer()
			memorizer.load()

			self._mailchecker = MailChecker(self._cfg, memorizer, self._hookreg)

			# Note: all code following _load_plugins() should be executed
			# asynchronously because the dbus plugin requires an active mainloop
			# (usually started in the programs main function).
			self._load_plugins(self._cfg, self._hookreg, memorizer)

			# Start checking for mails asynchronously.
			self._start_thread = threading.Thread(target = self._start)
			self._start_thread.start()

			self._initialized = True
	
	
	def dispose(self):
		with self._lock:
			if self._disposed:
				return

		# Note: _disposed must be set 
		# before cleaning up resources 
		# (in case an exception occurs) 
		# and before unloading plugins.
		self._disposed = True
		
		# clean up resources
		if (self._start_thread != None) and (self._start_thread.is_alive()):
			self._start_thread.join()
			logging.info('Starter thread exited successfully.')

		if (self._poll_thread != None) and (self._poll_thread.is_alive()):
			self._poll_thread_stop.set()
			self._poll_thread.join()
			logging.info('Polling thread exited successfully.')

		if self._idlrunner != None:
			self._idlrunner.dispose()

		if self._accounts != None:
			for acc in self._accounts:
				if acc.has_connection():
					if acc.imap:
						conn = acc.get_connection(use_existing = True)
						conn.close()
						conn.logout()
					else:
						conn.quit()

		self._unload_plugins()
	
	
	def is_initialized(self):
		return self._initialized
	
	
	def is_disposed(self):
		return self._disposed
	
	
	# Enforces manual mail checks
	def check_for_mails(self):
		# Don't allow mail checks before initialization or
		# after object disposal. F.i. plugins may not be 
		# loaded/unloaded completely or connections may 
		# have been closed already.
		self._ensure_valid_state()
		
		non_idle_accounts = filter(lambda acc: (not acc.imap) or 
			(acc.imap and not acc.idle), self._accounts)
		self._mailchecker.check(non_idle_accounts)
	
	
	def _ensure_valid_state(self):
		if not self._initialized:
			raise InvalidOperationException(
				"Daemon has not been initialized")
		
		if self._disposed:
			raise InvalidOperationException(
				"Daemon has been disposed")
	
	
	def _start(self):
		try:
			# Call Accounts-Loaded plugin hooks
			lst = self._accounts[:]
			for f in self._hookreg.get_hook_funcs(HookTypes.ACCOUNTS_LOADED):
				try_call( lambda: f(lst) )
			self._accounts[:] = lst
			
			# Immediate check, check *all* accounts
			try:
				self._mailchecker.check(self._accounts)
			except:
				logging.exception('Caught an exception.')

			idle_accounts = filter(lambda acc: acc.imap and acc.idle, self._accounts)
			non_idle_accounts = filter(lambda acc: (not acc.imap) or 
				(acc.imap and not acc.idle), self._accounts)

			# start polling thread for POP3 accounts and
			# IMAP accounts without idle support
			if len(non_idle_accounts) > 0:
				poll_interval = int(self._cfg.get('core', 'poll_interval'))

				def poll_func():
					try:
						while True:
							self._poll_thread_stop.wait(timeout = 60.0 * poll_interval)
							if self._poll_thread_stop.is_set():
								break

							self._mailchecker.check(non_idle_accounts)
					except:
						logging.exception('Caught an exception.')

				self._poll_thread = threading.Thread(target = poll_func)
				self._poll_thread.start()

			# start idler threads for IMAP accounts with idle support
			if len(idle_accounts) > 0:
				def sync_func(account):
					try:
						self._mailchecker.check([account])
					except:
						logging.exception('Caught an exception.')


				idle_timeout = int(self._cfg.get('core', 'imap_idle_timeout'))				
				self._idlrunner = IdlerRunner(idle_accounts, sync_func, idle_timeout)
				self._idlrunner.start()
		except Exception as ex:
			logging.exception('Caught an exception.')
			if self._fatal_error_handler != None:
				self._fatal_error_handler(ex)
	

	def _load_plugins(self, cfg, hookreg, memorizer):
		class MailnagController_Impl(MailnagController):
			def __init__(self, daemon, memorizer, hookreg, shutdown_request_hdlr):
				self._daemon = daemon
				self._memorizer = memorizer
				self._hookreg = hookreg
				self._shutdown_request_handler = shutdown_request_hdlr
				
			def get_hooks(self):
				return self._hookreg
			
			def shutdown(self):
				if self._shutdown_request_handler != None:
					self._shutdown_request_handler()
			
			def check_for_mails(self):
				self._daemon.check_for_mails()
			
			def mark_mail_as_read(self, mail_id):
				# Note: ensure_valid_state() is not really necessary here
				# (the memorizer object is available in init() and dispose()), 
				# but better be consistent with other daemon methods.
				self._daemon._ensure_valid_state()
				self._memorizer.set_to_seen(mail_id)
				self._memorizer.save()
		
		controller = MailnagController_Impl(self, memorizer, hookreg, self._shutdown_request_handler)
	
		enabled_lst = cfg.get('core', 'enabled_plugins').split(',')
		enabled_lst = filter(lambda s: s != '', map(lambda s: s.strip(), enabled_lst))
		self._plugins = Plugin.load_plugins(cfg, controller, enabled_lst)
	
		for p in self._plugins:
			try:
				p.enable()
				logging.info("Successfully enabled plugin '%s'." % p.get_modname())
			except:
				logging.error("Failed to enable plugin '%s'." % p.get_modname())
	

	def _unload_plugins(self):
		if len(self._plugins) > 0:
			err = False
		
			for p in self._plugins:
				try:
					p.disable()
				except:
					err = True
					logging.error("Failed to disable plugin '%s'." % p.get_modname())
		
			if not err:
				logging.info('Plugins disabled successfully.')



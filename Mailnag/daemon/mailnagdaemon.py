# Copyright 2016 Timo Kankare <timo.kankare@iki.fi>
# Copyright 2014 - 2020 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2020 Andreas Angerer
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
import time

from Mailnag.common.accounts import AccountManager
from Mailnag.daemon.mailchecker import MailChecker
from Mailnag.daemon.mails import Memorizer
from Mailnag.daemon.idlers import IdlerRunner
from Mailnag.daemon.conntest import ConnectivityTest, TestModes
from Mailnag.daemon.dbus import DBusService
from Mailnag.common.plugins import Plugin, HookRegistry, HookTypes, MailnagController
from Mailnag.common.exceptions import InvalidOperationException
from Mailnag.common.config import read_cfg
from Mailnag.common.utils import try_call


testmode_mapping = {
	'auto'				: TestModes.AUTO,
	'networkmanager'	: TestModes.NETWORKMANAGER,
	'ping'				: TestModes.PING
}

class MailnagDaemon(MailnagController):
	def __init__(self, fatal_error_handler = None, shutdown_request_handler = None):
		self._fatal_error_handler = fatal_error_handler
		self._shutdown_request_handler = shutdown_request_handler
		self._plugins = []
		self._poll_thread = None
		self._poll_thread_stop = threading.Event()
		self._idlrunner = None
		self._disposed = False
	
		self._cfg = read_cfg()
		
		accountman = AccountManager()
		accountman.load_from_cfg(self._cfg, enabled_only = True)
		self._accounts = accountman.to_list()
		self._hookreg = HookRegistry()
		self._conntest = ConnectivityTest(testmode_mapping[self._cfg.get('core', 'connectivity_test')])
		
		self._memorizer = Memorizer()
		self._memorizer.load()
		
		dbus_service = DBusService(self)

		self._mailchecker = MailChecker(self._cfg, self._memorizer, self._hookreg, self._conntest, dbus_service)

		# Note: all code following _load_plugins() should be executed
		# asynchronously because the dbus plugin requires an active mainloop
		# (usually started in the programs main function).
		self._load_plugins(self._cfg)

		# Start checking for mails asynchronously.
		self._start_thread = threading.Thread(target = self._start)
		self._start_thread.start()
	
	
	def dispose(self):
		if self._disposed:
			return

		# Note: _disposed must be set 
		# before cleaning up resources 
		# (in case an exception occurs) 
		# and before unloading plugins.
		# Also required by _wait_for_inet_connection().
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
				if acc.is_open():
					acc.close()

		self._unload_plugins()
	
	
	def is_disposed(self):
		return self._disposed
	
	
	# Part of MailnagController interface
	def get_hooks(self):
		# Note: ensure_not_disposed() cannot be called here
		# because plugins are calling get_hooks() when being disabled in dispose().
		# self._ensure_not_disposed()
		return self._hookreg
	

	# Part of MailnagController interface
	def shutdown(self):
		if self._shutdown_request_handler != None:
			self._shutdown_request_handler()
	
	
	# Part of MailnagController interface
	def mark_mail_as_read(self, mail_id):
		# Note: ensure_not_disposed() is not really necessary here
		# (the memorizer object is available in dispose()), 
		# but better be consistent with other daemon methods.
		self._ensure_not_disposed()
		
		self._memorizer.set_to_seen(mail_id)
		self._memorizer.save()
	
	
	# Enforces manual mail checks
	# Part of MailnagController interface
	def check_for_mails(self):
		# Don't allow mail checks after object disposal. 
		# F.i. plugins may not be unloaded completely or 
		# connections may have been closed already.
		self._ensure_not_disposed()
		
		non_idle_accounts = self._get_non_idle_accounts(self._accounts)
		self._mailchecker.check(non_idle_accounts)

		
	def _ensure_not_disposed(self):
		if self._disposed:
			raise InvalidOperationException(
				"Daemon has been disposed")
	
	
	def _start(self):
		try:
			# Call Accounts-Loaded plugin hooks
			for f in self._hookreg.get_hook_funcs(HookTypes.ACCOUNTS_LOADED):
				try_call( lambda: f(self._accounts) )
			
			if not self._wait_for_inet_connection():
				return
			
			# Immediate check, check *all* accounts
			try:
				self._mailchecker.check(self._accounts)
			except:
				logging.exception('Caught an exception.')

			idle_accounts = self._get_idle_accounts(self._accounts)
			non_idle_accounts = self._get_non_idle_accounts(self._accounts)

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
	

	def _wait_for_inet_connection(self):
		if self._conntest.is_offline():
			logging.info('Waiting for internet connection...')
		
		while True:
			if self._disposed:					return False
			if not self._conntest.is_offline():	return True
			# Note: don't sleep too long
			# (see timeout in mailnag.cleanup())
			# ..but also don't sleep to short in case of a ping connection test.
			time.sleep(3)


	def _get_idle_accounts(self, accounts):
		return [acc for acc in self._accounts if acc.supports_notifications()]


	def _get_non_idle_accounts(self, accounts):
		return [acc for acc in self._accounts if not acc.supports_notifications()]


	def _load_plugins(self, cfg):
		enabled_lst = cfg.get('core', 'enabled_plugins').split(',')
		enabled_lst = [s for s in [s.strip() for s in enabled_lst] if s != '']
		self._plugins = Plugin.load_plugins(cfg, self, enabled_lst)
	
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



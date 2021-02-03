# Copyright 2011 - 2021 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2016, 2018 Timo Kankare <timo.kankare@iki.fi>
# Copyright 2011 Leighton Earl <leighton.earl@gmx.com>
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
import time
import logging
from Mailnag.common.exceptions import InvalidOperationException


#
# Idler class
#
class Idler(object):
	def __init__(self, account, sync_callback, idle_timeout):
		self.RECONNECT_RETRY_INTERVAL = 5 # minutes
		
		self._thread = threading.Thread(target=self._idle)
		self._event = threading.Event()
		self._sync_callback = sync_callback
		self._account = account
		self._idle_timeout = idle_timeout
		self._disposing = False
		self._disposed = False


	def start(self):
		if self._disposed:
			raise InvalidOperationException("Idler has been disposed")
			
		self._thread.start()

		
	def dispose(self):
		if self._thread.is_alive():
			# flag a shutdown
			self._disposing = True
			# unblock idle event the _idle thread is waiting for
			self._event.set()
			self._thread.join()
		
		self._disposed = True
		logging.info('Idler closed')

		
	# idle thread
	def _idle(self):
		# mailbox may have been opened in mailnagdaemon.py already (immediate check)
		while (not self._account.is_open()) and (not self._disposing):
			try:
				self._account.open()
			except Exception as ex:
				logging.error("Failed to open mailbox for account '%s' (%s)." % (self._account.name, ex), exc_info=True)
				logging.info("Trying to reconnect Idler thread for account '%s' in %s minutes" % 
					(self._account.name, str(self.RECONNECT_RETRY_INTERVAL)))
				self._wait(60 * self.RECONNECT_RETRY_INTERVAL) # don't hammer the server

		while not self._disposing:
			self._needsync = False
			self._needreset = False
			
			try:
				self._account.notify_next_change(callback = self._idle_callback, timeout = 60 * self._idle_timeout)
			
				# waits for the event to be set
				# (in idle callback or in dispose())
				self._event.wait()
			except:				
				logging.exception('Caught an exception.')
				# Reset current connection if the call to notify_next_change() fails
				# as this is probably connection related (e.g. conn terminated).
				self._reset_conn()
			
			# if the event is set due to idle sync
			if self._needsync:			
				if self._needreset:
					self._reset_conn()
				
				# NOTE: the event must be cleared after resetting (closing) the connection
				# so no more callbacks (that may set the event again) can occur.
				self._event.clear()
				
				if self._account.is_open():
					try:
						# Fetch and sync mails from account
						self._sync_callback(self._account)
					except:
						logging.exception('Caught an exception.')
						# Reset current connection if the call to sync_callback() (mail sync) fails.
						# An immediate sync has already been performed successfully on startup,
						# so if an error occurs here, it may be connection related (e.g. conn terminated).
						self._reset_conn()

		self._account.cancel_notifications()
		
	
	# idle callback (runs on a further thread)
	def _idle_callback(self, error):
		# flag that a mail sync is needed
		self._needsync = True
		
		# flag the need for a connection reset in case of an error (e.g. conn terminated)
		if error is not None:
			error_type, error_val = error
			logging.error("Idle callback for account '%s' returned an error (%s - %s)." % (self._account.name, error_type, str(error_val)))
			self._needreset = True
		
		# trigger waiting _idle thread
		self._event.set()
	
			
	def _reset_conn(self):
		# Try to reset the connection to recover from a possible connection error (e.g. after system suspend)
		logging.info("Resetting connection for account '%s'" % self._account.name)
		try: self._account.close()
		except:	pass
		self._reconnect()
		
	
	def _reconnect(self):
		# connection has been reset by provider -> try to reconnect
		logging.info("Idler thread for account '%s' has been disconnected" % self._account.name)

		while (not self._account.is_open()) and (not self._disposing):
			logging.info("Trying to reconnect Idler thread for account '%s'." % self._account.name)
			try:
				self._account.open()
				logging.info("Successfully reconnected Idler thread for account '%s'." % self._account.name)
			except Exception as ex:
				logging.error("Failed to reconnect Idler thread for account '%s' (%s)." % (self._account.name, ex), exc_info=True)
				logging.info("Trying to reconnect Idler thread for account '%s' in %s minutes" % 
					(self._account.name, str(self.RECONNECT_RETRY_INTERVAL)))
				self._wait(60 * self.RECONNECT_RETRY_INTERVAL) # don't hammer the server
	
					
	def _wait(self, secs):
		start_time = time.time()
		while (((time.time() - start_time) < secs) and (not self._disposing)):
			time.sleep(1)


#
# IdlerRunner class
#
class IdlerRunner:
	def __init__(self, accounts, sync_callback, idle_timeout):
		self._idlerlist = []
		self._accounts = accounts
		self._sync_callback = sync_callback
		self._idle_timeout = idle_timeout
	
	
	def start(self):
		for acc in self._accounts:
			if acc.supports_notifications():
				try:
					idler = Idler(acc, self._sync_callback, self._idle_timeout)
					idler.start()
					self._idlerlist.append(idler)
				except Exception as ex:
					logging.error("Error: Failed to create an idler thread for account '%s' (%s)" % (acc.name, ex), exc_info=True)
					
	
	def dispose(self):
		for idler in self._idlerlist:
			idler.dispose()


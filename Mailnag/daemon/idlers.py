#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# idlers.py
#
# Copyright 2011 - 2016 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2016 Timo Kankare <timo.kankare@iki.fi>
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
		self._disposed = False


	def start(self):
		if self._disposed:
			raise InvalidOperationException("Idler has been disposed")
			
		self._thread.start()

		
	def dispose(self):
		if self._thread.is_alive():
			self._event.set()
			self._thread.join()
		
		self._disposed = True
		logging.info('Idler closed')

		
	# idle thread
	def _idle(self):
		# mailbox has been opened in mailnagdaemon.py already (immediate check)
		if not self._account.is_open():
			self._account.open()

		while True:
			# if the event is set here, 
			# disposed() must have been called
			# so stop the idle thread.
			if self._event.isSet():
				break
			
			self._needsync = False

			self._account.notify_next_change(callback = self._idle_callback, timeout = 60 * self._idle_timeout)
			
			# waits for the event to be set
			# (in idle callback or in dispose())
			self._event.wait()
			
			# if the event is set due to idle sync
			if self._needsync:
				self._event.clear()
				if not self._account.is_open():
					self._reconnect()
				
				if self._account.is_open():
					self._sync_callback(self._account)

		self._account.cancel_notifications()
		
	
	# idle callback (runs on a further thread)
	def _idle_callback(self, args):
		# flag that a mail sync is needed
		self._needsync = True
		# trigger waiting _idle thread
		self._event.set()
	
			
	def _reconnect(self):
		# connection has been reset by provider -> try to reconnect
		logging.info("Idler thread for account '%s' has been disconnected" % self._account.name)

		while (not self._account.is_open()) and (not self._event.isSet()):
			logging.info("Trying to reconnect Idler thread for account '%s'." % self._account.name)
			try:
				self._account.open()
				logging.info("Successfully reconnected Idler thread for account '%s'." % self._account.name)
			except Exception as ex:
				logging.error("Failed to reconnect Idler thread for account '%s' (%s)." % (self._account.name, ex))
				logging.info("Trying to reconnect Idler thread for account '%s' in %s minutes" % 
					(self._account.name, str(self.RECONNECT_RETRY_INTERVAL)))
				self._wait(60 * self.RECONNECT_RETRY_INTERVAL) # don't hammer the server
	
					
	def _wait(self, secs):
		start_time = time.time()
		while (((time.time() - start_time) < secs) and (not self._event.isSet())):
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
			if acc.imap and acc.idle:
				try:
					idler = Idler(acc, self._sync_callback, self._idle_timeout)
					idler.start()
					self._idlerlist.append(idler)
				except Exception as ex:
					logging.error("Error: Failed to create an idler thread for account '%s' (%s)" % (acc.name, ex))
					
	
	def dispose(self):
		for idler in self._idlerlist:
			idler.dispose()


#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# idlers.py
#
# Copyright 2011 - 2016 Patrick Ulbrich <zulu99@gmx.net>
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
from Mailnag.common.imaplib2 import AUTH
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
		# use_existing = True:
		# connection has been opened in mailnagdaemon.py already (immediate check)
		self._conn = account.get_connection(use_existing = True)
		self._disposed = False
				
		# Need to get out of AUTH mode of fresh connections.
		if self._conn.state == AUTH:
			self._select(self._conn, account)


	def start(self):
		if self._disposed:
			raise InvalidOperationException("Idler has been disposed")
			
		self._thread.start()

		
	def dispose(self):
		if self._thread.is_alive():
			self._event.set()
			self._thread.join()
		
		try:
			if self._conn != None:
				# Exit possible active idle state.
				# (also calls idle_callback)
				self._conn.noop()
		except:
			pass
		
		self._disposed = True
		logging.info('Idler closed')

		
	# idle thread
	def _idle(self):
		while True:
			# if the event is set here, 
			# disposed() must have been called
			# so stop the idle thread.
			if self._event.isSet():
				return
			
			self._needsync = False
			self._conn_closed = False

			# register idle callback that is called whenever an idle event arrives (new mail / mail deleted).
			# the callback is called after <idle_timeout> minutes at the latest. 
			# gmail sends keepalive events every 5 minutes.
			self._conn.idle(callback = self._idle_callback, timeout = 60 * self._idle_timeout)
			
			# waits for the event to be set
			# (in idle callback or in dispose())
			self._event.wait()
			
			# if the event is set due to idle sync
			if self._needsync:
				self._event.clear()
				if self._conn_closed:
					self._reconnect()
				
				if self._conn != None:
					self._sync_callback(self._account)

	
	# idle callback (runs on a further thread)
	def _idle_callback(self, args):
		# check if the connection has been reset by provider
		self._conn_closed = (args[2] != None) and (args[2][0] is self._conn.abort)
		# flag that a mail sync is needed
		self._needsync = True
		# trigger waiting _idle thread
		self._event.set()
	
			
	def _reconnect(self):
		# connection has been reset by provider -> try to reconnect
		logging.info("Idler thread for account '%s' has been disconnected" % self._account.name)
		
		# conn has already been closed, don't try to close it again
		# self._conn.close() # (calls idle_callback)
		
		# shutdown existing callback thread
		self._conn.logout()
		self._conn = None
		
		while (self._conn == None) and (not self._event.isSet()): 
			logging.info("Trying to reconnect Idler thread for account '%s'." % self._account.name)
			try:
				self._conn = self._account.get_connection(use_existing = False)
				logging.info("Successfully reconnected Idler thread for account '%s'." % self._account.name)
			except Exception as ex:
				logging.error("Failed to reconnect Idler thread for account '%s' (%s)." % (self._account.name, ex))
				logging.info("Trying to reconnect Idler thread for account '%s' in %s minutes" % 
					(self._account.name, str(self.RECONNECT_RETRY_INTERVAL)))
				self._wait(60 * self.RECONNECT_RETRY_INTERVAL) # don't hammer the server
			
		if self._conn != None:
			self._select(self._conn, self._account)
	
					
	def _select(self, conn, account):
		if len(account.folders) == 1:
			conn.select(account.folders[0])
		else:
			conn.select("INBOX")
	
			
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


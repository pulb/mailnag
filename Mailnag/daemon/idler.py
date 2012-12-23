#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# idler.py
#
# Copyright 2011, 2012 Patrick Ulbrich <zulu99@gmx.net>
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
import sys
from daemon.imaplib2 import AUTH

class Idler(object):
	def __init__(self, account, sync_callback):
		self.RECONNECT_RETRY_INTERVAL = 5 # minutes
		
		self._thread = threading.Thread(target=self._idle)
		self._event = threading.Event()
		self._sync_callback = sync_callback
		self._account = account
		# use_existing = True:
		# connection has been opened in mailnag.py already (immediate check)
		self._conn = account.get_connection(use_existing = True)
		self._disposed = False
				
		if self._conn == None:
			raise Exception("Failed to establish a connection for account '%s'" % account.name)
					
		# Need to get out of AUTH mode of fresh connections.
		if self._conn.state == AUTH:
			self._select(self._conn, account.folder)


	def run(self):
		if self._disposed:
			raise Exception("Idler has been disposed")
			
		self._thread.start()

		
	def dispose(self):
		if self._thread.is_alive():
			self._event.set()
			self._thread.join()
		
		try:
			if self._conn != None:
				# (calls idle_callback)
				self._conn.close()
				# shutdown existing callback thread
				self._conn.logout()
		except:
			pass
		
		self._disposed = True
		print "Idler closed"

		
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
			# the callback is called after 10 minutes at the latest. gmail sends keepalive events every 5 minutes.
			self._conn.idle(callback = self._idle_callback, timeout = 60 * 10)
			
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
		print "Idler thread for account '%s' has been disconnected" % self._account.name
		
		# conn has already been closed, don't try to close it again
		# self._conn.close() # (calls idle_callback)
		
		# shutdown existing callback thread
		self._conn.logout()
		self._conn = None
		
		while (self._conn == None) and (not self._event.isSet()): 
			sys.stdout.write("Trying to reconnect Idler thread for account '%s'..." % self._account.name)
			self._conn = self._account.get_connection(use_existing = False)
			if self._conn == None:
				sys.stdout.write("FAILED\n")
				print "Trying again in %s minutes" % self.RECONNECT_RETRY_INTERVAL
				self._wait(60 * self.RECONNECT_RETRY_INTERVAL) # don't hammer the server
			else:
				sys.stdout.write("OK\n")
		
		if self._conn != None:
			self._select(self._conn, self._account.folder)
	
					
	def _select(self, conn, folder):
		folder = folder.strip()
		if len(folder) > 0:
			conn.select(folder)
		else:
			conn.select("INBOX")
	
			
	def _wait(self, secs):
		start_time = time.time()
		while (((time.time() - start_time) < secs) and (not self._event.isSet())):
			time.sleep(1)


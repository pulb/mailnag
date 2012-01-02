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
from daemon.imaplib2 import AUTH

class Idler(object):
	def __init__(self, account, sync_callback):
		self._thread = threading.Thread(target=self._idle)
		self._event = threading.Event()
		self._sync_callback = sync_callback
		self._account = account
		self._conn = account.get_connection(use_existing = True) # connection has been opened in mailnag.py already (immediate check)
		
		if self._conn == None:
			raise Exception("Failed to establish a connection for account '%s'" % account.name)
					
		# Need to get out of AUTH mode of fresh connections.
		if self._conn.state == AUTH:
			self._select(self._conn, account.folder)


	def run(self):
		self._thread.start()

		
	def dispose(self):
		if self._thread.is_alive():
			self._event.set()
			self._thread.join()
		
		try:
			self._conn.close()
			self._conn.logout()
		except:
			pass
		
		print "Idler closed"

		
	def _idle(self):
		while True:
			# If the event is set stop the idle call and therefore thread
			if self._event.isSet():
				return
			self._needsync = False

			def callback(args):
				if (args[2] != None) and (args[2][0] is self._conn.abort):
					# connection has been reset by provider -> reopen
					print "Idler thread for account '%s' reconnected" % self._account.name
					self._conn = self._account.get_connection(use_existing = False)
					self._select(self._conn, self._account.folder)
				
				if not self._event.isSet():
					self._needsync = True
					self._event.set()
			
			# register idle callback that is called whenever an idle event arrives (new mail / mail deleted).
			# the callback is called after 10 minutes at the latest. gmail sends keepalive events every 5 minutes.
			self._conn.idle(callback = callback, timeout = 60 * 10)
			
			# Waits for event to be set
			self._event.wait()
			
			# If the event is set due to idle sync
			if self._needsync:
				self._event.clear()
				self._sync_callback(self._account)

	def _select(self, conn, folder):
		folder = folder.strip()
		if len(folder) > 0:
			conn.select(folder)
		else:
			conn.select("INBOX")


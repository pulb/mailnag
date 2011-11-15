#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# idler.py
#
# Copyright 2011 Leighton Earl <leighton.earl@gmx.com>
# Copyright 2011 Patrick Ulbrich <zulu99@gmx.net>
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

class Idler(object):
	def __init__(self, conn, sync_callback):
		self._thread = threading.Thread(target=self._idle)
		self._conn = conn
		self._event = threading.Event()
		self._sync_callback = sync_callback


	def run(self):
		self._thread.start()

		
	def dispose(self):
		if self._thread.is_alive():
			self._event.set()
			self._thread.join()
		
		self._conn.close()
		self._conn.logout()
		
		print "Idler closed"

		
	def _idle(self):
		while True:
			# If the event is set stop the idle call and therefore thread
			if self._event.isSet():
				return
			self._needsync = False

			def callback(args):
				if not self._event.isSet():
					self._needsync = True
					self._event.set()
			
			self._conn.idle(callback=callback)
			
			# Waits for event to be set
			self._event.wait()
			
			# If the event is set due to idle sync
			if self._needsync:
				self._event.clear()
				self._sync_callback()

	

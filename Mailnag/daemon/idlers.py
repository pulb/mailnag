#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# idlers.py
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

from daemon.idler import Idler

class Idlers:
	def __init__(self, accounts, sync_callback):
		self._idlerlist = []
		self._accounts = accounts
		self._sync_callback = sync_callback
	
	
	def run(self):
		for acc in self._accounts:
			if acc.imap and acc.idle:
				try:
					idler = Idler(acc, self._sync_callback)
					idler.run()
					self._idlerlist.append(idler)
				except Exception as ex:
					print "Error: Failed to create an idler thread for account '%s'" % acc.name
					
	
	def dispose(self):
		for idler in self._idlerlist:
			idler.dispose()


#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# idlers.py
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

from daemon.idler import Idler

class Idlers:
	def __init__(self, accounts, sync_callback):
		self._idlerlist = []
		self._accounts = accounts
		self._sync_callback = sync_callback
	
	
	def run(self):
		for acc in self._accounts.account:
			if acc.imap: # TODO : and enable_push
				try:
					self._new_idler(acc)
				except:
					pass
					
	
	def dispose(self):
		for idler in self._idlerlist:
			idler.dispose()
	
	
	def _new_idler(self, account):
		server = account.get_connection()
		
		if server == None:
			return
					
		# Need to get out of AUTH mode.
		if account.folder:
			server.select(account.folder)
		else:
			server.select("INBOX")
		
		try:
			tmp = server.search(None, 'UNSEEN') # ALL or UNSEEN
		except:
			server.select('INBOX', readonly=True) # If search fails select INBOX and try again
			tmp = server.search(None, 'UNSEEN') # ALL or UNSEEN
		
		idler = Idler(server, self._sync_callback)
		idler.run()
		self._idlerlist.append(idler)


# -*- coding: utf-8 -*-
#
# imap.py
#
# Copyright 2011 - 2016 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2016 Timo Kankare <timo.kankare@iki.fi>
# Copyright 2016 Thomas Haider <t.haider@deprecate.de>
# Copyright 2011 Ralf Hersel <ralf.hersel@gmx.net>
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

import logging
import poplib

class Pop3Backend:
	"""Implementation of POP3 mail boxes."""
	
	def __init__(self, name = '', user = '', password = '', oauth2string = '',
				 server = '', port = '', ssl = True):
		self.name = name
		self.user = user
		self.password = password
		self.oauth2string = oauth2string
		self.server = server
		self.port = port
		self.ssl = ssl # bool
		self._conn = None


	def get_connection(self, use_existing):
		# try to reuse existing connection
		if use_existing and self.has_connection():
			return self._conn
		
		self._conn = conn = None
		
		try:
			if self.ssl:
				if self.port == '':
					conn = poplib.POP3_SSL(self.server)
				else:
					conn = poplib.POP3_SSL(self.server, int(self.port))
			else:
				if self.port == '':
					conn = poplib.POP3(self.server)
				else:
					conn = poplib.POP3(self.server, int(self.port))
				
				# TODO : Use STARTTLS when Mailnag has been migrated to python 3
				# (analogous to get_connection in imap backend).
				logging.warning("Using unencrypted connection for account '%s'" % self.name)
				
			conn.getwelcome()
			conn.user(self.user)
			conn.pass_(self.password)
			
			self._conn = conn
		except:
			try:
				if conn != None:
					conn.quit()
			except:	pass
			raise # re-throw exception
		
		return self._conn


	def has_connection(self):
		return (self._conn != None) and \
				('sock' in self._conn.__dict__)
	

	def request_folders(self):
		lst = []
		return lst


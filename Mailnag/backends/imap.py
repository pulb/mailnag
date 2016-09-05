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
import re
import Mailnag.common.imaplib2 as imaplib

class ImapBackend:
	"""Implementation of IMAP mail boxes."""
	
	def __init__(self, name = '', user = '', password = '', oauth2string = '',
				 server = '', port = '', ssl = True, folders = []):
		self.name = name
		self.user = user
		self.password = password
		self.oauth2string = oauth2string
		self.server = server
		self.port = port
		self.ssl = ssl # bool
		self.folders = folders
		self._conn = None


	def get_connection(self, use_existing):
		# try to reuse existing connection
		if use_existing and self.has_connection():
			return self._conn
		
		self._conn = conn = None
		
		try:
			if self.ssl:
				if self.port == '':
					conn = imaplib.IMAP4_SSL(self.server)
				else:
					conn = imaplib.IMAP4_SSL(self.server, int(self.port))
			else:
				if self.port == '':
					conn = imaplib.IMAP4(self.server)
				else:
					conn = imaplib.IMAP4(self.server, int(self.port))
				
				if 'STARTTLS' in conn.capabilities:
					conn.starttls()
				else:
					logging.warning("Using unencrypted connection for account '%s'" % self.name)
				
			if self.oauth2string != '':
				conn.authenticate('XOAUTH2', lambda x: self.oauth2string)
			else:
				conn.login(self.user, self.password)
			
			self._conn = conn
		except:
			try:
				if conn != None:
					# conn.close() # allowed in SELECTED state only
					conn.logout()
			except:	pass
			raise # re-throw exception
		
		return self._conn


	def close(self):
		self._conn.close()
		self._conn.logout()


	def has_connection(self):
		return (self._conn != None) and \
				(self._conn.state != imaplib.LOGOUT) and \
				(not self._conn.Terminate)


	def request_folders(self):
		lst = []
		
		# Always create a new connection as an existing one may
		# be used for IMAP IDLE.
		conn = self.get_connection(use_existing = False)

		try:
			status, data = conn.list('', '*')
		finally:
			# conn.close() # allowed in SELECTED state only
			conn.logout()
		
		for d in data:
			match = re.match('.+\s+("."|"?NIL"?)\s+"?([^"]+)"?$', d)

			if match == None:
				logging.warning("Folder format not supported.")
			else:
				folder = match.group(2)
				lst.append(folder)
		
		return lst


#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# account.py
#
# Copyright 2011, 2012 Patrick Ulbrich <zulu99@gmx.net>
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

import poplib
import daemon.imaplib2 as imaplib
from common.i18n import _

account_defaults = {
	'enabled'			: '0',
	'name'				: '',	
	'user'				: '',
	'server'			: '',
	'port'				: '',
	'ssl'				: '1',
	'imap'				: '0',	
	'idle'				: '0',
	'folder'			: ''
}

class Account:
	def __init__(self, enabled = False, name = _('Unnamed'), user = '', \
		password = '', server = '', port = '', ssl = True, imap = False, idle = False, folder = '' ):
		
		self.enabled = enabled # bool
		self.name = name
		self.user = user
		self.password = password
		self.server = server
		self.port = port
		self.ssl = ssl # bool
		self.imap = imap # bool		
		self.idle = idle # bool
		self.folder = folder
		self._conn = None


	def get_connection(self, use_existing = False): # get email server connection
		if self.imap:
			try:
				conn = self._get_IMAP_connection(use_existing)
			except:
				print "Error: Cannot connect to IMAP account: %s. " % self.server
				conn = None
		else:
			try:
				conn = self._get_POP3_connection(use_existing)
			except:
				print "Error: Cannot connect to POP account: %s. " % self.server
				conn = None

		return conn
	
	
	def get_id(self):
		# TODO : this id is not really unique...
		return str(hash(self.user + self.server))
	
	
	def _get_IMAP_connection(self, use_existing):
		# try to reuse existing connection
		if use_existing and (self._conn != None) and \
		(self._conn.state != imaplib.LOGOUT) and (not self._conn.Terminate):
			return self._conn
		
		if self.ssl:
			if self.port == '':
				self._conn = imaplib.IMAP4_SSL(self.server)
			else:
				self._conn = imaplib.IMAP4_SSL(self.server, self.port)
		else:
			if self.port == '':
				self._conn = imaplib.IMAP4(self.server)
			else:
				self._conn = imaplib.IMAP4(self.server, self.port)
		
		self._conn.login(self.user, self.password)
		
		return self._conn
	
	
	def _get_POP3_connection(self, use_existing):
		# try to reuse existing connection
		if use_existing and (self._conn != None) and ('sock' in self._conn.__dict__):
			return self._conn
		
		if self.ssl:
			if self.port == '':
				self._conn = poplib.POP3_SSL(self.server)
			else:
				self._conn = poplib.POP3_SSL(self.server, self.port)
		else:
			if self.port == '':
				self._conn = poplib.POP3(self.server)
			else:
				self._conn = poplib.POP3(self.server, self.port)
		
		self._conn.getwelcome()
		self._conn.user(self.user)
		self._conn.pass_(self.password)
		
		return self._conn


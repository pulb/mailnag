#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# account.py
#
# Copyright 2011 Patrick Ulbrich <zulu99@gmx.net>
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

PACKAGE_NAME = "mailnag"

import gettext
import time
import poplib
import daemon.imaplib2 as imaplib

gettext.bindtextdomain(PACKAGE_NAME, './locale')
gettext.textdomain(PACKAGE_NAME)
_ = gettext.gettext

account_defaults = {
	'enabled'			: '0',
	'name'				: '',	
	'user'				: '',
	'server'			: '',
	'port'				: '',
	'ssl'				: '0',
	'imap'				: '0',	
	'idle'				: '0',
	'folder'			: ''
}

class Account:
	def __init__(self, enabled = False, name = _('Unnamed'), user = '', \
		password = '', server = '', port = '', ssl = False, imap = False, idle = False, folder = '' ):
	
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


	def get_connection(self):											# get email server connection
		if self.imap:													# IMAP
			try:
				srv = self._get_IMAP_connection()
			except:
				print "Warning: Cannot connect to IMAP account: %s. " \
					"Next try in 30 seconds." % self.server
				time.sleep(30)											# wait 30 seconds
				try:
					srv = self._get_IMAP_connection()
				except:
					print "Error: Cannot connect to IMAP account: %s. " % self.server
					srv = None
		else:															# POP
			try:
				srv = self._get_POP3_connection()
			except:
				print "Warning: Cannot connect to POP account: %s. " \
					"Next try in 30 seconds." % self.server
				time.sleep(30)											# wait 30 seconds
				try:
					srv = self._get_POP3_connection()
				except:
					print "Error: Cannot connect to POP account: %s. " % self.server
					srv = None

		return srv														# server object


	def _get_IMAP_connection(self):
		if self.ssl:
			if self.port == '':
				srv = imaplib.IMAP4_SSL(self.server)
			else:
				srv = imaplib.IMAP4_SSL(self.server, self.port)
		else:
			if self.port == '':
				srv = imaplib.IMAP4(self.server)
			else:
				srv = imaplib.IMAP4(self.server, self.port)
		
		srv.login(self.user, self.password)
		return srv
	
	
	def _get_POP3_connection(self):
		if self.ssl:
			if self.port == '':
				srv = poplib.POP3_SSL(self.server)
			else:
				srv = poplib.POP3_SSL(self.server, self.port)
		else:
			if self.port == '':
				srv = poplib.POP3(self.server)
			else:
				srv = poplib.POP3(self.server, self.port)
		
		srv.getwelcome()
		srv.user(self.user)
		srv.pass_(self.password)
		return srv


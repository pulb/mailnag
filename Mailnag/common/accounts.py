#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# accounts.py
#
# Copyright 2011 - 2013 Patrick Ulbrich <zulu99@gmx.net>
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
from common.keyring import Keyring

account_defaults = {
	'enabled'			: '0',
	'name'				: '',	
	'user'				: '',
	'server'			: '',
	'port'				: '',
	'ssl'				: '1',
	'imap'				: '1',	
	'idle'				: '1',
	'folder'			: ''
}

#
# Account class
#
class Account:
	def __init__(self, enabled = False, name = _('Unnamed'), user = '', \
		password = '', server = '', port = '', ssl = True, imap = True, idle = True, folder = '' ):
		
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
			return self._get_IMAP_connection(use_existing)
		else:
			return self._get_POP3_connection(use_existing)
	
	
	def get_id(self):
		# TODO : this id is not really unique...
		return str(hash(self.user + self.server + self.folder))
	
	
	def _get_IMAP_connection(self, use_existing):
		# try to reuse existing connection
		if use_existing and (self._conn != None) and \
		(self._conn.state != imaplib.LOGOUT) and (not self._conn.Terminate):
			return self._conn
		
		self._conn = conn = None
		
		try:
			if self.ssl:
				if self.port == '':
					conn = imaplib.IMAP4_SSL(self.server)
				else:
					conn = imaplib.IMAP4_SSL(self.server, self.port)
			else:
				if self.port == '':
					conn = imaplib.IMAP4(self.server)
				else:
					conn = imaplib.IMAP4(self.server, self.port)
			
			conn.login(self.user, self.password)
			
			self._conn = conn
		except:
			print "Error: Cannot connect to IMAP account: %s. " % self.server
			try:
				if conn != None:
					# conn.close() # allowed in SELECTED state only
					conn.logout()
			except:
				pass		
		
		return self._conn
	
	
	def _get_POP3_connection(self, use_existing):
		# try to reuse existing connection
		if use_existing and (self._conn != None) and ('sock' in self._conn.__dict__):
			return self._conn
		
		self._conn = conn = None
		
		try:
			if self.ssl:
				if self.port == '':
					conn = poplib.POP3_SSL(self.server)
				else:
					conn = poplib.POP3_SSL(self.server, self.port)
			else:
				if self.port == '':
					conn = poplib.POP3(self.server)
				else:
					conn = poplib.POP3(self.server, self.port)
		
			conn.getwelcome()
			conn.user(self.user)
			conn.pass_(self.password)
			
			self._conn = conn
		except:
			print "Error: Cannot connect to POP account: %s. " % self.server
			try:
				if conn != None:
					conn.quit()
			except:
				pass	
		
		return self._conn


#
# AccountList class
#
class AccountList(list):
	def __init__(self):
		self._keyring = Keyring()

	
	def load_from_cfg(self, cfg, enabled_only=False):
		del self[:]
		
		i = 1
		section_name = "Account" + str(i)
		
		while cfg.has_section(section_name):
			enabled		= bool(int(	self._get_account_cfg(cfg, section_name, 'enabled')	))
			
			if (not enabled_only) or (enabled_only and enabled):
				name	=			self._get_account_cfg(cfg, section_name, 'name')
				user	=			self._get_account_cfg(cfg, section_name, 'user')
				server	=			self._get_account_cfg(cfg, section_name, 'server')
				port	=			self._get_account_cfg(cfg, section_name, 'port')
				ssl		= bool(int(	self._get_account_cfg(cfg, section_name, 'ssl')		))
				imap	= bool(int(	self._get_account_cfg(cfg, section_name, 'imap')	))
				idle	= bool(int(	self._get_account_cfg(cfg, section_name, 'idle')	))
				folder	= 			self._get_account_cfg(cfg, section_name, 'folder')
			
				protocol = 'imap' if imap else 'pop'
				password = self._keyring.get(protocol, user, server)
			
				acc = Account(enabled, name, user, password, server, port, ssl, imap, idle, folder)
				self.append(acc)

			i = i + 1
			section_name = "Account" + str(i)
			

	def save_to_cfg(self, cfg):		
		# remove existing accounts from cfg
		i = 1
		section_name = "Account" + str(i)
		while cfg.has_section(section_name):
			cfg.remove_section(section_name)
			i = i + 1
			section_name = "Account" + str(i)
		
		# add accounts
		i = 1
		for acc in self:
			section_name = "Account" + str(i)
			
			cfg.add_section(section_name)
			
			cfg.set(section_name, 'enabled', int(acc.enabled))
			cfg.set(section_name, 'name', acc.name)
			cfg.set(section_name, 'user', acc.user)
			cfg.set(section_name, 'server', acc.server)
			cfg.set(section_name, 'port', acc.port)
			cfg.set(section_name, 'ssl', int(acc.ssl))
			cfg.set(section_name, 'imap', int(acc.imap))
			cfg.set(section_name, 'idle', int(acc.idle))
			cfg.set(section_name, 'folder', acc.folder)
			
			protocol = 'imap' if acc.imap else 'pop'
			self._keyring.set(protocol, acc.user, acc.server, acc.password)

			i = i + 1
		
		# delete obsolete entries from Keyring
		self._keyring.remove(self)
	
		
	def _get_account_cfg(self, cfg, section_name, option_name):
		if cfg.has_option(section_name, option_name):
			return cfg.get(section_name, option_name)
		else:
			return account_defaults[option_name]


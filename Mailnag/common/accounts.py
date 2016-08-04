#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# accounts.py
#
# Copyright 2011 - 2016 Patrick Ulbrich <zulu99@gmx.net>
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

import re
import poplib
import logging
import Mailnag.common.imaplib2 as imaplib
from Mailnag.common.utils import splitstr

account_defaults = {
	'enabled'			: '0',
	'name'				: '',	
	'user'				: '',
	'password'			: '',
	'server'			: '',
	'port'				: '',
	'ssl'				: '1',
	'imap'				: '1',	
	'idle'				: '1',
	'folder'			: ''
}

CREDENTIAL_KEY = 'Mailnag password for %s://%s@%s'

#
# Account class
#
class Account:
	def __init__(self, enabled = False, name = '', user = '', \
		password = '', oauth2string = '', server = '', port = '', ssl = True, imap = True, idle = True, folders = []):
		
		self.enabled = enabled # bool
		self.name = name
		self.user = user
		self.password = password
		self.oauth2string = oauth2string
		self.server = server
		self.port = port
		self.ssl = ssl # bool
		self.imap = imap # bool		
		self.idle = idle # bool
		self.folders = folders
		self._conn = None


	def get_connection(self, use_existing = False): # get email server connection
		if self.imap:
			return self._get_IMAP_connection(use_existing)
		else:
			return self._get_POP3_connection(use_existing)
	
	
	# Indicates whether the account 
	# holds an active existing connection.
	# Note: this method only indicates if the 
	# account *holds* (caches) an existing connection. 
	# There may be further, but no longer
	# associated connections if get_connection() 
	# was called multiple times (with use_existing 
	# set to False).
	def has_connection(self):
		if self.imap:
			return self._has_IMAP_connection()
		else:
			return self._has_POP3_connection()
	
	
	# Requests folder names (list) from a server.
	# Relevant for IMAP accounts only.
	# Returns an empty list when used on POP3 accounts.
	def request_server_folders(self):
		lst = []
		
		if not self.imap:
			return lst
		
		# Always create a new connection as an existing one may 
		# be used for IMAP IDLE.
		conn = self._get_IMAP_connection(use_existing = False)

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
		
		
	def get_id(self):
		# TODO : this id is not really unique...
		return str(hash(self.user + self.server + ', '.join(self.folders)))
	

	def _has_IMAP_connection(self):
		return (self._conn != None) and \
				(self._conn.state != imaplib.LOGOUT) and \
				(not self._conn.Terminate)
	
	
	def _get_IMAP_connection(self, use_existing):
		# try to reuse existing connection
		if use_existing and self._has_IMAP_connection():
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
	
	
	def _has_POP3_connection(self):
		return (self._conn != None) and \
				('sock' in self._conn.__dict__)
	
	
	def _get_POP3_connection(self, use_existing):
		# try to reuse existing connection
		if use_existing and self._has_POP3_connection():
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
				# (analogous to get_IMAP_connection).
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


#
# AccountManager class
#
class AccountManager:
	def __init__(self, credentialstore = None):
		self._accounts = []
		self._removed = []
		self._credentialstore = credentialstore

	
	def __len__(self):
		return len(self._accounts)
	
	
	def __iter__(self):
		for acc in self._accounts:
			yield acc

		
	def __contains__(self, item):
		return (item in self._accounts)
	
	
	def add(self, account):
		self._accounts.append(account)
	
	
	def remove(self, account):
		self._accounts.remove(account)
		self._removed.append(account)
	
	
	def clear(self):
		for acc in self._accounts:
			self._removed.append(acc)
		del self._accounts[:]
	
	
	def to_list(self):
		# Don't pass a ref to the internal accounts list.
		# (Accounts must be removed via the remove() method only.)
		return self._accounts[:]
	
	
	def load_from_cfg(self, cfg, enabled_only = False):
		del self._accounts[:]
		del self._removed[:]
		
		i = 1
		section_name = "account" + str(i)
		
		while cfg.has_section(section_name):
			enabled		= bool(int(	self._get_account_cfg(cfg, section_name, 'enabled')	))
			
			if (not enabled_only) or (enabled_only and enabled):
				name		=			self._get_account_cfg(cfg, section_name, 'name')
				user		=			self._get_account_cfg(cfg, section_name, 'user')
				password	=			self._get_account_cfg(cfg, section_name, 'password')
				server		=			self._get_account_cfg(cfg, section_name, 'server')
				port		=			self._get_account_cfg(cfg, section_name, 'port')
				ssl			= bool(int(	self._get_account_cfg(cfg, section_name, 'ssl')		))
				imap		= bool(int(	self._get_account_cfg(cfg, section_name, 'imap')	))
				idle		= bool(int(	self._get_account_cfg(cfg, section_name, 'idle')	))
				folders		= splitstr(self._get_account_cfg(cfg, section_name, 'folder'), ',')

				if self._credentialstore != None:
					protocol = 'imap' if imap else 'pop'
					password = self._credentialstore.get(CREDENTIAL_KEY % (protocol, user, server))
				
				acc = Account(enabled, name, user, password, '', server, port, ssl, imap, idle, folders)
				self._accounts.append(acc)

			i = i + 1
			section_name = "account" + str(i)
			

	def save_to_cfg(self, cfg):		
		# Remove all accounts from cfg
		i = 1
		section_name = "account" + str(i)
		while cfg.has_section(section_name):
			cfg.remove_section(section_name)
			i = i + 1
			section_name = "account" + str(i)
		
		# Delete secrets of removed accounts from the credential store
		# (it's important to do this before adding accounts, 
		# in case multiple accounts with the same credential key exist).
		if self._credentialstore != None:
			for acc in self._removed:
				protocol = 'imap' if acc.imap else 'pop'
				# Note: CredentialStore implementations must check if the key acutally exists!
				self._credentialstore.remove(CREDENTIAL_KEY % (protocol, acc.user, acc.server))
			
		del self._removed[:]
		
		# Add accounts
		i = 1
		for acc in self._accounts:
			if acc.oauth2string != '':
				logging.warning("Saving of OAuth2 based accounts is not supported. Account '%s' skipped." % acc.name)
				continue
				
			section_name = "account" + str(i)
			
			cfg.add_section(section_name)
			
			cfg.set(section_name, 'enabled', int(acc.enabled))
			cfg.set(section_name, 'name', acc.name)
			cfg.set(section_name, 'user', acc.user)
			cfg.set(section_name, 'password', '')
			cfg.set(section_name, 'server', acc.server)
			cfg.set(section_name, 'port', acc.port)
			cfg.set(section_name, 'ssl', int(acc.ssl))
			cfg.set(section_name, 'imap', int(acc.imap))
			cfg.set(section_name, 'idle', int(acc.idle))
			cfg.set(section_name, 'folder', ', '.join(acc.folders))
			
			if self._credentialstore != None:
				protocol = 'imap' if acc.imap else 'pop'
				self._credentialstore.set(CREDENTIAL_KEY % (protocol, acc.user, acc.server), acc.password)
			else:
				cfg.set(section_name, 'password', acc.password)

			i = i + 1
	
		
	def _get_account_cfg(self, cfg, section_name, option_name):
		if cfg.has_option(section_name, option_name):
			return cfg.get(section_name, option_name)
		else:
			return account_defaults[option_name]


#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# accounts.py
#
# Copyright 2011 - 2016 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2016 Thomas Haider <t.haider@deprecate.de>
# Copyright 2016 Timo Kankare <timo.kankare@iki.fi>
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
import logging
import json
from Mailnag.backends.imap import IMAPMailboxBackend
from Mailnag.backends.pop3 import POP3MailboxBackend
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
	'folder'			: '[]'
}

CREDENTIAL_KEY = 'Mailnag password for %s://%s@%s'

#
# Account class
#
class Account:
	def __init__(self, enabled = False, name = '', user = '', \
		password = '', oauth2string = '', server = '', port = '', ssl = True, imap = True, idle = True, folders = [], backend = None):
		
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
		self.backend = backend


	def open(self, reopen = True):
		"""Open mailbox for the account."""
		self.backend.open(reopen = reopen)


	def close(self):
		"""Close mailbox for this account."""
		self.backend.close()


	# Indicates whether the account 
	# holds an active existing connection.
	# Note: this method only indicates if the 
	# account *holds* (caches) an existing connection. 
	# There may be further, but no longer
	# associated connections if get_connection() 
	# was called multiple times (with use_existing 
	# set to False).
	def is_open(self):
		"""Returns true if the mailbox is opened."""
		return self.backend.is_open()


	def list_messages(self):
		"""Lists unseen messages from the mailbox for this account.
		Yields a set of tuples (folder, message).
		"""
		return self.backend.list_messages()


	def notify_next_change(self, callback=None, timeout=None):
		"""Asks mailbox to notify next change.
		Callback is called when new mail arrives or removed.
		This may raise an exception if mailbox does not support
		notifications.
		"""
		self.backend.notify_next_change(callback, timeout)


	def cancel_notifications(self):
		"""Cancels notifications.
		This may raise an exception if mailbox does not support
		notifications.
		"""
		self.backend.cancel_notifications()


	def request_server_folders(self):
		"""Requests folder names (list) from a server.
		Returns an empty list if mailbox does not support folders.
		"""
		return self.backend.request_folders()
		
		
	def get_id(self):
		# TODO : this id is not really unique...
		return str(hash(self.user + self.server + ', '.join(self.folders)))
	

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
				folders_str	= self._get_account_cfg(cfg, section_name, 'folder')
				if re.match(r'^\[.*\]$', folders_str):
					folders	= json.loads(folders_str)
				else:
					folders	= splitstr(folders_str, ',')

				if self._credentialstore != None:
					protocol = 'imap' if imap else 'pop'
					password = self._credentialstore.get(CREDENTIAL_KEY % (protocol, user, server))
				
				if imap:
					backend = IMAPMailboxBackend(name, user, password, '', server, port, ssl, folders)
				else:
					backend = POP3MailboxBackend(name, user, password, '', server, port, ssl)
				
				acc = Account(enabled, name, user, password, '', server, port, ssl, imap, idle, folders, backend)
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
			cfg.set(section_name, 'folder', json.dumps(acc.folders))
			
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


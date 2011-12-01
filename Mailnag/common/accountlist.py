#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# accountlist.py
#
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

from common.account import Account, account_defaults
from common.keyring import Keyring

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
	
	
	def import_from_keyring(self):
		# append imported accounts to existing accounts
		self.extend(self._keyring.import_accounts())
	
	
	def _get_account_cfg(self, cfg, section_name, option_name):
		if cfg.has_option(section_name, option_name):
			return cfg.get(section_name, option_name)
		else:
			return account_defaults[option_name]


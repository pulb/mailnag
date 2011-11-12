#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# accounts.py
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

from common.keyring import Keyring
from daemon.account import Account

class Accounts:
	def __init__(self, cfg):
		self.account = []
		keyring = Keyring()
		self.keyring_was_locked = keyring.was_locked

		separator = '|'
		on_list = cfg.get('account', 'on').split(separator)
		name_list = cfg.get('account', 'name').split(separator)
		server_list = cfg.get('account', 'server').split(separator)
		user_list = cfg.get('account', 'user').split(separator)
		imap_list = cfg.get('account', 'imap').split(separator)
		folder_list = cfg.get('account', 'folder').split(separator)
		port_list = cfg.get('account', 'port').split(separator)
		check_interval = cfg.get('general', 'check_interval')
		
		# check if the account list is empty
		if len(name_list) == 1 and name_list[0] == '':
			return
		
		for i in range(len(name_list)):									# iterate 0 to nr of elements in name_list
			on = int(on_list[i])
			name = name_list[i]
			if not on or name == '': continue							# ignore accounts that are off or have no name
			server = server_list[i]
			user = user_list[i]
			imap = int(imap_list[i])
			folder = folder_list[i]
			port = port_list[i]
			if imap: protocol = 'imap'
			else: protocol = 'pop'
			password = keyring.get(protocol, user, server)
			self.account.append(Account(check_interval, name, server, user, password, imap, folder, port))


	def get_count(self, name):											# get number of emails for this provider
		count = 'error'
		for acc in self.account:
			if acc.name == name:
				count = str(acc.mail_count)
				break
		if count == 'error':
			print 'Cannot find account (get_count)'
		return count

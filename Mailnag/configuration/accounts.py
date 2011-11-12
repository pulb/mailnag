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

PACKAGE_NAME = "mailnag"

import gettext
from configuration.account import Account

gettext.bindtextdomain(PACKAGE_NAME, './locale')
gettext.textdomain(PACKAGE_NAME)
_ = gettext.gettext


class Accounts:
	def __init__(self, cfg, keyring):
		self.account = []
		self.current = None												# currently selected account_id
		self.cfg = cfg
		self.keyring = keyring

	def add(self, on = 0, name = _('Unnamed'), server = '', user= '' , \
		password = '', imap = 0, folder = '', port = ''):				# add one new account
		self.account.append(Account(on, name, server, user, \
			password, imap, folder, port))
		this_account = self.account[-1]									# get last element of the list
		id = this_account.id
		return id


	def remove(self, id):												# delete account by id
		for acc in self.account[:]:										# iterate copy of account list
			if acc.id == id:											# find matching account
				self.account.remove(acc)								# delete it
				break													# stop iteration


	def load(self):
		self.account = []												# empty account list

		on = self.cfg.get('account', 'on')
		name = self.cfg.get('account', 'name')
		server = self.cfg.get('account', 'server')
		user = self.cfg.get('account', 'user')
		imap = self.cfg.get('account', 'imap')
		folder = self.cfg.get('account', 'folder')
		port = self.cfg.get('account', 'port')

		separator = '|'
		on_list = on.split(separator)
		name_list = name.split(separator)
		server_list = server.split(separator)
		user_list = user.split(separator)
		imap_list = imap.split(separator)
		folder_list = folder.split(separator)
		port_list = port.split(separator)
		
		for i in range(len(name_list)):									# iterate 0 to nr of elements in name_list
			name = name_list[i]
			if name == '': continue			
			on = int(on_list[i])			
			server = server_list[i]
			user = user_list[i]
			imap = int(imap_list[i])
			folder = folder_list[i]
			port = port_list[i]
			if imap: protocol = 'imap'
			else: protocol = 'pop'
			password = self.keyring.get(protocol, user, server)
			self.add(on, name, server, user, password, imap, folder, port)	# fill Account list


	def get(self, id):													# return all data of one account
		self.current = id
		for acc in self.account:
			if acc.id == id:
				return acc
		return None


	def get_current(self):												# return current account
		if self.current != None:
			for acc in self.account:
				if acc.id == self.current:
					return acc
		return None


	def get_cfg(self):													# return arrays of account strings for cfg
		separator = '|'

		on_list = []
		name_list = []
		server_list = []
		user_list = []
		password_list = []
		imap_list = []
		folder_list = []
		port_list = []

		for acc in self.account:										# collect all values
			on_list.append(str(int(acc.on)))
			name_list.append(acc.name)
			server_list.append(acc.server)
			user_list.append(acc.user)
			password_list.append(acc.password)
			imap_list.append(str(int(acc.imap)))
			folder_list.append(acc.folder)
			port_list.append(acc.port)

		cfg_on = separator.join(on_list)								# concatenate values
		cfg_name = separator.join(name_list)
		cfg_server = separator.join(server_list)
		cfg_user = separator.join(user_list)
		cfg_imap = separator.join(imap_list)
		cfg_folder = separator.join(folder_list)
		cfg_port = separator.join(port_list)

		return cfg_on, cfg_name, cfg_server, cfg_user, password_list, cfg_imap, cfg_folder, cfg_port



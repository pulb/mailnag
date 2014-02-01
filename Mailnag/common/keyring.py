#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# keyring.py
#
# Copyright 2011 - 2014 Patrick Ulbrich <zulu99@gmx.net>
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

from gi.repository import GnomeKeyring
from common.i18n import _


class KeyringUnlockException(Exception):
	def __init__(self, message):
		Exception.__init__(self, message)


class Keyring:
	def __init__(self):
		self.KEYRING_ITEM_NAME = 'Mailnag password for %s://%s@%s'
		
		(result, kr_name) = GnomeKeyring.get_default_keyring_sync()
		self._defaultKeyring = kr_name
		
		if self._defaultKeyring == None:
			self._defaultKeyring = 'login'

		result = GnomeKeyring.unlock_sync(self._defaultKeyring, None)
		
		if result != GnomeKeyring.Result.OK:
			raise KeyringUnlockException('Failed to unlock default keyring')


	# get password for account from Gnome Keyring
	def get(self, protocol, user, server):
		(result, ids) = GnomeKeyring.list_item_ids_sync(self._defaultKeyring)		
		if result == GnomeKeyring.Result.OK:
			displayNameDict = {}
			for identity in ids:
				(result, item) = GnomeKeyring.item_get_info_sync(self._defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity

			if self.KEYRING_ITEM_NAME % (protocol, user, server) in displayNameDict:
				(result, item) = GnomeKeyring.item_get_info_sync(self._defaultKeyring, \
					displayNameDict[self.KEYRING_ITEM_NAME % \
					(protocol, user, server)])

				if item.get_secret() != '':
					return item.get_secret()
				else:
					# logging.debug("Keyring.get(): No Keyring Password for %s://%s@%s." % (protocol, user, server))
					return ''

			else:
				# logging.debug("Keyring.get(): %s://%s@%s not in Keyring." % (protocol, user, server))
				return ''

		else:
			# logging.debug("Keyring.get(): Neither default- nor 'login'-Keyring available.")
			return ''


	# store password in Gnome-Keyring
	def set(self, protocol, user, server, password):
		if password != '':
			displayNameDict = {}
			(result, ids) = GnomeKeyring.list_item_ids_sync(self._defaultKeyring)
			for identity in ids:
				(result, item) = GnomeKeyring.item_get_info_sync(self._defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity

			attrs = GnomeKeyring.Attribute.list_new()
			GnomeKeyring.Attribute.list_append_string(attrs, 'application',	'Mailnag')
			GnomeKeyring.Attribute.list_append_string(attrs, 'protocol',	protocol)
			GnomeKeyring.Attribute.list_append_string(attrs, 'user',		user)
			GnomeKeyring.Attribute.list_append_string(attrs, 'server',		server)
			
			if self.KEYRING_ITEM_NAME % (protocol, user, server) in displayNameDict:
				(result, item) = GnomeKeyring.item_get_info_sync(self._defaultKeyring, \
					displayNameDict[self.KEYRING_ITEM_NAME % \
					(protocol, user, server)])
				
				if password != item.get_secret():
					GnomeKeyring.item_create_sync(self._defaultKeyring, \
						GnomeKeyring.ItemType.GENERIC_SECRET, \
						self.KEYRING_ITEM_NAME % (protocol, user, server), \
						attrs, password, True)
			else:
				GnomeKeyring.item_create_sync(self._defaultKeyring, \
					GnomeKeyring.ItemType.GENERIC_SECRET, \
					self.KEYRING_ITEM_NAME % (protocol, user, server), \
					attrs, password, True)


	# delete obsolete entries from Keyring
	def remove(self, accounts):
		# create list of all valid accounts
		valid_accounts = []
		for acc in accounts:
			protocol = 'imap' if acc.imap else 'pop'
			valid_accounts.append(self.KEYRING_ITEM_NAME % \
			(protocol, acc.user, acc.server))

		# find and delete invalid entries
		(result, ids) = GnomeKeyring.list_item_ids_sync(self._defaultKeyring)
		if result == GnomeKeyring.Result.OK:
			displayNameDict = {}
			for identity in ids:
				(result, item) = GnomeKeyring.item_get_info_sync(self._defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity
			for key in displayNameDict.keys():
				if key.startswith('Mailnag password for') \
				and key not in valid_accounts:
					GnomeKeyring.item_delete_sync(self._defaultKeyring, displayNameDict[key])

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# keyring.py
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

from gi.repository import GObject, GLib, GdkPixbuf, Gtk, GnomeKeyring

from common.i18n import _
from common.account import Account

class Keyring:
	def __init__(self):
		(result, kr_name) = GnomeKeyring.get_default_keyring_sync()
		self._defaultKeyring = kr_name
		
		if self._defaultKeyring == None:
			self._defaultKeyring = 'login'

		result = GnomeKeyring.unlock_sync(self._defaultKeyring, None)
		
		if (result != GnomeKeyring.Result.OK):
			raise Exception('Failed to unlock default keyring')


	def get(self, protocol, user, server):								# get password for account from Gnome Keyring
		(result, ids) = GnomeKeyring.list_item_ids_sync(self._defaultKeyring)		
		if result == GnomeKeyring.Result.OK:
			displayNameDict = {}
			for identity in ids:
				(result, item) = GnomeKeyring.item_get_info_sync(self._defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity

			if 'Mailnag password for %s://%s@%s' % (protocol, user, server) in displayNameDict:
				(result, item) = GnomeKeyring.item_get_info_sync(self._defaultKeyring, \
					displayNameDict['Mailnag password for %s://%s@%s' % \
					(protocol, user, server)])

				if item.get_secret() != '':
					return item.get_secret()
				else:
					# DEBUG print "Keyring.get(): No Keyring Password for %s://%s@%s." % (protocol, user, server)
					return ''

			else:
				# DEBUG print "Keyring.get(): %s://%s@%s not in Keyring." % (protocol, user, server)
				return ''

		else:
			# DEBUG print "Keyring.get(): Either default- nor 'login'-Keyring available."
			return ''


	def set(self, protocol, user, server, password): # store password in Gnome-Keyring
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
			
			if 'Mailnag password for %s://%s@%s' % (protocol, user, server) in displayNameDict:
				(result, item) = GnomeKeyring.item_get_info_sync(self._defaultKeyring, \
					displayNameDict['Mailnag password for %s://%s@%s' % \
					(protocol, user, server)])
				
				if password != item.get_secret():
					GnomeKeyring.item_create_sync(self._defaultKeyring, \
						GnomeKeyring.ItemType.GENERIC_SECRET, \
						'Mailnag password for %s://%s@%s' % (protocol, user, server), \
						attrs, password, True)
			else:
				GnomeKeyring.item_create_sync(self._defaultKeyring, \
					GnomeKeyring.ItemType.GENERIC_SECRET, \
					'Mailnag password for %s://%s@%s' % (protocol, user, server), \
					attrs, password, True)


	def remove(self, accounts):											# delete obsolete entries from Keyring
		valid_accounts = []
		for acc in accounts:											# create list of all valid accounts
			protocol = 'imap' if acc.imap else 'pop'
			valid_accounts.append('Mailnag password for %s://%s@%s' % \
			(protocol, acc.user, acc.server))

		(result, ids) = GnomeKeyring.list_item_ids_sync(self._defaultKeyring)
		if result == GnomeKeyring.Result.OK:				# find and delete invalid entries
			displayNameDict = {}
			for identity in ids:
				(result, item) = GnomeKeyring.item_get_info_sync(self._defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity
			for key in displayNameDict.keys():
				if key.startswith('Mailnag password for') \
				and key not in valid_accounts:
					GnomeKeyring.item_delete_sync(self._defaultKeyring, displayNameDict[key])

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

from gi.repository import GObject, GLib, GdkPixbuf, Gtk
import gnomekeyring

from common.dist_cfg import PACKAGE_NAME
from common.i18n import _
from common.utils import get_data_file
from common.account import Account

class Keyring:
	def __init__(self):
		GLib.set_application_name('mailnag')
		self._was_locked = False										# True if Dialog shown. Required for Sortorder problem
		self._keyring_password = ''
		self._defaultKeyring = gnomekeyring.get_default_keyring_sync()
		if self._defaultKeyring == None:
			self._defaultKeyring = 'login'

		while gnomekeyring.get_info_sync(self._defaultKeyring).get_is_locked():		# Keyring locked?
			self._message_response = 'cancel'							# default response for message dialog
			try:
				try: gnomekeyring.unlock_sync(self._defaultKeyring, \
						self._keyring_password)
				except gnomekeyring.IOError:
					self._show_keyring_dialog()							# get keyring password
					Gtk.main()											# wait until dialog is closed
					result = gnomekeyring.unlock_sync(self._defaultKeyring, \
								self._keyring_password)
			except gnomekeyring.IOError:
				self._show_message(_('Failed to unlock Keyring "{0}".\nWrong password.\n\nDo you want to try again?').format(self._defaultKeyring))
				Gtk.main()												# wait until dialog is closed
				if self._message_response == 'cancel': exit(1)			# close application (else: continue getting password)


	def get(self, protocol, user, server):												# get password for account from Gnome Keyring
		if gnomekeyring.list_item_ids_sync(self._defaultKeyring):
			displayNameDict = {}
			for identity in gnomekeyring.list_item_ids_sync(self._defaultKeyring):
				item = gnomekeyring.item_get_info_sync(self._defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity

			if 'Mailnag password for %s://%s@%s' % (protocol, user, server) in displayNameDict:

				if gnomekeyring.item_get_info_sync(self._defaultKeyring, \
				displayNameDict['Mailnag password for %s://%s@%s' % \
				(protocol, user, server)]).get_secret() != '':
					return gnomekeyring.item_get_info_sync(self._defaultKeyring, \
					displayNameDict['Mailnag password for %s://%s@%s' % \
					(protocol, user, server)]).get_secret()
				else:
					# DEBUG print "Keyring.get(): No Keyring Password for %s://%s@%s." % (protocol, user, server)
					return ''

			else:
				# DEBUG print "Keyring.get(): %s://%s@%s not in Keyring." % (protocol, user, server)
				return ''

		else:
			# DEBUG print "Keyring.get(): Either default- nor 'login'-Keyring available."
			return ''


	def import_accounts(self): # get email accounts from Gnome-Keyring
		accounts = []
		if gnomekeyring.list_item_ids_sync(self._defaultKeyring):
			displayNameDict = {}
			for identity in gnomekeyring.list_item_ids_sync(self._defaultKeyring):
				item = gnomekeyring.item_get_info_sync(self._defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity
			for displayName in displayNameDict:
				if displayName.startswith('pop://') \
				or displayName.startswith('imap://'):
					server = displayName.split('@')[1][:-1]
					if displayName.startswith('imap://'):
						imap = True
						user = displayName.split('@')[0][7:]
					else:
						imap = False
						user = displayName.split('@')[0][6:]
					
					user = user.replace('%40','@')
					
					if ';' in user:
						user = user.split(';')[0]
					
					password = gnomekeyring.item_get_info_sync(self._defaultKeyring, \
						displayNameDict[displayName]).get_secret()
					
					accounts.append(Account(enabled = True, name = "%s (%s)" % (server, user), \
						server = server, user = user, password = password, imap = imap))
		return accounts


	def set(self, protocol, user, server, password): # store password in Gnome-Keyring
		if password != '':
			displayNameDict = {}
			for identity in gnomekeyring.list_item_ids_sync(self._defaultKeyring):
				item = gnomekeyring.item_get_info_sync(self._defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity

			if 'Mailnag password for %s://%s@%s' % (protocol, user, server) in displayNameDict:

				if password != gnomekeyring.item_get_info_sync(self._defaultKeyring, \
				displayNameDict['Mailnag password for %s://%s@%s' % \
				(protocol, user, server)]).get_secret():
					gnomekeyring.item_create_sync(self._defaultKeyring, \
						gnomekeyring.ITEM_GENERIC_SECRET, \
						'Mailnag password for %s://%s@%s' % (protocol, user, server), \
						{'application':'Mailnag', 'protocol':protocol, 'user':user, 'server':server}, \
						password, True)
			else:
				gnomekeyring.item_create_sync(self._defaultKeyring, \
					gnomekeyring.ITEM_GENERIC_SECRET, \
					'Mailnag password for %s://%s@%s' % (protocol, user, server), \
					{'application':'Mailnag', 'protocol':protocol, 'user':user, 'server':server}, password, True)


	def remove(self, accounts):											# delete obsolete entries from Keyring
		defaultKeyring = gnomekeyring.get_default_keyring_sync()
		if defaultKeyring == None:
			defaultKeyring = 'login'

		valid_accounts = []
		for acc in accounts:											# create list of all valid accounts
			protocol = 'imap' if acc.imap else 'pop'
			valid_accounts.append('Mailnag password for %s://%s@%s' % \
			(protocol, acc.user, acc.server))

		if gnomekeyring.list_item_ids_sync(defaultKeyring):				# find and delete invalid entries
			displayNameDict = {}
			for identity in gnomekeyring.list_item_ids_sync(defaultKeyring):
				item = gnomekeyring.item_get_info_sync(defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity
			for key in displayNameDict.keys():
				if key.startswith('Mailnag password for') \
				and key not in valid_accounts:
					gnomekeyring.item_delete_sync(defaultKeyring, displayNameDict[key])


	def _show_keyring_dialog(self):										# dialog to get password to unlock keyring
		self._was_locked = True
		builder = Gtk.Builder()
		builder.set_translation_domain(PACKAGE_NAME)
		builder.add_from_file(get_data_file("keyring_dialog.ui"))
		builder.connect_signals({"gtk_main_quit" : self._exit_keyring_dialog, \
			"on_button_cancel_clicked" : self._exit_keyring_dialog, \
			"on_button_ok_clicked" : self._ok_keyring_dialog, \
			"on_entry_password_activate" : self._ok_keyring_dialog})	# hit RETURN in entry field
		self._window = builder.get_object("dialog_keyring")
		self._password = builder.get_object("entry_password")
		self._window.show()


	def _exit_keyring_dialog(self, widget):								# password dialog exit or cancel clicked
		self._window.destroy()
		Gtk.main_quit()													# terminate loop to allow continuation


	def _ok_keyring_dialog(self, widget):								# password dialog ok clicked
		self._keyring_password = self._password.get_text()				# get text from widget
		self._exit_keyring_dialog(widget)


	def _show_message(self, message):									# dialog to show keyring messages
		builder = Gtk.Builder()
		builder.set_translation_domain(PACKAGE_NAME)
		builder.add_from_file(get_data_file("message_dialog.ui"))
		builder.connect_signals({"gtk_main_quit" : self._exit_message, \
			"on_button_cancel_clicked" : self._exit_message, \
			"on_button_ok_clicked" : self._ok_message})
		self._window = builder.get_object("dialog_message")
		self._message = builder.get_object("label_message")
		self._message.set_text(message)									# put message text into label
		self._window.show()


	def _exit_message(self, widget):									# keyring message dialog exit or cancel clicked
		self._window.destroy()
		Gtk.main_quit()													# terminate loop to allow continuation


	def _ok_message(self, widget):										# keyring message dialog ok clicked
		self._message_response = 'ok'
		self._exit_message(widget)


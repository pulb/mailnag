#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# accountdialog.py
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

PACKAGE_NAME = "mailnag"

from gi.repository import GLib, GdkPixbuf, Gtk
import gettext
from common.utils import get_data_file

gettext.bindtextdomain(PACKAGE_NAME, './locale')
gettext.textdomain(PACKAGE_NAME)
_ = gettext.gettext


class AccountDialog:
	def __init__(self, parent):
		builder = Gtk.Builder()
		builder.set_translation_domain(PACKAGE_NAME)
		builder.add_from_file(get_data_file("account_dialog.ui"))
		builder.connect_signals({ \
			"entry_changed" : self.__on_entry_changed, \
			"chk_account_imap_toggled" : self.__on_chk_account_imap_toggled, \
			"btn_cancel_clicked" : self.__on_btn_cancel_clicked, \
			"btn_save_clicked" : self.__on_btn_save_clicked \
		})

		self.window = builder.get_object("account_dialog")
		self.window.set_transient_for(parent)

		self.entry_account_name = builder.get_object("entry_account_name")
		self.entry_account_user = builder.get_object("entry_account_user")
		self.entry_account_password = builder.get_object("entry_account_password")
		self.entry_account_server = builder.get_object("entry_account_server")		
		self.entry_account_port = builder.get_object("entry_account_port")
		self.chk_account_imap = builder.get_object("chk_account_imap")
		self.entry_account_folder = builder.get_object("entry_account_folder")
		self.button_save = builder.get_object("button_save")

		
	def run(self):
		return self.window.run()


	def destroy(self):
		self.window.destroy()

	
	def __on_btn_cancel_clicked(self, widget):
		pass


	def __on_btn_save_clicked(self, widget):
		pass

	
	def __on_entry_changed(self, widget):
		# validate
		ok = len(self.entry_account_name.get_text()) > 0 and \
		     len(self.entry_account_user.get_text()) > 0 and \
		     len(self.entry_account_password.get_text()) > 0 and \
		     len(self.entry_account_server.get_text()) > 0
		
		self.button_save.set_sensitive(ok)
		
		
	def __on_chk_account_imap_toggled(self, widget):
		self.entry_account_folder.set_sensitive(self.chk_account_imap.get_active())



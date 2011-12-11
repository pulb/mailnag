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

from gi.repository import GLib, GdkPixbuf, Gtk
from common.utils import get_data_file
from common.account import Account
from common.i18n import PACKAGE_NAME, _

class AccountDialog:
	def __init__(self, parent, acc):
		self.acc = acc
		
		builder = Gtk.Builder()
		builder.set_translation_domain(PACKAGE_NAME)
		builder.add_from_file(get_data_file("account_dialog.ui"))
		builder.connect_signals({ \
			"account_type_changed" : self.__on_cmb_account_type_changed, \
			"entry_changed" : self.__on_entry_changed, \
			"btn_cancel_clicked" : self.__on_btn_cancel_clicked, \
			"btn_save_clicked" : self.__on_btn_save_clicked \
		})

		self.window = builder.get_object("account_dialog")
		self.window.set_transient_for(parent)

		self.cmb_account_type = builder.get_object("cmb_account_type")
		self.entry_account_name = builder.get_object("entry_account_name")
		self.entry_account_user = builder.get_object("entry_account_user")
		self.entry_account_password = builder.get_object("entry_account_password")
		self.entry_account_server = builder.get_object("entry_account_server")		
		self.entry_account_port = builder.get_object("entry_account_port")
		self.label_account_folder = builder.get_object("label_account_folder")
		self.entry_account_folder = builder.get_object("entry_account_folder")
		self.chk_account_push = builder.get_object("chk_account_push")
		self.chk_account_ssl = builder.get_object("chk_account_ssl")
		self.button_save = builder.get_object("button_save")

		self.entry_account_port.set_placeholder_text(_("optional"))
		self.entry_account_folder.set_placeholder_text(_("optional"))
		
		
	def run(self):
		self.cmb_account_type.set_active(int(self.acc.imap))
		self.entry_account_name.set_text(self.acc.name)
		self.entry_account_user.set_text(self.acc.user)
		self.entry_account_password.set_text(self.acc.password)
		self.entry_account_server.set_text(self.acc.server)
		self.entry_account_port.set_text(self.acc.port)
		self.entry_account_folder.set_text(self.acc.folder)
		self.chk_account_push.set_active(self.acc.idle)
		self.chk_account_ssl.set_active(self.acc.ssl)
			
		res = self.window.run()
		
		if res == 1:
			self.acc.name = self.entry_account_name.get_text()
			self.acc.user = self.entry_account_user.get_text()
			self.acc.password = self.entry_account_password.get_text()
			self.acc.server = self.entry_account_server.get_text()
			self.acc.port = self.entry_account_port.get_text()
			self.acc.ssl = self.chk_account_ssl.get_active()
			
			if self.cmb_account_type.get_active() == 0: # POP3
				self.acc.imap = False
				self.acc.folder = ''
				self.acc.idle = False
			else: # IMAP
				self.acc.imap = True
				self.acc.folder = self.entry_account_folder.get_text()
				self.acc.idle = self.chk_account_push.get_active()
		
		self.window.destroy()
		return res

	
	def get_account(self):
		return self.acc
	
		
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
		
		
	def __on_cmb_account_type_changed(self, widget):
		if self.cmb_account_type.get_active() == 0: # POP3
			self.label_account_folder.set_visible(False)
			self.entry_account_folder.set_visible(False)
			self.chk_account_push.set_visible(False)
		else: # IMAP
			self.label_account_folder.set_visible(True)
			self.entry_account_folder.set_visible(True)
			self.chk_account_push.set_visible(True)



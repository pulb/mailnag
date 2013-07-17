#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# accountdialog.py
#
# Copyright 2011 - 2013 Patrick Ulbrich <zulu99@gmx.net>
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
from common.dist_cfg import PACKAGE_NAME
from common.i18n import _
from common.utils import get_data_file
from common.accounts import Account

class AccountDialog:
	def __init__(self, parent, acc):
		self._acc = acc
		
		builder = Gtk.Builder()
		builder.set_translation_domain(PACKAGE_NAME)
		builder.add_from_file(get_data_file("account_dialog.ui"))
		builder.connect_signals({ \
			"account_type_changed" : self._on_cmb_account_type_changed, \
			"entry_changed" : self._on_entry_changed, \
			"btn_cancel_clicked" : self._on_btn_cancel_clicked, \
			"btn_save_clicked" : self._on_btn_save_clicked \
		})

		self._window = builder.get_object("account_dialog")
		self._window.set_transient_for(parent)

		self._cmb_account_type = builder.get_object("cmb_account_type")
		self._entry_account_name = builder.get_object("entry_account_name")
		self._entry_account_user = builder.get_object("entry_account_user")
		self._entry_account_password = builder.get_object("entry_account_password")
		self._entry_account_server = builder.get_object("entry_account_server")		
		self._entry_account_port = builder.get_object("entry_account_port")
		self._label_account_folder = builder.get_object("label_account_folder")
		self._entry_account_folder = builder.get_object("entry_account_folder")
		self._chk_account_push = builder.get_object("chk_account_push")
		self._chk_account_ssl = builder.get_object("chk_account_ssl")
		self._button_save = builder.get_object("button_save")

		self._entry_account_port.set_placeholder_text(_("optional"))
		self._entry_account_folder.set_placeholder_text(_("optional"))
		
		
	def run(self):
		self._cmb_account_type.set_active(int(self._acc.imap))
		self._entry_account_name.set_text(self._acc.name)
		self._entry_account_user.set_text(self._acc.user)
		self._entry_account_password.set_text(self._acc.password)
		self._entry_account_server.set_text(self._acc.server)
		self._entry_account_port.set_text(self._acc.port)
		self._entry_account_folder.set_text(self._acc.folder)
		self._chk_account_push.set_active(self._acc.idle)
		self._chk_account_ssl.set_active(self._acc.ssl)
			
		res = self._window.run()
		
		if res == 1:
			self._acc.name = self._entry_account_name.get_text()
			self._acc.user = self._entry_account_user.get_text()
			self._acc.password = self._entry_account_password.get_text()
			self._acc.server = self._entry_account_server.get_text()
			self._acc.port = self._entry_account_port.get_text()
			self._acc.ssl = self._chk_account_ssl.get_active()
			
			if self._cmb_account_type.get_active() == 0: # POP3
				self._acc.imap = False
				self._acc.folder = ''
				self._acc.idle = False
			else: # IMAP
				self._acc.imap = True
				self._acc.folder = self._entry_account_folder.get_text()
				self._acc.idle = self._chk_account_push.get_active()
		
		self._window.destroy()
		return res

	
	def get_account(self):
		return self._acc
	
		
	def _on_btn_cancel_clicked(self, widget):
		pass


	def _on_btn_save_clicked(self, widget):
		pass

	
	def _on_entry_changed(self, widget):		
		if widget is self._entry_account_folder:
			# disable IMAP Push checkbox if multiple folders are specifed
			if ("," in self._entry_account_folder.get_text()):
				self._chk_account_push.set_active(False)
				self._chk_account_push.set_sensitive(False)
			else:
				self._chk_account_push.set_sensitive(True)
		else:
			# validate
			ok = len(self._entry_account_name.get_text()) > 0 and \
				 len(self._entry_account_user.get_text()) > 0 and \
				 len(self._entry_account_password.get_text()) > 0 and \
				 len(self._entry_account_server.get_text()) > 0
		
			self._button_save.set_sensitive(ok)
		
		
	def _on_cmb_account_type_changed(self, widget):
		if self._cmb_account_type.get_active() == 0: # POP3
			self._label_account_folder.set_visible(False)
			self._entry_account_folder.set_visible(False)
			self._chk_account_push.set_visible(False)
		else: # IMAP
			self._label_account_folder.set_visible(True)
			self._entry_account_folder.set_visible(True)
			self._chk_account_push.set_visible(True)



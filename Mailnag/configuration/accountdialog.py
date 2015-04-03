#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# accountdialog.py
#
# Copyright 2011 - 2015 Patrick Ulbrich <zulu99@gmx.net>
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

from gi.repository import GLib, Gtk
from Mailnag.common.dist_cfg import PACKAGE_NAME
from Mailnag.common.i18n import _
from Mailnag.common.utils import get_data_file, splitstr

IDX_GMAIL	= 0
IDX_GMX		= 1
IDX_WEB_DE	= 2
IDX_YAHOO	= 3
IDX_IMAP	= 4
IDX_POP3	= 5

PROVIDER_CONFIGS = [
	[ 'Gmail', 'imap.gmail.com', '993'],
	[ 'GMX', 'imap.gmx.net', '993'],
	[ 'Web.de', 'imap.web.de', '993'],
	[ 'Yahoo', 'imap.mail.yahoo.com', '993']
]

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
		self._label_account_name = builder.get_object("label_account_name")
		self._entry_account_name = builder.get_object("entry_account_name")
		self._entry_account_user = builder.get_object("entry_account_user")
		self._entry_account_password = builder.get_object("entry_account_password")
		self._label_account_server = builder.get_object("label_account_server")
		self._entry_account_server = builder.get_object("entry_account_server")		
		self._label_account_port = builder.get_object("label_account_port")
		self._entry_account_port = builder.get_object("entry_account_port")
		self._label_account_folders = builder.get_object("label_account_folders")
		self._entry_account_folders = builder.get_object("entry_account_folders")
		self._chk_account_push = builder.get_object("chk_account_push")
		self._chk_account_ssl = builder.get_object("chk_account_ssl")
		self._button_save = builder.get_object("button_save")

		self._entry_account_port.set_placeholder_text(_("optional"))
		self._entry_account_folders.set_placeholder_text(_("optional"))
		
		
	def run(self):
		self._fill_account_type_cmb()
		
		self._entry_account_name.set_text(self._acc.name)
		self._entry_account_user.set_text(self._acc.user)
		self._entry_account_password.set_text(self._acc.password)
		self._entry_account_server.set_text(self._acc.server)
		self._entry_account_port.set_text(self._acc.port)
		self._entry_account_folders.set_text(', '.join(self._acc.folders))
		self._chk_account_push.set_active(self._acc.idle)
		self._chk_account_ssl.set_active(self._acc.ssl)
			
		res = self._window.run()
		
		if res == 1:
			acctype = self._cmb_account_type.get_active()
			if (acctype == IDX_POP3) or (acctype == IDX_IMAP):
				self._acc.name = self._entry_account_name.get_text()
				self._acc.user = self._entry_account_user.get_text()
				self._acc.password = self._entry_account_password.get_text()
				self._acc.server = self._entry_account_server.get_text()
				self._acc.port = self._entry_account_port.get_text()
				self._acc.ssl = self._chk_account_ssl.get_active()
			
				if acctype == IDX_POP3:
					self._acc.imap = False
					self._acc.folders = []
					self._acc.idle = False
				elif acctype == IDX_IMAP:
					self._acc.imap = True
					self._acc.folders = splitstr(self._entry_account_folders.get_text(), ',')
					self._acc.idle = self._chk_account_push.get_active()
					
			else: # known provider (imap only)
				self._acc.name = self._entry_account_user.get_text()
				self._acc.user = self._entry_account_user.get_text()
				self._acc.password = self._entry_account_password.get_text()
				self._acc.ssl = True
				self._acc.imap = True
				self._acc.folders = splitstr(self._entry_account_folders.get_text(), ',')
				self._acc.idle = not self._has_multiple_folders()
				
				if acctype < len(PROVIDER_CONFIGS):
					p = PROVIDER_CONFIGS[acctype]
					if not (p[0].lower() in self._acc.name.lower()): self._acc.name += (' (%s)' % p[0])
					self._acc.server = p[1]
					self._acc.port = p[2]
				else:
					raise Exception('Unknown account type')
				
		self._window.destroy()
		return res

	
	def get_account(self):
		return self._acc
	
	
	def _fill_account_type_cmb(self):
		# fill acount type cmb
		for p in PROVIDER_CONFIGS:
			self._cmb_account_type.append_text(p[0])
		self._cmb_account_type.append_text(_("Other (IMAP)"))
		self._cmb_account_type.append_text(_("Other (POP3)"))
		
		# select account type
		if len(self._acc.server) == 0:
			# default to Gmail when creating new accounts
			self._cmb_account_type.set_active(IDX_GMAIL)
		else:
			i = 0
			idx = -1
			for p in PROVIDER_CONFIGS:
				if p[1] == self._acc.server:
					idx = i
					break
				i+=1
			
			if idx >= 0:
				self._cmb_account_type.set_active(idx)
			else:
				self._cmb_account_type.set_active(IDX_IMAP if self._acc.imap else IDX_POP3)
	
	
	def _has_multiple_folders(self):
		return ("," in self._entry_account_folders.get_text())
	
	
	def _on_btn_cancel_clicked(self, widget):
		pass


	def _on_btn_save_clicked(self, widget):
		pass

	
	def _on_entry_changed(self, widget):		
		if widget is self._entry_account_folders:
			# disable IMAP Push checkbox if multiple folders are specifed
			if self._has_multiple_folders():
				self._chk_account_push.set_active(False)
				self._chk_account_push.set_sensitive(False)
			else:
				self._chk_account_push.set_sensitive(True)
		else:
			# validate
			acctype = self._cmb_account_type.get_active()
			if (acctype == IDX_POP3) or (acctype == IDX_IMAP):
				ok = len(self._entry_account_name.get_text()) > 0 and \
					 len(self._entry_account_user.get_text()) > 0 and \
					 len(self._entry_account_password.get_text()) > 0 and \
					 len(self._entry_account_server.get_text()) > 0
			else: # known provider
				ok = len(self._entry_account_user.get_text()) > 0 and \
					 len(self._entry_account_password.get_text()) > 0
			
			self._button_save.set_sensitive(ok)
		
		
	def _on_cmb_account_type_changed(self, widget):
		acctype = self._cmb_account_type.get_active()
		
		if acctype == IDX_POP3:
			self._label_account_name.set_visible(True)
			self._entry_account_name.set_visible(True)
			self._label_account_server.set_visible(True)
			self._entry_account_server.set_visible(True)
			self._label_account_port.set_visible(True)
			self._entry_account_port.set_visible(True)
			self._label_account_folders.set_visible(False)
			self._entry_account_folders.set_visible(False)
			self._chk_account_push.set_visible(False)
			self._chk_account_ssl.set_visible(True)
		elif acctype == IDX_IMAP:
			self._label_account_name.set_visible(True)
			self._entry_account_name.set_visible(True)
			self._label_account_server.set_visible(True)
			self._entry_account_server.set_visible(True)
			self._label_account_port.set_visible(True)
			self._entry_account_port.set_visible(True)
			self._label_account_folders.set_visible(True)
			self._entry_account_folders.set_visible(True)
			self._chk_account_push.set_visible(True)
			self._chk_account_ssl.set_visible(True)
		else: # known provider (imap only)
			self._label_account_name.set_visible(False)
			self._entry_account_name.set_visible(False)
			self._label_account_server.set_visible(False)
			self._entry_account_server.set_visible(False)
			self._label_account_port.set_visible(False)
			self._entry_account_port.set_visible(False)
			self._label_account_folders.set_visible(True)
			self._entry_account_folders.set_visible(True)
			self._chk_account_push.set_visible(False)
			self._chk_account_ssl.set_visible(False)


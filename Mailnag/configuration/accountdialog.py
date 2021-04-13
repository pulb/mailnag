# Copyright 2011 - 2021 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2016, 2019 Timo Kankare <timo.kankare@iki.fi>
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

import os
import json
import logging
import base64
import urllib
import urllib.request
import io
from http.cookiejar import CookieJar
from http.client import HTTPMessage
from _thread import start_new_thread

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GLib', '2.0')
from gi.repository import GObject, GLib, Gtk, Gdk

from Mailnag.common.dist_cfg import PACKAGE_NAME
from Mailnag.common.i18n import _
from Mailnag.common.utils import get_data_file, splitstr
from Mailnag.common.accounts import Account
from Mailnag.backends.gmail_rss import (
	GMAIL_URL,
	GMAIL_RSS_URL,
	load_gmail_cookies,
	save_gmail_cookies,
	generate_gmail_cookies_key,
)

IDX_GMAIL	= 0
IDX_GMX		= 1
IDX_WEB_DE	= 2
IDX_YAHOO	= 3
IDX_IMAP	= 4
IDX_POP3	= 5
IDX_MBOX	= 6
IDX_MAILDIR	= 7
IDX_GMAIL_RSS   = 8

GMAIL_SUPPORT_PAGE = "https://support.google.com/mail/answer/185833?hl=en"

PROVIDER_CONFIGS = [
	[ 'Gmail', 'imap.gmail.com', '993'],
	[ 'GMX', 'imap.gmx.net', '993'],
	[ 'Web.de', 'imap.web.de', '993'],
	[ 'Yahoo', 'imap.mail.yahoo.com', '993']
]


def folder_cell_data(tree_column, cell, model, iter, *data):
	value = model[iter][1]
	if value == '':
		value = '[root folder]'
	cell.set_property('text', value)

class FakeHTTPResonse:
	"""Dummy response for working with CookieJar"""
	def __init__(self, set_cookie_headers):
		msg = HTTPMessage()
		for set_cookie_header in set_cookie_headers:
			msg.add_header("Set-Cookie", set_cookie_header)
		self._info = msg
	def info(self):
		return self._info

class AccountDialog:
	def __init__(self, parent, acc):
		self._acc = acc
		self._gmail_cookies_key = ''
		self._gmail_cookies = CookieJar()

		builder = Gtk.Builder()
		builder.set_translation_domain(PACKAGE_NAME)
		builder.add_from_file(get_data_file("account_widget.ui"))
		builder.connect_signals({
			"account_type_changed" : self._on_cmb_account_type_changed,
			"entry_changed" : self._on_entry_changed,
			"expander_folders_activate" : self._on_expander_folders_activate,
			"password_info_icon_released" : self._on_password_info_icon_released,
			"log_in" : self._on_log_in,
			"gmail_label_add" : self._on_gmail_label_add,
			"gmail_label_remove" : self._on_gmail_label_remove,
			"gmail_label_edited" : self._on_gmail_label_edited,
			"gmail_label_mode_edited" : self._on_gmail_label_mode_edited,
			"gmail_labels_selection_changed" : self._on_gmail_labels_selection_changed,
		})

		self._window = Gtk.Dialog(title = _('Mail Account'), parent = parent, use_header_bar = True, \
			buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self._window.set_default_response(Gtk.ResponseType.OK)
		self._window.set_default_size(400, 0)

		self._box = self._window.get_content_area()
		self._box.set_border_width(12)
		self._box.set_spacing(12)

		self._box.pack_start(builder.get_object("account_widget"), True, True, 0)

		self._cmb_account_type = builder.get_object("cmb_account_type")
		self._label_log_in = builder.get_object("label_log_in")
		self._label_gmail_labels = builder.get_object("label_gmail_labels")
		self._box_gmail_labels = builder.get_object("box_gmail_labels")
		self._button_log_in = builder.get_object("button_log_in")
		self._button_remove_gmail_label = builder.get_object("button_remove_gmail_label")
		self._label_account_name = builder.get_object("label_account_name")
		self._entry_account_name = builder.get_object("entry_account_name")
		self._label_account_user = builder.get_object("label_account_user")
		self._entry_account_user = builder.get_object("entry_account_user")
		self._label_account_password = builder.get_object("label_account_password")
		self._entry_account_password = builder.get_object("entry_account_password")
		self._label_account_server = builder.get_object("label_account_server")
		self._entry_account_server = builder.get_object("entry_account_server")
		self._label_account_port = builder.get_object("label_account_port")
		self._entry_account_port = builder.get_object("entry_account_port")
		self._label_account_file_path = builder.get_object("label_account_file_path")
		self._chooser_account_file_path = builder.get_object("chooser_file_path")
		self._label_account_directory_path = builder.get_object("label_account_directory_path")
		self._chooser_account_directory_path = builder.get_object("chooser_directory_path")
		self._expander_folders = builder.get_object("expander_folders")
		self._overlay = builder.get_object("overlay")
		self._treeview_folders = builder.get_object("treeview_folders")
		self._liststore_folders = builder.get_object("liststore_folders")
		self._liststore_gmail_labels = builder.get_object("liststore_gmail_labels")
		self._treeview_gmail_labels = builder.get_object("treeview_gmail_labels")
		self._chk_account_push = builder.get_object("chk_account_push")
		self._chk_account_ssl = builder.get_object("chk_account_ssl")

		self._button_ok = self._window.get_widget_for_response(Gtk.ResponseType.OK)
		self._button_ok.set_sensitive(False)

		self._error_label = None
		self._folders_received = False
		self._selected_folder_count = 0
		self._pwd_info_icon = self._entry_account_password.get_icon_name(Gtk.EntryIconPosition.SECONDARY)

		self._entry_account_port.set_placeholder_text(_("optional"))

		renderer_folders_enabled = Gtk.CellRendererToggle()
		renderer_folders_enabled.connect("toggled", self._on_folder_toggled)
		column_folders_enabled = Gtk.TreeViewColumn(_('Enabled'), renderer_folders_enabled)
		column_folders_enabled.add_attribute(renderer_folders_enabled, "active", 0)
		column_folders_enabled.set_alignment(0.5)
		self._treeview_folders.append_column(column_folders_enabled)

		renderer_folders_name = Gtk.CellRendererText()
		column_folders_name = Gtk.TreeViewColumn(_('Name'), renderer_folders_name, text = 1)
		column_folders_name.set_cell_data_func(renderer_folders_name, folder_cell_data)
		self._treeview_folders.append_column(column_folders_name)
		self._on_gmail_labels_selection_changed(
			self._treeview_gmail_labels.get_selection())

	def run(self):
		self._fill_account_type_cmb()
		self._load_account(self._acc)

		res = self._window.run()

		if res == Gtk.ResponseType.OK:
			self._configure_account(self._acc)

		self._window.destroy()
		return res


	def get_account(self):
		return self._acc


	def _load_account(self, acc):
		config = acc.get_config()
		self._entry_account_name.set_text(acc.name)
		if 'user' in config:
			self._entry_account_user.set_text(config['user'])
		if 'password' in config:
			self._entry_account_password.set_text(config['password'])
		if 'gmail_labels' in config:
			self._liststore_gmail_labels.clear()
			for data in config['gmail_labels']:
				self._liststore_gmail_labels.append(
					[data["label"],
					 data.get("mode", "Include")])
		if 'server' in config:
			self._entry_account_server.set_text(config['server'])
		if 'port' in config:
			self._entry_account_port.set_text(config['port'])
		if 'idle' in config:
			self._chk_account_push.set_active(config['idle'])
		if 'folders' in config:
			self._chk_account_push.set_sensitive(len(config['folders']) < 2)
		if 'ssl' in config:
			self._chk_account_ssl.set_active(config['ssl'])
		if ('path' in config) and os.path.exists(config.get('path')):
			self._chooser_account_file_path.set_filename(config.get('path'))
			# Workaround: fire the on-entry-changed signal manually as it is only called
			# when the user changes the file by mouse or keyboard.
			# See https://developer.gnome.org/gtk3/stable/GtkFileChooserButton.html#GtkFileChooserButton-file-set
			self._on_entry_changed(self._chooser_account_file_path)
			self._chooser_account_directory_path.set_filename(config.get('path'))
			self._on_entry_changed(self._chooser_account_directory_path)
		if acc.mailbox_type == 'gmail_rss' and acc.name and 'password' in config:
			self._set_gmail_credentials(
				config['password'],
				load_gmail_cookies(acc.name, config['password']))
		self._on_entry_changed(None)

	def _configure_account(self, acc):
		config = {}
		acctype = self._cmb_account_type.get_active()

		if (acctype == IDX_POP3) or (acctype == IDX_IMAP):
			name = self._entry_account_name.get_text()
			config['user'] = self._entry_account_user.get_text()
			config['password'] = self._entry_account_password.get_text()
			config['server'] = self._entry_account_server.get_text()
			config['folders'] = []
			config['port'] = self._entry_account_port.get_text()
			config['ssl'] = self._chk_account_ssl.get_active()

			if acctype == IDX_POP3:
				mailbox_type = 'pop3'
				config['imap'] = False
				config['idle'] = False
			elif acctype == IDX_IMAP:
				mailbox_type = 'imap'
				config['imap'] = True
				if self._folders_received:
					config['folders'] = self._get_selected_folders()
				config['idle'] = self._chk_account_push.get_active()
		elif acctype == IDX_MBOX:
			mailbox_type = 'mbox'
			name = self._entry_account_name.get_text()
			config['folders'] = []
			config['path'] = self._chooser_account_file_path.get_filename()
		elif acctype == IDX_MAILDIR:
			mailbox_type = 'maildir'
			name = self._entry_account_name.get_text()
			config['path'] = self._chooser_account_directory_path.get_filename()
			config['folders'] = []
			if self._folders_received:
				config['folders'] = self._get_selected_folders()
		elif acctype == IDX_GMAIL_RSS:
			name = self._entry_account_name.get_text()
			mailbox_type = 'gmail_rss'
			assert self._gmail_cookies_key
			assert self._gmail_cookies
			config['password'] = self._gmail_cookies_key
			save_gmail_cookies(name, self._gmail_cookies_key, self._gmail_cookies)
			label_list = []
			def _row_cb(model, _path, it):
				label, mode = model.get(it, 0, 1)
				label_list.append({
					"label": label,
					"mode": mode,
				})
			self._liststore_gmail_labels.foreach(_row_cb)
			config['gmail_labels'] = label_list

		else: # known provider (imap only)
			mailbox_type = 'imap'
			name = self._entry_account_user.get_text()
			config['user'] = self._entry_account_user.get_text()
			config['password'] = self._entry_account_password.get_text()
			config['ssl'] = True
			config['imap'] = True
			config['folders'] = []
			if self._folders_received:
				config['folders'] = self._get_selected_folders()
			config['idle'] = (len(config['folders']) < 2)

			if acctype < len(PROVIDER_CONFIGS):
				p = PROVIDER_CONFIGS[acctype]
				name += (' (%s)' % p[0])
				config['server'] = p[1]
				config['port'] = p[2]
			else:
				raise Exception('Unknown account type')

		acc.set_config(
			mailbox_type=mailbox_type,
			enabled=acc.enabled,
			name=name,
			config=config)


	def _get_selected_folders(self):
		folders = []
		for row in self._liststore_folders:
			if row[0]:
				folders.append(row[1])
		return folders


	def _fill_account_type_cmb(self):
		# fill acount type cmb
		for p in PROVIDER_CONFIGS:
			self._cmb_account_type.append_text(p[0])
		self._cmb_account_type.append_text(_("IMAP (Custom)"))
		self._cmb_account_type.append_text(_("POP3 (Custom)"))
		self._cmb_account_type.append_text(_("MBox (Custom)"))
		self._cmb_account_type.append_text(_("Maildir (Custom)"))
		self._cmb_account_type.append_text(_("GMail RSS (No IMAP)"))

		config = self._acc.get_config()

		# select account type
		if self._acc.mailbox_type == '':
			# default to Gmail when creating new accounts
			idx = IDX_GMAIL
		else:
			idx = -1
			if 'user' in config and 'server' in config and 'port' in config:
				user = config['user']
				server = config['server']
				port = config['port']
				for i, p in enumerate(PROVIDER_CONFIGS):
					if (('%s (%s)' % (user, p[0])) == self._acc.name) and \
							p[1] == server and p[2] == port:
						idx = i
						break

			if idx < 0:
				if self._acc.mailbox_type == 'imap':
					idx = IDX_IMAP
				elif self._acc.mailbox_type == 'pop3':
					idx = IDX_POP3
				elif self._acc.mailbox_type == 'mbox':
					idx = IDX_MBOX
				elif self._acc.mailbox_type == 'maildir':
					idx = IDX_MAILDIR
				elif self._acc.mailbox_type == 'gmail_rss':
					idx = IDX_GMAIL_RSS
				else:
					# This is actually error case, but recovering to IMAP
					idx = IDX_IMAP
		self._cmb_account_type.set_active(idx) # triggers _on_cmb_account_type_changed()
		# Don't allow changing the account type if the loaded account has folders.
		if 'folders' in config:
			is_type_change_allowed = len(config['folders']) == 0
		else:
			is_type_change_allowed = True
		self._cmb_account_type.set_sensitive(is_type_change_allowed)


	def _on_entry_changed(self, widget):
		#
		# Validate
		#
		acctype = self._cmb_account_type.get_active()
		if (acctype == IDX_POP3) or (acctype == IDX_IMAP):
			ok = len(self._entry_account_name.get_text()) > 0 and \
				 len(self._entry_account_user.get_text()) > 0 and \
				 len(self._entry_account_password.get_text()) > 0 and \
				 len(self._entry_account_server.get_text()) > 0
		elif acctype == IDX_MBOX:
			ok = len(self._entry_account_name.get_text()) > 0 and \
				 (self._chooser_account_file_path.get_filename() is not None)
		elif acctype == IDX_MAILDIR:
			ok = len(self._entry_account_name.get_text()) > 0 and \
				 (self._chooser_account_directory_path.get_filename() is not None)
		elif acctype == IDX_GMAIL_RSS:
			ok = len(self._entry_account_name.get_text()) > 0 and \
				self._gmail_cookies and self._gmail_cookies_key
		else: # known provider
			ok = len(self._entry_account_user.get_text()) > 0 and \
				 len(self._entry_account_password.get_text()) > 0

		self._expander_folders.set_sensitive(self._folders_received or ok)
		self._button_ok.set_sensitive(ok)


	def _on_expander_folders_activate(self, widget):
		# Folder list has already been loaded or
		# expander is going to be closed -> do nothing.
		if self._folders_received or \
				self._expander_folders.get_expanded():
			return

		if self._error_label != None:
			self._error_label.destroy()
			self._error_label = None

		spinner = Gtk.Spinner()
		spinner.set_halign(Gtk.Align.CENTER)
		spinner.set_valign(Gtk.Align.CENTER)
		spinner.start()

		self._overlay.add_overlay(spinner)
		self._overlay.show_all()

		# Executed on a new worker thread
		def worker_thread(name):
			folders = []
			exception = None

			try:
				acc = Account()
				self._configure_account(acc)
				folders = acc.request_server_folders()
			except Exception as ex:
				exception = ex

			# Executed on the GTK main thread
			def finished_func():
				spinner.stop()
				spinner.destroy()

				if exception != None:
					self._error_label = Gtk.Label()
					self._error_label.set_justify(Gtk.Justification.CENTER)
					self._error_label.set_halign(Gtk.Align.CENTER)
					self._error_label.set_valign(Gtk.Align.CENTER)
					self._error_label.set_markup('<span foreground="red"><b>%s</b></span>' % _('Connection failed.'))

					self._overlay.add_overlay(self._error_label)
					self._overlay.show_all()
				else:
					for f in folders:
						enabled = False
						if f in self._acc.folders:
							enabled = True
							self._selected_folder_count += 1
						row = [enabled, f]
						self._liststore_folders.append(row)

					# Enable the push checkbox in case a remote folder wasn't found
					# and the folder count is now <2.
					# (e.g. folders have been renamed/removed on the server, the user has entered a
					# diffent username/password in this dialog, ...)
					self._chk_account_push.set_sensitive(self._selected_folder_count < 2)
					self._folders_received = True

			GObject.idle_add(finished_func)

		start_new_thread(worker_thread, ("worker_thread",))


	def _on_password_info_icon_released(self, widget, icon_pos, event):
		Gtk.show_uri_on_window(None, GMAIL_SUPPORT_PAGE, Gdk.CURRENT_TIME)


	def _on_folder_toggled(self, cell, path):
		isactive = not cell.get_active()
		model = self._liststore_folders
		iter = model.get_iter(path)
		self._liststore_folders.set_value(iter, 0, isactive)

		if isactive:
			self._selected_folder_count += 1
		else:
			self._selected_folder_count -= 1

		if self._selected_folder_count < 2:
			self._chk_account_push.set_sensitive(True)
		else:
			self._chk_account_push.set_active(False)
			self._chk_account_push.set_sensitive(False)


	def _on_cmb_account_type_changed(self, widget):
		acctype = widget.get_active()
		self._entry_account_password.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, None)

		self._label_gmail_labels.set_visible(acctype == IDX_GMAIL_RSS)
		self._box_gmail_labels.set_visible(acctype == IDX_GMAIL_RSS)
		self._label_log_in.set_visible(acctype == IDX_GMAIL_RSS)
		self._button_log_in.set_visible(acctype == IDX_GMAIL_RSS)

		#
		# Reset everything when the account type changes
		#

		if acctype == IDX_POP3:
			self._label_account_name.set_visible(True)
			self._entry_account_name.set_visible(True)
			self._label_account_user.set_visible(True)
			self._entry_account_user.set_visible(True)
			self._label_account_password.set_visible(True)
			self._entry_account_password.set_visible(True)
			self._label_account_server.set_visible(True)
			self._entry_account_server.set_visible(True)
			self._label_account_port.set_visible(True)
			self._entry_account_port.set_visible(True)
			self._expander_folders.set_visible(False)
			self._chk_account_push.set_visible(False)
			self._chk_account_ssl.set_visible(True)
			self._label_account_file_path.set_visible(False)
			self._chooser_account_file_path.set_visible(False)
			self._label_account_directory_path.set_visible(False)
			self._chooser_account_directory_path.set_visible(False)
		elif acctype == IDX_IMAP:
			self._label_account_name.set_visible(True)
			self._entry_account_name.set_visible(True)
			self._label_account_user.set_visible(True)
			self._entry_account_user.set_visible(True)
			self._label_account_password.set_visible(True)
			self._entry_account_password.set_visible(True)
			self._label_account_server.set_visible(True)
			self._entry_account_server.set_visible(True)
			self._label_account_port.set_visible(True)
			self._entry_account_port.set_visible(True)
			self._expander_folders.set_visible(True)
			self._chk_account_push.set_visible(True)
			self._chk_account_ssl.set_visible(True)
			self._label_account_file_path.set_visible(False)
			self._chooser_account_file_path.set_visible(False)
			self._label_account_directory_path.set_visible(False)
			self._chooser_account_directory_path.set_visible(False)
		elif acctype == IDX_MBOX:
			self._label_account_name.set_visible(True)
			self._entry_account_name.set_visible(True)
			self._label_account_user.set_visible(False)
			self._entry_account_user.set_visible(False)
			self._label_account_password.set_visible(False)
			self._entry_account_password.set_visible(False)
			self._label_account_server.set_visible(False)
			self._entry_account_server.set_visible(False)
			self._label_account_port.set_visible(False)
			self._entry_account_port.set_visible(False)
			self._expander_folders.set_visible(False)
			self._chk_account_push.set_visible(False)
			self._chk_account_ssl.set_visible(False)
			self._label_account_file_path.set_visible(True)
			self._chooser_account_file_path.set_visible(True)
			self._label_account_directory_path.set_visible(False)
			self._chooser_account_directory_path.set_visible(False)
		elif acctype == IDX_MAILDIR:
			self._label_account_name.set_visible(True)
			self._entry_account_name.set_visible(True)
			self._label_account_user.set_visible(False)
			self._entry_account_user.set_visible(False)
			self._label_account_password.set_visible(False)
			self._entry_account_password.set_visible(False)
			self._label_account_server.set_visible(False)
			self._entry_account_server.set_visible(False)
			self._label_account_port.set_visible(False)
			self._entry_account_port.set_visible(False)
			self._expander_folders.set_visible(True)
			self._chk_account_push.set_visible(False)
			self._chk_account_ssl.set_visible(False)
			self._label_account_file_path.set_visible(False)
			self._chooser_account_file_path.set_visible(False)
			self._label_account_directory_path.set_visible(True)
			self._chooser_account_directory_path.set_visible(True)
		elif acctype == IDX_GMAIL_RSS:
			self._label_account_name.set_visible(True)
			self._entry_account_name.set_visible(True)
			self._label_account_user.set_visible(False)
			self._entry_account_user.set_visible(False)
			self._label_account_password.set_visible(False)
			self._entry_account_password.set_visible(False)
			self._label_account_server.set_visible(False)
			self._entry_account_server.set_visible(False)
			self._label_account_port.set_visible(False)
			self._entry_account_port.set_visible(False)
			self._expander_folders.set_visible(False)
			self._chk_account_push.set_visible(False)
			self._chk_account_ssl.set_visible(False)
			self._label_account_file_path.set_visible(False)
			self._chooser_account_file_path.set_visible(False)
			self._label_account_directory_path.set_visible(False)
			self._chooser_account_directory_path.set_visible(False)

		else: # known provider (imap only)
			self._label_account_name.set_visible(False)
			self._entry_account_name.set_visible(False)
			self._label_account_user.set_visible(True)
			self._entry_account_user.set_visible(True)
			self._label_account_password.set_visible(True)
			self._entry_account_password.set_visible(True)
			self._label_account_server.set_visible(False)
			self._entry_account_server.set_visible(False)
			self._label_account_port.set_visible(False)
			self._entry_account_port.set_visible(False)
			self._expander_folders.set_visible(True)
			self._chk_account_push.set_visible(False)
			self._chk_account_ssl.set_visible(False)
			self._label_account_file_path.set_visible(False)
			self._chooser_account_file_path.set_visible(False)
			self._label_account_directory_path.set_visible(False)
			self._chooser_account_directory_path.set_visible(False)

			if acctype == IDX_GMAIL:
				self._entry_account_password.set_icon_from_icon_name(
					Gtk.EntryIconPosition.SECONDARY, self._pwd_info_icon)

		self._folders_received = False
		self._selected_folder_count = 0

		self._expander_folders.set_expanded(False)
		self._liststore_folders.clear()

		empty_acc = Account()
		self._load_account(empty_acc)

	def _on_gmail_label_add(self, _widget):
		it = self._liststore_gmail_labels.append(
			["<new label>", "Include"])
		self._treeview_gmail_labels.set_cursor_on_cell(
			self._liststore_gmail_labels.get_path(it),
			focus_column=self._treeview_gmail_labels.get_column(0),
			focus_cell=None,
			start_editing=True)

	def _on_gmail_label_remove(self, _widget):
		model = self._liststore_gmail_labels
		selection = self._treeview_gmail_labels.get_selection()
		_, row_paths = selection.get_selected_rows()
		row_refs = [Gtk.TreeRowReference(model, path)
			    for path in row_paths]
		for row_ref in row_refs:
			model.remove(model.get_iter(row_ref.get_path()))

	def _on_gmail_labels_selection_changed(self, selection):
		self._button_remove_gmail_label.set_sensitive(
			selection.count_selected_rows() > 0)

	def _on_gmail_label_edited(self, cell, path, new_text):
		if not new_text:
			return
		it = self._liststore_gmail_labels.get_iter_from_string(path)
		self._liststore_gmail_labels.set_value(it, 0, new_text)

	def _on_gmail_label_mode_edited(self, cell, path, new_value_it):
		[new_text] = cell.get_property("model").get(new_value_it, 0)
		if new_text not in ["Include", "Exclude"]:
			return
		it = self._liststore_gmail_labels.get_iter_from_string(path)
		self._liststore_gmail_labels.set_value(it, 1, new_text)

	def _set_gmail_credentials(self, password, cookies):
		self._gmail_cookies_key = password
		self._gmail_cookies = cookies
		if password and cookies:
			self._button_log_in.set_label(_("Logged in"))
		else:
			self._button_log_in.set_label(_("Log in to account"))

	def _on_log_in(self, _widget):
		import gi
		gi.require_version('WebKit2', '4.0')
		from gi.repository import Gtk, WebKit2, Soup
		loop = GLib.MainLoop()
		window = Gtk.Window()
		window.set_title("Log in to GMail")
		window.set_default_size(800, 600)
		window.set_destroy_with_parent(True)
		window.set_transient_for(self._window)
		window.set_modal(True)
		scrolled_window = Gtk.ScrolledWindow()
		window.add(scrolled_window)
		webview = WebKit2.WebView()
		webview.load_uri(GMAIL_URL)
		scrolled_window.add(webview)
		window.connect("destroy", lambda _: loop.quit())
		got_to_inbox = False
		def _on_load_changed(_, load_event):
			if load_event != WebKit2.LoadEvent.FINISHED:
				return
			uri = webview.get_uri()
			nonlocal got_to_inbox
			if uri == "https://mail.google.com/mail/u/0/#inbox":
				nonlocal got_to_inbox
				got_to_inbox = True
				window.destroy()
		webview.connect("load-changed", _on_load_changed)
		window.show_all()
		loop.run()
		cookie_headers = None
		def _got_cookies(cookies, result, data):
			try:
				headers = []
				for cookie in cookies.get_cookies_finish(result):
					headers.append(cookie.to_set_cookie_header())
				nonlocal cookie_headers
				cookie_headers = headers
			except:
				logging.warning("getting cookies failed", exc_info=True)
			loop.quit()
		webview.get_context().get_cookie_manager().get_cookies(
			GMAIL_RSS_URL, None, _got_cookies, None)
		loop.run()
		window.destroy()
		if not cookie_headers:
			logging.warning("could not set cookies from login")
			return
		if not got_to_inbox:
			logging.warning("login dialog closed before login done")
			return
		cookie_jar = CookieJar()
		cookie_jar.extract_cookies(
			FakeHTTPResonse(cookie_headers),
			urllib.request.Request(GMAIL_RSS_URL))
		self._set_gmail_credentials(generate_gmail_cookies_key(), cookie_jar)
			
		self._on_entry_changed(None)

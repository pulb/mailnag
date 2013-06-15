#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# configwindow.py
#
# Copyright 2011 - 2013 Patrick Ulbrich <zulu99@gmx.net>
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

import os
import xdg.BaseDirectory as bd
from gi.repository import GLib, GdkPixbuf, Gtk, GObject

from common.dist_cfg import PACKAGE_NAME, APP_VERSION
from common.i18n import _
from common.utils import get_data_file
from common.config import read_cfg, write_cfg
from common.accountlist import AccountList
from common.account import Account
from configuration.accountdialog import AccountDialog

class ConfigWindow:
	def __init__(self):
		builder = Gtk.Builder()
		builder.set_translation_domain(PACKAGE_NAME)
		builder.add_from_file(get_data_file("config_window.ui"))
		builder.connect_signals({ \
			"config_window_deleted" : self._on_config_window_deleted, \
			"btn_add_clicked" : self._on_btn_add_clicked, \
			"btn_edit_clicked" : self._on_btn_edit_clicked, \
			"btn_remove_clicked" : self._on_btn_remove_clicked, \
			"treeview_accounts_row_activated" : self._on_treeview_accounts_row_activated, \
			"liststore_accounts_row_deleted" : self._on_liststore_accounts_row_deleted, \
			"liststore_accounts_row_inserted" : self._on_liststore_accounts_row_inserted, \
		})

		self._window = builder.get_object("config_window")
		self._window.set_icon(GdkPixbuf.Pixbuf.new_from_file_at_size(get_data_file("mailnag.svg"), 48, 48));
		self._cfg = read_cfg()
		
		self.daemon_enabled = False
		
		#
		# general tab
		#
		self._image_logo = builder.get_object("image_logo")
		pb = GdkPixbuf.Pixbuf.new_from_file_at_size(get_data_file("mailnag.svg"), 180, 180)
		pb = pb.new_subpixbuf(0, 10, 180, 146) # crop whitespace at the bottom
		self._image_logo.set_from_pixbuf(pb)
		self._label_app_desc = builder.get_object("label_app_desc")
		self._label_app_desc.set_markup("<span font=\"24\"><b>Mailnag</b></span>\nVersion %s" % str(APP_VERSION))
		self._switch_daemon_enabled = builder.get_object("switch_daemon_enabled")
		
		#
		# accounts tab
		#
		self._accounts = AccountList()

		self._treeview_accounts = builder.get_object("treeview_accounts")
		self._liststore_accounts = builder.get_object("liststore_accounts")

		self._button_edit = builder.get_object("btn_edit")
		self._button_remove = builder.get_object("btn_remove")

		renderer_on = Gtk.CellRendererToggle()
		renderer_on.connect("toggled", self._on_account_toggled)
		column_on = Gtk.TreeViewColumn(_('Enabled'), renderer_on)
		column_on.add_attribute(renderer_on, "active", 1)
		column_on.set_alignment(0.5)
		self._treeview_accounts.append_column(column_on)

		renderer_name = Gtk.CellRendererText()
		column_name = Gtk.TreeViewColumn(_('Name'), renderer_name, text=2)
		self._treeview_accounts.append_column(column_name)

		self._spinbutton_interval = builder.get_object("spinbutton_interval")
		
		#
		# plugins tab
		#
		
		# TODO
		
		self._load_config()
		self._window.show()


	def _load_config(self):
		self._switch_daemon_enabled.set_active(bool(int(self._cfg.get('general', 'autostart'))))
		self._spinbutton_interval.set_value(int(self._cfg.get('general', 'check_interval')))
		
		self._accounts.load_from_cfg(self._cfg)
		
		for acc in self._accounts:
			row = [acc, acc.enabled, acc.name]
			self._liststore_accounts.append(row)
		self._select_path((0,))		
		

	def _save_config(self):
		autostart = self._switch_daemon_enabled.get_active()
		self._cfg.set('general', 'autostart', int(autostart))
		self._cfg.set('general', 'check_interval', int(self._spinbutton_interval.get_value()))

		self._accounts.save_to_cfg(self._cfg)
				
		write_cfg(self._cfg)

		if autostart: self._create_autostart()
		else: self._delete_autostart()


	def _show_yesno_dialog(self, text):
		message = Gtk.MessageDialog(self._window, Gtk.DialogFlags.MODAL, \
			Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, text)
		resp = message.run()
		message.destroy()
		if resp == Gtk.ResponseType.YES: return True
		else: return False
	
	
	def _get_selected_account(self):
		treeselection = self._treeview_accounts.get_selection()
		selection = treeselection.get_selected()
		model, iter = selection
		# get account object from treeviews 1. column
		if iter != None: acc = model.get_value(iter, 0)
		else: acc = None
		return acc, model, iter
	
	
	def _select_path(self, path):
		treeselection = self._treeview_accounts.get_selection()
		treeselection.select_path(path)
		self._treeview_accounts.grab_focus()


	def _edit_account(self):
		acc, model, iter = self._get_selected_account()
		if iter != None:
			d = AccountDialog(self._window, acc)
			
			if d.run() == 1:
				model.set_value(iter, 2, acc.name)


	def _create_autostart(self):
		# get current working directory
		curdir = os.getcwd()
		# path to mailnag startscript
		exec_file = os.path.join(curdir, "mailnag")

		content = "\n" + \
		"[Desktop Entry]\n" + \
		"Type=Application\n" + \
		"Exec=" + exec_file + "\n" + \
		"Hidden=false\n" + \
		"NoDisplay=false\n" + \
		"X-GNOME-Autostart-enabled=true\n" + \
		"Name=Mailnag\n" + \
		"Comment=Email notifier for GNOME 3\n" \
		"OnlyShowIn=GNOME;\n" \
		"AutostartCondition=GNOME3 if-session gnome"

		autostart_folder = os.path.join(bd.xdg_config_home, "autostart")
		if not os.path.exists(autostart_folder):
			os.makedirs(autostart_folder)
		autostart_file = os.path.join(autostart_folder, "mailnag.desktop")
		f = open(autostart_file, 'w') # create file
		f.write(content)
		f.close()


	def _delete_autostart(self):
		autostart_folder = os.path.join(bd.xdg_config_home, "autostart")
		autostart_file = autostart_folder + "mailnag.desktop"
		if os.path.exists(autostart_file):
			os.remove(autostart_file)


	def _on_account_toggled(self, cell, path):
		model = self._liststore_accounts
		iter = model.get_iter(path)
		acc = model.get_value(iter, 0)
		acc.enabled = not acc.enabled
		
		self._liststore_accounts.set_value(iter, 1, not cell.get_active())
		

	def _on_btn_add_clicked(self, widget):
		acc = Account(enabled = True, name = '')
		d = AccountDialog(self._window, acc)
	
		if d.run() == 1:
			self._accounts.append(acc)
			
			row = [acc, acc.enabled, acc.name]
			iter = self._liststore_accounts.append(row)
			model = self._treeview_accounts.get_model()
			path = model.get_path(iter)
			self._treeview_accounts.set_cursor(path, None, False)
			self._treeview_accounts.grab_focus()


	def _on_btn_edit_clicked(self, widget):
		self._edit_account()


	def _on_btn_remove_clicked(self, widget):
		acc, model, iter = self._get_selected_account()
		if iter != None:
			if self._show_yesno_dialog(_('Delete this account:') + \
				'\n\n' + acc.name):
				
				# select prev/next account
				p = model.get_path(iter)
				if not p.prev():
					p.next()
				self._select_path(p)
				
				# remove from treeview
				model.remove(iter)
				# remove from accounts list
				self._accounts.remove(acc)


	def _on_treeview_accounts_row_activated(self, treeview, path, view_column):
		self._edit_account()


	def _on_liststore_accounts_row_deleted(self, model, path):
		self._button_edit.set_sensitive(len(model) > 0)
		self._button_remove.set_sensitive(len(model) > 0)


	def _on_liststore_accounts_row_inserted(self, model, path, user_param):
		self._button_edit.set_sensitive(len(model) > 0)
		self._button_remove.set_sensitive(len(model) > 0)
		
	
	def _save_and_quit(self):
		self._save_config()	
		self.daemon_enabled = self._switch_daemon_enabled.get_active()
		Gtk.main_quit()
		

	def _on_config_window_deleted(self, widget, event):
		self._save_and_quit()



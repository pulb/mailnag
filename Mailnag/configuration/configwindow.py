#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# configwindow.py
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

import os
from gi.repository import GLib, GdkPixbuf, Gtk, GObject

from common.i18n import PACKAGE_NAME, _
from common.utils import get_data_file
from common.config import read_cfg, write_cfg, APP_VERSION
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
			"chk_enable_filter_toggled" : self._on_chk_enable_filter_toggled, \
			"chk_script0_toggled" : self._on_chk_script0_toggled, \
			"chk_script1_toggled" : self._on_chk_script1_toggled \
		})

		self._window = builder.get_object("config_window")
		self._window.set_icon(GdkPixbuf.Pixbuf.new_from_file_at_size(get_data_file("mailnag.svg"), 48, 48));
		self._cfg = read_cfg()
		
		#
		# account tab
		#
		self._accounts = AccountList()

		self._treeview_accounts = builder.get_object("treeview_accounts")
		self._liststore_accounts = builder.get_object("liststore_accounts")

		self._button_edit = builder.get_object("button_edit")
		self._button_remove = builder.get_object("button_remove")

		renderer_on = Gtk.CellRendererToggle()
		renderer_on.connect("toggled", self._on_account_toggled)		# bind toggle signal
		column_on = Gtk.TreeViewColumn(_('Enabled'), renderer_on)		# Account On/Off
		column_on.add_attribute(renderer_on, "active", 1)
		column_on.set_alignment(0.5)									# center column heading
		self._treeview_accounts.append_column(column_on)

		renderer_name = Gtk.CellRendererText()
		column_name = Gtk.TreeViewColumn(_('Name'), renderer_name, text=2)	# Account Name
		self._treeview_accounts.append_column(column_name)

		#
		# general tab
		#
		self._entry_label = builder.get_object("entry_label")	
		self._spinbutton_interval = builder.get_object("spinbutton_interval")
		self._cb_notification_mode = builder.get_object("cb_notification_mode")
		cell = Gtk.CellRendererText()
		self._cb_notification_mode.pack_start(cell, True)
		self._cb_notification_mode.add_attribute(cell, "text", 0)
		self._chk_playsound = builder.get_object("chk_playsound")
		self._chk_autostart = builder.get_object("chk_autostart")
		
		#
		# spam filter tab
		#
		self._chk_enable_filter = builder.get_object("chk_enable_filter")
		self._textview_filter = builder.get_object("textview_filter")	
		self._textbuffer_filter = builder.get_object("textbuffer_filter")	

		#
		# events tab
		#
		self._chk_script0 = builder.get_object("chk_script0")
		self._filechooser_script0 = builder.get_object("filechooser_script0")
		self._chk_script1 = builder.get_object("chk_script1")
		self._filechooser_script1 = builder.get_object("filechooser_script1")
		
		#
		# about tab
		#
		self._image_logo = builder.get_object("image_logo")
		pb = GdkPixbuf.Pixbuf.new_from_file_at_size(get_data_file("mailnag.svg"), 180, 180)
		pb = pb.new_subpixbuf(0, 0, 180, 150) # crop whitespace at the bottom
		self._image_logo.set_from_pixbuf(pb)
		self._label_app_desc = builder.get_object("label_app_desc")
		self._label_app_desc.set_markup("<span font=\"24\"><b>Mailnag</b></span>\nVersion %s" % str(APP_VERSION))

		self._load_config()
		self._window.show()


	def _load_config(self):
		self._entry_label.set_text(self._cfg.get('general', 'messagetray_label'))
		self._spinbutton_interval.set_value(int(self._cfg.get('general', 'check_interval')))
		self._cb_notification_mode.set_active(int(self._cfg.get('general', 'notification_mode')))
		self._chk_playsound.set_active(bool(int(self._cfg.get('general', 'playsound'))))
		self._chk_autostart.set_active(bool(int(self._cfg.get('general', 'autostart'))))

		
		self._chk_enable_filter.set_active(bool(int(self._cfg.get('filter', 'filter_enabled'))))
		self._textbuffer_filter.set_text(self._cfg.get('filter', 'filter_text'))

		self._chk_script0.set_active(bool(int(self._cfg.get('script', 'script0_enabled'))))
		
		tmp = self._cfg.get('script', 'script0_file')
		if len(tmp) > 0:
			self._filechooser_script0.set_filename(tmp)
		
		self._chk_script1.set_active(bool(int(self._cfg.get('script', 'script1_enabled'))))
		
		tmp = self._cfg.get('script', 'script1_file')
		if len(tmp) > 0:
			self._filechooser_script1.set_filename(tmp)
		
		self._accounts.load_from_cfg(self._cfg)
		
		if len(self._accounts) == 0:
			self._accounts.import_from_keyring()
			if len(self._accounts) > 0 and \
				(not self._show_yesno_dialog(_("Mailnag found %s mail accounts on this computer.\n\nDo you want to import them?") % len(self._accounts))):
				del self._accounts[:]

		for acc in self._accounts:
			row = [acc, acc.enabled, acc.name]
			self._liststore_accounts.append(row)
		self._select_path((0,))		
		

	def _save_config(self):
		self._cfg.set('general', 'messagetray_label', self._entry_label.get_text())
		self._cfg.set('general', 'check_interval', int(self._spinbutton_interval.get_value()))
		self._cfg.set('general', 'notification_mode', int(self._cb_notification_mode.get_active()))
		self._cfg.set('general', 'playsound',int(self._chk_playsound.get_active()))
		autostart = self._chk_autostart.get_active()
		self._cfg.set('general', 'autostart', int(autostart))

		self._cfg.set('filter', 'filter_enabled', int(self._chk_enable_filter.get_active()))
		start, end = self._textbuffer_filter.get_bounds()		
		self._cfg.set('filter', 'filter_text', self._textbuffer_filter.get_text(start, end, True))	
		
		self._cfg.set('script', 'script0_enabled', int(self._chk_script0.get_active()))
		tmp = self._filechooser_script0.get_filename()
		if tmp == None: tmp = ""
		self._cfg.set('script', 'script0_file', tmp)
		
		self._cfg.set('script', 'script1_enabled', int(self._chk_script1.get_active()))
		tmp = self._filechooser_script1.get_filename()
		if tmp == None: tmp = ""
		self._cfg.set('script', 'script1_file', tmp)
		
		self._accounts.save_to_cfg(self._cfg)
				
		write_cfg(self._cfg)

		if autostart: self._create_autostart()
		else: self._delete_autostart()


	def _show_yesno_dialog(self, text):									# Show YesNo Dialog
		message = Gtk.MessageDialog(self._window, Gtk.DialogFlags.MODAL, \
			Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, text)
		resp = message.run()											# show dialog window
		message.destroy()												# close dialog
		if resp == Gtk.ResponseType.YES: return True					# if YES clicked
		else: return False												# if NO clicked
	
	
	def _get_selected_account(self):									# return selected row
		treeselection = self._treeview_accounts.get_selection()			# get tree_selection object
		selection = treeselection.get_selected()						# get selected tupel (model, iter)
		model, iter = selection											# get selected iter
		if iter != None: acc = model.get_value(iter, 0)					# get account object from treeviews 1. column
		else: acc = None
		return acc, model, iter
	
	
	def _select_path(self, path):										# select path in treeview
		treeselection = self._treeview_accounts.get_selection()			# get tree selection object
		treeselection.select_path(path)									# select path
		self._treeview_accounts.grab_focus()							# put focus on treeview


	def _edit_account(self):
		acc, model, iter = self._get_selected_account()
		if iter != None:
			d = AccountDialog(self._window, acc)
			
			if d.run() == 1:
				model.set_value(iter, 2, acc.name)


	def _create_autostart(self):
		curdir = os.getcwd()											# get working directory
		exec_file = os.path.join(curdir, "mailnag")						# path of the shell script to start mailnag.py

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

		autostart_folder = "%s/.config/autostart/" % (os.path.expanduser("~/"))
		if not os.path.exists(autostart_folder):
			os.makedirs(autostart_folder)
		autostart_file = autostart_folder + "mailnag.desktop"
		f = open(autostart_file, 'w')
		f.write(content) # create it
		f.close()


	def _delete_autostart(self):
		autostart_folder = "%s/.config/autostart/" % (os.path.expanduser("~/"))
		autostart_file = autostart_folder + "mailnag.desktop"
		if os.path.exists(autostart_file):
			os.remove(autostart_file)


	def _on_account_toggled(self, cell, path):							# chk_box account_on toggled
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
				
				p = model.get_path(iter)
				if not p.prev():
					p.next()
				self._select_path(p)									# select prev/next account
				
				model.remove(iter)										# delete in treeview
				self._accounts.remove(acc)								# delete in accounts list


	def _on_treeview_accounts_row_activated(self, treeview, path, view_column):
		self._edit_account()


	def _on_liststore_accounts_row_deleted(self, model, path):
		self._button_edit.set_sensitive(len(model) > 0)
		self._button_remove.set_sensitive(len(model) > 0)


	def _on_liststore_accounts_row_inserted(self, model, path, user_param):
		self._button_edit.set_sensitive(len(model) > 0)
		self._button_remove.set_sensitive(len(model) > 0)


	def _on_chk_enable_filter_toggled(self, widget):
		self._textview_filter.set_sensitive(self._chk_enable_filter.get_active())


	def _on_chk_script0_toggled(self, widget):
		self._filechooser_script0.set_sensitive(self._chk_script0.get_active())
		
	
	def _on_chk_script1_toggled(self, widget):
		self._filechooser_script1.set_sensitive(self._chk_script1.get_active())
		
	
	def _save_and_quit(self):
		self._save_config()	
		Gtk.main_quit()
		

	def _on_config_window_deleted(self, widget, event):
		self._save_and_quit()



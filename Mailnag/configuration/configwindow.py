# Copyright 2011 - 2021 Patrick Ulbrich <zulu99@gmx.net>
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

import gi
gi.require_version('Gtk', '3.0')

import os
import shutil
import xdg.BaseDirectory as bd
from gi.repository import Gtk

from Mailnag.common.dist_cfg import PACKAGE_NAME, APP_VERSION, BIN_DIR, DESKTOP_FILE_DIR
from Mailnag.common.i18n import _
from Mailnag.common.utils import get_data_file
from Mailnag.common.config import read_cfg, write_cfg
from Mailnag.common.accounts import Account, AccountManager
from Mailnag.common.plugins import Plugin
from Mailnag.configuration.accountdialog import AccountDialog
from Mailnag.configuration.plugindialog import PluginDialog


class ConfigWindow:
	def __init__(self, app):
		builder = Gtk.Builder()
		builder.set_translation_domain(PACKAGE_NAME)
		builder.add_from_file(get_data_file("config_window.ui"))
		builder.connect_signals({ \
			"config_window_deleted" : self._on_config_window_deleted, \
			"btn_info_clicked" : self._on_btn_info_clicked, \
			"btn_add_account_clicked" : self._on_btn_add_account_clicked, \
			"btn_edit_account_clicked" : self._on_btn_edit_account_clicked, \
			"btn_remove_account_clicked" : self._on_btn_remove_account_clicked, \
			"treeview_accounts_row_activated" : self._on_treeview_accounts_row_activated, \
			"liststore_accounts_row_deleted" : self._on_liststore_accounts_row_deleted, \
			"liststore_accounts_row_inserted" : self._on_liststore_accounts_row_inserted, \
			"btn_edit_plugin_clicked" : self._on_btn_edit_plugin_clicked, \
			"treeview_plugins_row_activated" : self._on_treeview_plugins_row_activated, \
			"treeview_plugins_cursor_changed" : self._on_treeview_plugins_cursor_changed, \
		})
		
		self._window = builder.get_object("config_window")
		self._window.set_icon_name("mailnag")
		self._window.set_application(app)
		self._cfg = read_cfg()
		
		self._daemon_enabled = False
		
		self._switch_daemon_enabled = builder.get_object("switch_daemon_enabled")
		
		#
		# accounts page
		#
		self._accountman = AccountManager()

		self._treeview_accounts = builder.get_object("treeview_accounts")
		self._liststore_accounts = builder.get_object("liststore_accounts")
		
		self._button_edit_account = builder.get_object("btn_edit_account")
		self._button_remove_account = builder.get_object("btn_remove_account")
		
		self._button_edit_account.set_sensitive(False)
		self._button_remove_account.set_sensitive(False)
		
		renderer_acc_enabled = Gtk.CellRendererToggle()
		renderer_acc_enabled.connect("toggled", self._on_account_toggled)
		column_acc_enabled = Gtk.TreeViewColumn(_('Enabled'), renderer_acc_enabled)
		column_acc_enabled.add_attribute(renderer_acc_enabled, "active", 1)
		column_acc_enabled.set_alignment(0.5)
		self._treeview_accounts.append_column(column_acc_enabled)

		renderer_acc_name = Gtk.CellRendererText()
		column_acc_name = Gtk.TreeViewColumn(_('Name'), renderer_acc_name, text = 2)
		self._treeview_accounts.append_column(column_acc_name)
		
		#
		# plugins page
		#
		self._treeview_plugins = builder.get_object("treeview_plugins")
		self._liststore_plugins = builder.get_object("liststore_plugins")
		
		self._button_edit_plugin = builder.get_object("btn_edit_plugin")
		self._button_edit_plugin.set_sensitive(False)
		
		renderer_plugin_enabled = Gtk.CellRendererToggle()
		renderer_plugin_enabled.connect("toggled", self._on_plugin_toggled)
		column_plugin_enabled = Gtk.TreeViewColumn(_('Enabled'), renderer_plugin_enabled)
		column_plugin_enabled.add_attribute(renderer_plugin_enabled, "active", 1)
		column_plugin_enabled.set_alignment(0.5)
		self._treeview_plugins.append_column(column_plugin_enabled)

		renderer_plugin_name = Gtk.CellRendererText()
		column_plugin_name = Gtk.TreeViewColumn(_('Name'), renderer_plugin_name, markup = 2)
		self._treeview_plugins.append_column(column_plugin_name)
		
		# load config
		self._load_config()
		self._window.show_all()

	
	def get_gtk_window(self):
		return self._window


	def get_daemon_enabled(self):
		return self._daemon_enabled


	def _load_config(self):
		self._switch_daemon_enabled.set_active(bool(int(self._cfg.get('core', 'autostart'))))
		
		self._accountman.load_from_cfg(self._cfg)
		
		# load accounts
		for acc in self._accountman:
			row = [acc, acc.enabled, acc.name]
			self._liststore_accounts.append(row)
		self._select_account_path((0,))
		
		# load plugins
		enabled_lst = self._cfg.get('core', 'enabled_plugins').split(',')
		enabled_lst = [s for s in [s.strip() for s in enabled_lst] if s != '']
		
		plugins = Plugin.load_plugins(self._cfg)
		plugins.sort(key = lambda p : p.get_manifest()[0])
		
		for plugin in plugins:
			name, desc, ver, author = plugin.get_manifest()
			enabled = True if (plugin.get_modname() in enabled_lst) else False
			description = '<b>%s</b> (%s)\n%s' % (name, ver, desc)
			row = [plugin, enabled, description]
			self._liststore_plugins.append(row)
		self._select_plugin_path((0,))
	

	def _save_config(self):
		autostart = self._switch_daemon_enabled.get_active()
		self._cfg.set('core', 'autostart', int(autostart))

		self._accountman.save_to_cfg(self._cfg)
		
		enabled_plugins = ''
		for row in self._liststore_plugins:
			plugin = row[0]
			modname = plugin.get_modname()
			
			if row[1] == True:
				if len(enabled_plugins) > 0:
					enabled_plugins += ', '
				enabled_plugins += modname
			
			config = plugin.get_config()
			if len(config) > 0:
				if not self._cfg.has_section(modname):
					self._cfg.add_section(modname)
				for k, v in config.items():
					self._cfg.set(modname, k, v)
		
		self._cfg.set('core', 'enabled_plugins', enabled_plugins)
		
		write_cfg(self._cfg)

		if autostart: self._create_autostart()
		else: self._delete_autostart()


	def _show_confirmation_dialog(self, text):
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
		# get account object from treeviews 1st column
		if iter != None: acc = model.get_value(iter, 0)
		else: acc = None
		return acc, model, iter
	
	
	def _select_account_path(self, path):
		treeselection = self._treeview_accounts.get_selection()
		treeselection.select_path(path)
		self._treeview_accounts.grab_focus()


	def _edit_account(self):
		acc, model, iter = self._get_selected_account()
		if iter != None:
			d = AccountDialog(self._window, acc)
			
			if d.run() == Gtk.ResponseType.OK:
				model.set_value(iter, 2, acc.name)


	def _get_selected_plugin(self):
		treeselection = self._treeview_plugins.get_selection()
		selection = treeselection.get_selected()
		model, iter = selection
		# get plugin object from treeviews 1st column
		if iter != None: plugin = model.get_value(iter, 0)
		else: plugin = None
		return plugin, model, iter
	
	
	def _select_plugin_path(self, path):
		treeselection = self._treeview_plugins.get_selection()
		treeselection.select_path(path)
		self._treeview_plugins.grab_focus()
	
	
	def _edit_plugin(self):
		plugin, model, iter = self._get_selected_plugin()
		
		if (iter != None) and plugin.has_config_ui():
			d = PluginDialog(self._window, plugin)
			d.run()
	
	
	def _create_autostart(self):
		autostart_folder = os.path.join(bd.xdg_config_home, "autostart")
		src = os.path.join(DESKTOP_FILE_DIR, "mailnag.desktop")
		dst = os.path.join(autostart_folder, "mailnag.desktop")
		
		if not os.path.exists(autostart_folder):
			os.makedirs(autostart_folder)

		try:
			shutil.copyfile(src, dst)
		except Exception as e:
			import logging
			logging.info(f"failed setting autostart: {e}")
			return
		
		# If mailag-config was started from a local directory, 
		# patch the exec path of the autostart .desktop file accordingly.
		if not os.path.isabs(DESKTOP_FILE_DIR):
			exec_file = os.path.join(os.path.abspath(BIN_DIR), "mailnag")
			with open(dst, 'r') as f:
				strn = f.read()
				strn = strn.replace('/usr/bin/mailnag', exec_file)
			with open(dst, 'w') as f:
				f.write(strn)


	def _delete_autostart(self):
		autostart_folder = os.path.join(bd.xdg_config_home, "autostart")
		autostart_file = os.path.join(autostart_folder, "mailnag.desktop")
		if os.path.exists(autostart_file):
			os.remove(autostart_file)

	
	def _on_btn_info_clicked(self, widget):
		aboutdialog = Gtk.AboutDialog()
		aboutdialog.set_title(_("About %s") % PACKAGE_NAME.title())
		aboutdialog.set_version(APP_VERSION)
		aboutdialog.set_program_name(PACKAGE_NAME.title())
		aboutdialog.set_comments(_("An extensible mail notification daemon."))
		aboutdialog.set_copyright(_("Copyright (c) 2011 - 2021 Patrick Ulbrich and contributors."))
		aboutdialog.set_logo_icon_name("mailnag")
		aboutdialog.set_website("https://github.com/pulb/mailnag")
		aboutdialog.set_website_label(_("Homepage"))
		aboutdialog.set_license_type(Gtk.License.GPL_2_0)		
		aboutdialog.set_authors([
			"Patrick Ulbrich (maintainer)",
			"Andreas Angerer",
			"Balló György",
			"Dan Christensen",
			"Denis Anuschewski",
			"Edwin Smulders",
			"Freeroot",
			"James Powell",
			"Leighton Earl",
			"Matthias Mailänder",
			"Oleg",
			"Ralf Hersel",
			"razer",
			"Taylor Braun-Jones",
			"Thomas Haider",
			"Timo Kankare",
			"Vincent Cheng"
		])
		aboutdialog.set_translator_credits(_("translator-credits"))
		aboutdialog.set_artists([ "Reda Lazri" ])
		aboutdialog.connect("response", lambda w, r: aboutdialog.destroy())
		
		aboutdialog.set_modal(True)
		aboutdialog.set_transient_for(self._window)		
		aboutdialog.show()


	def _on_account_toggled(self, cell, path):
		model = self._liststore_accounts
		iter = model.get_iter(path)
		acc = model.get_value(iter, 0)
		acc.enabled = not acc.enabled
		
		self._liststore_accounts.set_value(iter, 1, not cell.get_active())
		

	def _on_btn_add_account_clicked(self, widget):
		acc = Account(enabled = True)
		d = AccountDialog(self._window, acc)
	
		if d.run() == Gtk.ResponseType.OK:
			self._accountman.add(acc)
			
			row = [acc, acc.enabled, acc.name]
			iter = self._liststore_accounts.append(row)
			model = self._treeview_accounts.get_model()
			path = model.get_path(iter)
			self._treeview_accounts.set_cursor(path, None, False)
			self._treeview_accounts.grab_focus()


	def _on_btn_edit_account_clicked(self, widget):
		self._edit_account()


	def _on_btn_remove_account_clicked(self, widget):
		acc, model, iter = self._get_selected_account()
		if iter != None:
			if self._show_confirmation_dialog(_('Delete this account:') + \
				'\n\n' + acc.name):
				
				# select prev/next account
				p = model.get_path(iter)
				if not p.prev():
					p.next()
				self._select_account_path(p)
				
				# remove from treeview
				model.remove(iter)
				# remove from account manager
				self._accountman.remove(acc)


	def _on_treeview_accounts_row_activated(self, treeview, path, view_column):
		self._edit_account()


	def _on_liststore_accounts_row_deleted(self, model, path):
		self._button_edit_account.set_sensitive(len(model) > 0)
		self._button_remove_account.set_sensitive(len(model) > 0)


	def _on_liststore_accounts_row_inserted(self, model, path, user_param):
		self._button_edit_account.set_sensitive(len(model) > 0)
		self._button_remove_account.set_sensitive(len(model) > 0)
		
	
	def _on_plugin_toggled(self, cell, path):
		model = self._liststore_plugins
		iter = model.get_iter(path)
		self._liststore_plugins.set_value(iter, 1, not cell.get_active())
	
	
	def _on_btn_edit_plugin_clicked(self, widget):
		self._edit_plugin()
	
	
	def _on_treeview_plugins_row_activated(self, treeview, path, view_column):
		self._edit_plugin()
	
		
	def _on_treeview_plugins_cursor_changed(self, treeview):
		# Workaround for a bug in GTK < 3.8,
		# see http://permalink.gmane.org/gmane.comp.gnome.svn/694089
		if not self._window.get_visible(): return
		
		plugin, model, iter = self._get_selected_plugin()
		if iter != None:
			self._button_edit_plugin.set_sensitive(plugin.has_config_ui())
	

	def _on_config_window_deleted(self, widget, event):
		self._save_config()	
		self._daemon_enabled = self._switch_daemon_enabled.get_active()



#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# config_window.py
#
# Copyright 2011 Patrick Ulbrich <zulu99@gmx.net>
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

PACKAGE_NAME = "mailnag"

__builtins__.USE_GTK3 = True # make keyring.py use GTK3

import gobject
from gi.repository import GLib, GdkPixbuf, Gtk

import os
import ConfigParser
import locale
import gettext
import xdg.BaseDirectory as bd
from utils import *
from keyring import Keyring
from account_dialog import AccountDialog

locale.bindtextdomain(PACKAGE_NAME, './locale')
gettext.bindtextdomain(PACKAGE_NAME, './locale')
gettext.textdomain(PACKAGE_NAME)
_ = gettext.gettext

#
# Configuration window
#
class ConfigWindow:
	def __init__(self):
		builder = Gtk.Builder()
		builder.set_translation_domain(PACKAGE_NAME)
		builder.add_from_file(get_data_file("config_window.ui"))
		builder.connect_signals({ \
			"config_window_deleted" : self.__on_config_window_deleted, \
			"btn_add_clicked" : self.__on_btn_add_clicked, \
			"btn_edit_clicked" : self.__on_btn_edit_clicked, \
			"btn_remove_clicked" : self.__on_btn_remove_clicked, \
			"treeview_accounts_row_activated" : self.__on_treeview_accounts_row_activated, \
			"liststore_accounts_row_deleted" : self.__on_liststore_accounts_row_deleted, \
			"liststore_accounts_row_inserted" : self.__on_liststore_accounts_row_inserted, \
			"chk_enable_filter_toggled" : self.__on_chk_enable_filter_toggled \
		})

		self.window = builder.get_object("config_window")
		self.window.set_icon(GdkPixbuf.Pixbuf.new_from_file_at_size(get_data_file("mailnag.svg"), 48, 48));
		
		#
		# account tab
		#
		self.accounts = Accounts()

		self.treeview_accounts = builder.get_object("treeview_accounts")
		self.liststore_accounts = builder.get_object("liststore_accounts")

		self.button_edit = builder.get_object("button_edit")
		self.button_remove = builder.get_object("button_remove")

#		colhead = [('Id'), _('Active'), _('Name')]						# column headings
#
#		renderer_id = Gtk.CellRendererText()
#		column_id = Gtk.TreeViewColumn(colhead[0], renderer_id, text=0)	# Account Id

		renderer_on = Gtk.CellRendererToggle()
		renderer_on.connect("toggled", self.__on_account_toggled)		# bind toggle signal
		column_on = Gtk.TreeViewColumn(_('Enabled'), renderer_on)		# Account On/Off
		column_on.add_attribute(renderer_on, "active", 1)
		column_on.set_alignment(0.5)									# center column heading
		self.treeview_accounts.append_column(column_on)

		renderer_name = Gtk.CellRendererText()
		column_name = Gtk.TreeViewColumn(_('Name'), renderer_name, text=2)	# Account Name
		self.treeview_accounts.append_column(column_name)

		#
		# general tab
		#
		self.entry_mail_client = builder.get_object("entry_mail_client")
		self.entry_label = builder.get_object("entry_label")	
		self.spinbutton_interval = builder.get_object("spinbutton_interval")
		self.chk_playsound = builder.get_object("chk_playsound")
		self.chk_autostart = builder.get_object("chk_autostart")
		
		#
		# spam filter tab
		self.chk_enable_filter = builder.get_object("chk_enable_filter")
		self.textview_filter = builder.get_object("textview_filter")	
		self.textbuffer_filter = builder.get_object("textbuffer_filter")	

		#
		# events tab
		# TODO

		# about tab
		self.image_logo = builder.get_object("image_logo")
		pb = GdkPixbuf.Pixbuf.new_from_file_at_size(get_data_file("mailnag.svg"), 200, 200)
		self.image_logo.set_from_pixbuf(pb)

		self.load_config()
		self.window.show()


	def load_config(self):
		self.entry_mail_client.set_text(cfg.get('general', 'mail_client'))
		self.entry_label.set_text(cfg.get('general', 'messagetray_label'))
		self.spinbutton_interval.set_value(int(cfg.get('general', 'check_interval')))
		self.chk_playsound.set_active(int(cfg.get('general', 'playsound')))
		self.chk_autostart.set_active(int(cfg.get('general', 'autostart')))

		
		self.chk_enable_filter.set_active(int(cfg.get('filter', 'filter_on')))
		self.textbuffer_filter.set_text(cfg.get('filter', 'filter_text'))

		self.accounts.load()

		for acc in self.accounts.account:								# load accounts into treeview
			row = acc.get_row()
			self.liststore_accounts.append(row)
		self.select_path((0,))		
		

	def save_config(self):
		cfg.set('general', 'mail_client', self.entry_mail_client.get_text())
		cfg.set('general', 'messagetray_label', self.entry_label.get_text())
		cfg.set('general', 'check_interval', int(self.spinbutton_interval.get_value()))
		cfg.set('general', 'playsound',int(self.chk_playsound.get_active()))
		autostart = self.chk_autostart.get_active()
		cfg.set('general', 'autostart', int(autostart))

		cfg.set('filter', 'filter_on', int(self.chk_enable_filter.get_active()))
		start, end = self.textbuffer_filter.get_bounds()		
		cfg.set('filter', 'filter_text', self.textbuffer_filter.get_text(start, end, True))	
		
		on, name, server, user, password, imap, folder, port = self.accounts.get_cfg()
		cfg.set('account', 'on', on)
		cfg.set('account', 'name', name)
		cfg.set('account', 'server', server)
		cfg.set('account', 'user', user)
		cfg.set('account', 'imap', imap)
		cfg.set('account', 'folder', folder)
		cfg.set('account', 'port', port)

		for acc in self.accounts.account:
			if bool(acc.imap): protocol = 'imap'
			else: protocol = 'pop'
			keyring.set(protocol, acc.user, acc.server, acc.password)
		
		cfg_file = os.path.join(cfg_folder, "mailnag.cfg")
		with open(cfg_file, 'wb') as configfile: cfg.write(configfile)

		if autostart: create_autostart()
		else: delete_autostart()


	def show_yesno_dialog(self, text):									# Show YesNo Dialog
		message = Gtk.MessageDialog(self.window, Gtk.DialogFlags.MODAL, \
			Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, text)
		resp = message.run()											# show dialog window
		message.destroy()												# close dialog
		if resp == Gtk.ResponseType.YES: return True					# if YES clicked
		else: return False												# if NO clicked
	
	
	def get_selected_account(self):										# return selected row
		treeselection = self.treeview_accounts.get_selection()			# get tree_selection object
		selection = treeselection.get_selected()						# get selected tupel (model, iter)
		model, iter = selection											# get selected iter
		if iter != None: id = model.get_value(iter, 0)					# get account_id from treeviews 1. column
		else: id = None
		return id, model, iter
	
	
	def select_path(self, path):										# select path in treeview
		treeselection = self.treeview_accounts.get_selection()			# get tree selection object
		treeselection.select_path(path)									# select path
		self.treeview_accounts.grab_focus()								# put focus on treeview


	def edit_account(self):
		id, model, iter = self.get_selected_account()
		if iter != None:
			acc = self.accounts.get(id)
			d = AccountDialog(self.window)
			
			d.entry_account_name.set_text(acc.name)
			d.entry_account_user.set_text(acc.user)
			d.entry_account_password.set_text(acc.password)
			d.entry_account_server.set_text(acc.server)
			d.entry_account_port.set_text(acc.port)
			d.chk_account_imap.set_active(acc.imap)
			d.entry_account_folder.set_text(acc.folder)
			
			res = d.run()
			
			if res == 1:
				acc.name = d.entry_account_name.get_text()
				acc.user = d.entry_account_user.get_text()
				acc.password = d.entry_account_password.get_text()
				acc.server = d.entry_account_server.get_text()
				acc.port = d.entry_account_port.get_text()
				acc.imap = d.chk_account_imap.get_active()
				acc.folder = d.entry_account_folder.get_text()
			
				model.set_value(iter, 2, acc.name)
			
			d.destroy()


	def __on_account_toggled(self, cell, path):							# chk_box account_on toggled
		model = self.liststore_accounts
		iter = model.get_iter(path)
		id = model.get_value(iter, 0)
		acc = self.accounts.get(id)										# get account by id
		acc.on = not acc.on												# update account.on
		
		self.liststore_accounts.set_value(iter, 1, not cell.get_active())


	def __on_btn_add_clicked(self, widget):
		d = AccountDialog(self.window)
		res = d.run()

		if res == 1:
			id = self.accounts.add(1, d.entry_account_name.get_text(),
			d.entry_account_server.get_text(), d.entry_account_user.get_text(),
			d.entry_account_password.get_text(), d.chk_account_imap.get_active(), 
			d.entry_account_folder.get_text(), d.entry_account_port.get_text()
			)
			
			row = [id, 1, d.entry_account_name.get_text()]
			iter = self.liststore_accounts.append(row)
			model = self.treeview_accounts.get_model()
			path = model.get_path(iter)
			self.treeview_accounts.set_cursor(path, None, False)
			self.treeview_accounts.grab_focus()

		d.destroy()


	def __on_btn_edit_clicked(self, widget):
		self.edit_account()


	def __on_btn_remove_clicked(self, widget):
		id, model, iter = self.get_selected_account()
		if iter != None:
			name = model.get_value(iter, 2)								# get account_name
			if self.show_yesno_dialog(_('Delete this account:') + \
				'\n\n' + name):
				
				p = model.get_path(iter)
				if not p.prev():
					p.next()
				self.select_path(p)										# select prev/next account
				
				model.remove(iter)										# delete in treeview
				self.accounts.remove(id)								# delete in accounts list


	def __on_treeview_accounts_row_activated(self, treeview, path, view_column):
		self.edit_account()


	def __on_liststore_accounts_row_deleted(self, model, path):
		self.button_edit.set_sensitive(len(model) > 0)
		self.button_remove.set_sensitive(len(model) > 0)


	def __on_liststore_accounts_row_inserted(self, model, path, user_param):
		self.button_edit.set_sensitive(len(model) > 0)
		self.button_remove.set_sensitive(len(model) > 0)


	def __on_chk_enable_filter_toggled(self, widget):
		self.textview_filter.set_sensitive(self.chk_enable_filter.get_active())


	def __save_and_quit(self):
		self.save_config()
		keyring.remove(self.accounts.account)							# delete obsolete entries from Keyring	
		Gtk.main_quit()
		

	def __on_config_window_deleted(self, widget, event):
		self.__save_and_quit()


#
# Accounts
#
class Account:
	def __init__(self, on, name, server, user, password, imap, folder, port):
		self.id = str(id(self))											# unique identifier
		self.on = on													# int
		self.name = name
		self.server = server
		self.user = user
		self.password = password
		self.imap = imap												# int
		self.folder = folder
		self.port = port


	def get_row(self):
		return [self.id, self.on, self.name]


class Accounts:
	def __init__(self):
		self.account = []
		self.current = None												# currently selected account_id


	def add(self, on = 0, name = _('Unnamed'), server = '', user= '' , \
		password = '', imap = 0, folder = '', port = ''):				# add one new account
		self.account.append(Account(on, name, server, user, \
			password, imap, folder, port))
		this_account = self.account[-1]									# get last element of the list
		id = this_account.id
		return id


	def remove(self, id):												# delete account by id
		for acc in self.account[:]:										# iterate copy of account list
			if acc.id == id:											# find matching account
				self.account.remove(acc)								# delete it
				break													# stop iteration


	def load(self):
		self.account = []												# empty account list

		on = cfg.get('account', 'on')
		name = cfg.get('account', 'name')
		server = cfg.get('account', 'server')
		user = cfg.get('account', 'user')
		imap = cfg.get('account', 'imap')
		folder = cfg.get('account', 'folder')
		port = cfg.get('account', 'port')

		separator = '|'
		on_list = on.split(separator)
		name_list = name.split(separator)
		server_list = server.split(separator)
		user_list = user.split(separator)
		imap_list = imap.split(separator)
		folder_list = folder.split(separator)
		port_list = port.split(separator)
		
		for i in range(len(name_list)):									# iterate 0 to nr of elements in name_list
			name = name_list[i]
			if name == '': continue			
			on = int(on_list[i])			
			server = server_list[i]
			user = user_list[i]
			imap = int(imap_list[i])
			folder = folder_list[i]
			port = port_list[i]
			if imap: protocol = 'imap'
			else: protocol = 'pop'
			password = keyring.get(protocol, user, server)
			self.add(on, name, server, user, password, imap, folder, port)	# fill Account list


	def get(self, id):													# return all data of one account
		self.current = id
		for acc in self.account:
			if acc.id == id:
				return acc
		return None


	def get_current(self):												# return current account
		if self.current != None:
			for acc in self.account:
				if acc.id == self.current:
					return acc
		return None


	def get_cfg(self):													# return arrays of account strings for cfg
		separator = '|'

		on_list = []
		name_list = []
		server_list = []
		user_list = []
		password_list = []
		imap_list = []
		folder_list = []
		port_list = []

		for acc in self.account:										# collect all values
			on_list.append(str(int(acc.on)))
			name_list.append(acc.name)
			server_list.append(acc.server)
			user_list.append(acc.user)
			password_list.append(acc.password)
			imap_list.append(str(int(acc.imap)))
			folder_list.append(acc.folder)
			port_list.append(acc.port)

		cfg_on = separator.join(on_list)								# concatenate values
		cfg_name = separator.join(name_list)
		cfg_server = separator.join(server_list)
		cfg_user = separator.join(user_list)
		cfg_imap = separator.join(imap_list)
		cfg_folder = separator.join(folder_list)
		cfg_port = separator.join(port_list)

		return cfg_on, cfg_name, cfg_server, cfg_user, password_list, cfg_imap, cfg_folder, cfg_port


	def ok(self, window):												# check if name, server, user, password are not empty
		nok = []														# list of not-ok accounts
		for acc in self.account:
			if acc.name == '' or \
			acc.server == '' or \
			acc.user == '' or \
			acc.password == '':
				nok.append(acc.name)
		if len(nok) > 0:
			message_text = _("Missing data in account(s):") + "\n\n"
			for acc_name in nok:
				message_text += acc_name + '\n'
			message_text += "\n" + _("Please correct this first.")
			window.show_message(message_text)
			return False, nok
		else:
			return True, True


#
# Misc
#
def read_config():														# read config file or create it
	cfg = ConfigParser.RawConfigParser()
	cfg_file = cfg_file = os.path.join(cfg_folder, "mailnag.cfg")
	if not os.path.exists(cfg_file):									# create a fresh config file
		print _("Config file does not exist, creating new one")
		cfg = set_default_config(cfg)									# write default values to cfg
		with open(cfg_file, 'wb') as configfile: cfg.write(configfile)

	cfg.read(cfg_file)
	return cfg


def set_default_config(cfg):
	try: cfg.add_section('general')
	except ConfigParser.DuplicateSectionError: pass
	cfg.set('general', 'mail_client', "evolution")
	cfg.set('general', 'messagetray_label', "mailnag")
	cfg.set('general', 'check_interval', 5)
	cfg.set('general', 'show_only_new', 0)
	cfg.set('general', 'remember', 1)
	cfg.set('general', 'check_once', 0)
	cfg.set('general', 'sender_format', 1)
	cfg.set('general', 'playsound', 1)
	cfg.set('general', 'soundfile', 'mailnag.wav')
	cfg.set('general', 'autostart', 1)

	try: cfg.add_section('filter')
	except ConfigParser.DuplicateSectionError: pass
	cfg.set('filter', 'filter_on', 0)	
	cfg.set('filter', 'filter_text', 'newsletter, viagra')

	try: cfg.add_section('script')
	except ConfigParser.DuplicateSectionError: pass
	cfg.set('script', 'script0_on', 0)
	cfg.set('script', 'script1_on', 0)
	cfg.set('script', 'script2_on', 0)
	cfg.set('script', 'script3_on', 0)
	cfg.set('script', 'script4_on', 0)
	cfg.set('script', 'script5_on', 0)
	cfg.set('script', 'script0_file', '')
	cfg.set('script', 'script1_file', '')
	cfg.set('script', 'script2_file', '')
	cfg.set('script', 'script3_file', '')
	cfg.set('script', 'script4_file', '')
	cfg.set('script', 'script5_file', '')

	try: cfg.add_section('account')
	except ConfigParser.DuplicateSectionError: pass
	cfg.set('account', 'on', '')
	cfg.set('account', 'name', '')
	cfg.set('account', 'server', '')
	cfg.set('account', 'user', '')
	cfg.set('account', 'imap', '')
	cfg.set('account', 'folder', '')
	cfg.set('account', 'port', '')

	return cfg		


def create_autostart():
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
	"Comment=Email notifier for GNOME 3"

	autostart_folder = "%s/.config/autostart/" % (os.path.expanduser("~/"))
	if not os.path.exists(autostart_folder):
		os.popen("mkdir -p " + autostart_folder)
	autostart_file = autostart_folder + "mailnag.desktop"
	f = open(autostart_file, 'w')
	f.write(content)													# create it
	f.close()


def delete_autostart():
	autostart_folder = "%s/.config/autostart/" % (os.path.expanduser("~/"))
	autostart_file = autostart_folder + "mailnag.desktop"
	if os.path.exists(autostart_file):
		os.popen("rm " + autostart_file)								# delete it


#
# Entry point
#
def main():
	global cfg, cfg_folder, keyring

	set_procname("mailnag_config")

	cfg_folder = os.path.join(bd.xdg_config_home, "mailnag")
	if not os.path.exists(cfg_folder):
		os.popen("mkdir -p " + cfg_folder)

	cfg = read_config()													# get configurations
	keyring = Keyring()

	confwin = ConfigWindow()

	Gtk.main()															# start main loop


if __name__ == "__main__":  main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mailnag_config.py
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

import gtk
import os
import subprocess
import ConfigParser
import poplib
import imaplib
import locale
import gettext
import gnomekeyring
import glib
import cairo

# Settings =============================================================

class Settings:
	def __init__(self):
		builder = gtk.Builder()											# build GUI from Glade file
		builder.set_translation_domain('mailnag_config')
		builder.add_from_file("mailnag_config.glade")
		builder.connect_signals({ \
		"gtk_main_quit" : self.exit, \
		"on_button_restore_clicked" : self.restore, \
		"on_button_cancel_clicked" : self.cancel, \
		"on_button_exit_clicked" : self.exit, \
		"on_button_test_clicked" : self.test, \
		"on_entry_account_frequency_focus_out_event" : self.plausibility, \
		"on_entry_numberofentries_focus_out_event" : self.plausibility, \
		"on_entry_headline_focus_out_event" : self.plausibility, \
		"on_entry_notify_text_multi_focus_out_event" : self.plausibility, \
		"on_entry_soundfile_focus_out_event" : self.plausibility, \
		"on_button_select_soundfile_clicked" : self.select_soundfile, \
		"on_button_test_sound_clicked" : self.play_sound, \
		"on_entry_subject_length_focus_out_event" : self.plausibility, \
		"on_select_script0_clicked" : self.select_script, \
		"on_select_script1_clicked" : self.select_script, \
		"on_select_script2_clicked" : self.select_script, \
		"on_select_script3_clicked" : self.select_script, \
		"on_select_script4_clicked" : self.select_script, \
		"on_select_script5_clicked" : self.select_script, \
		"on_treeview_account_cursor_changed" : self.account_changed, \
		"on_entry_account_name_changed" : self.account_field_changed, \
		"on_entry_account_server_changed" : self.account_field_changed, \
		"on_entry_account_user_changed" : self.account_field_changed, \
		"on_entry_account_password_changed" : self.account_field_changed, \
		"on_chk_account_imap_toggled" : self.account_field_changed, \
		"on_entry_account_folder_changed" : self.account_field_changed, \
		"on_entry_account_port_changed" : self.account_field_changed, \
		"on_button_account_import_clicked" : self.show_imported_accounts, \
		"on_button_account_add_clicked" : self.add_account, \
		"on_button_account_del_clicked" : self.del_account, \
		"on_button_dd_preview_clicked" : self.preview_dd})

		self.window = builder.get_object("config_window")

		self.autostart = builder.get_object("chk_autostart")			# get the widgets
		self.version = builder.get_object("label_version_nr")
		self.headline = builder.get_object("entry_headline")

		# === Accounts =================================================
		self.accounts = Accounts()

		self.treeview_account = builder.get_object("treeview_account")
		self.liststore_account = builder.get_object("liststore_account")

		colhead = [('Id'), _('On'), _('Name')]							# column headings

		renderer_id = gtk.CellRendererText()
		column_id = gtk.TreeViewColumn(colhead[0], renderer_id, text=0)	# Account Id

		renderer_on = gtk.CellRendererToggle()
		renderer_on.set_property('activatable', True)					# make cell activatable
		renderer_on.connect("toggled", self.account_on_toggled)			# bind toggle signal
		column_on = gtk.TreeViewColumn(colhead[1], renderer_on)			# Account On/Off
		column_on.add_attribute(renderer_on, "active", 1)
		column_on.set_alignment(0.5)									# center column heading
		self.treeview_account.append_column(column_on)

		renderer_name = gtk.CellRendererText()
		column_name = gtk.TreeViewColumn(colhead[2], renderer_name, text=2)	# Account Name
		self.treeview_account.append_column(column_name)

		self.account_id = builder.get_object("entry_account_id")
		self.account_name = builder.get_object("entry_account_name")
		self.account_server = builder.get_object("entry_account_server")
		self.account_user = builder.get_object("entry_account_user")
		self.account_password = builder.get_object("entry_account_password")
		self.account_imap = builder.get_object("chk_account_imap")
		self.account_folder = builder.get_object("entry_account_folder")
		self.account_port = builder.get_object("entry_account_port")

		self.frequency = builder.get_object("entry_account_frequency")
		self.check_once = builder.get_object("chk_account_check_only_once")

		# === Indicate =================================================
		self.show_sender = builder.get_object("chk_showsender")
		self.sender_radio = builder.get_object("radio_sender_name")		# get the first radio button
		self.sender_format_radio_group = self.sender_radio.get_group()	# get the radio button group in a list
		self.message_radio = builder.get_object("radio_subject_sender")
		self.message_format_radio_group = self.message_radio.get_group()
		self.sort_radio = builder.get_object("radio_sort_date")
		self.sort_radio_group = self.sort_radio.get_group()

		self.show_subject = builder.get_object("chk_showsubject")
		self.show_provider = builder.get_object("chk_showprovider")
		self.subject_length = builder.get_object("entry_subject_length")
		self.remember = builder.get_object("chk_remember")
		self.start_on_click = builder.get_object("entry_startonclick")
		self.clear_on_click = builder.get_object("chk_clear_on_click")
		self.show_only_new = builder.get_object("chk_show_only_new")
		self.remove_single_email = builder.get_object("chk_remove_single_email")

		self.show_menu_1 = builder.get_object("chk_menu_1")
		self.show_menu_2 = builder.get_object("chk_menu_2")
		self.show_menu_3 = builder.get_object("chk_menu_3")
		self.name_menu_1 = builder.get_object("entry_menu_text_1")
		self.name_menu_2 = builder.get_object("entry_menu_text_2")
		self.name_menu_3 = builder.get_object("entry_menu_text_3")
		self.cmd_menu_1 = builder.get_object("entry_menu_cmd_1")
		self.cmd_menu_2 = builder.get_object("entry_menu_cmd_2")
		self.cmd_menu_3 = builder.get_object("entry_menu_cmd_3")

		# === Notify ===================================================
		self.notify = builder.get_object("chk_notify")
		self.notify_text_one = builder.get_object("entry_notify_text_one")
		self.notify_text_multi = builder.get_object("entry_notify_text_multi")
		self.playsound = builder.get_object("chk_playsound")
		self.soundfile = builder.get_object("entry_soundfile")
		self.speak = builder.get_object("chk_speak")

		self.script0_on = builder.get_object("chk_script0")
		self.script1_on = builder.get_object("chk_script1")
		self.script2_on = builder.get_object("chk_script2")
		self.script3_on = builder.get_object("chk_script3")
		self.script4_on = builder.get_object("chk_script4")
		self.script5_on = builder.get_object("chk_script5")
		self.script0_file = builder.get_object("entry_script0")
		self.script1_file = builder.get_object("entry_script1")
		self.script2_file = builder.get_object("entry_script2")
		self.script3_file = builder.get_object("entry_script3")
		self.script4_file = builder.get_object("entry_script4")
		self.script5_file = builder.get_object("entry_script5")

		# === Desktop Display ==========================================
		self.dd_on = builder.get_object("chk_dd_on")
		self.dd_pos_x = builder.get_object("entry_dd_pos_x")
		self.dd_pox_y = builder.get_object("entry_dd_pos_y")
		self.dd_width = builder.get_object("entry_dd_width")
		self.dd_height = builder.get_object("entry_dd_height")
		self.dd_bg_color = builder.get_object("button_dd_bg_color")
		self.dd_transparency = builder.get_object("entry_dd_transparency")
		self.dd_text_color = builder.get_object("button_dd_text_color")
		self.dd_font = builder.get_object("button_dd_font")
		self.dd_font.set_use_font(True)
		self.desktop_display = None										# the Window object for Desktop_Display
		self.dd_click_close = builder.get_object("chk_dd_click_close")
		self.dd_click_launch = builder.get_object("chk_dd_click_launch")

		# === Filter ===================================================
		self.filter_on = builder.get_object("chk_filter")
		self.filter_text = builder.get_object("textbuffer_filter")

		self.load()														# load config values into widgets

		# === Test =====================================================
		self.test = builder.get_object("textbuffer_testresult")

		self.help = builder.get_object("textbuffer_help")				# load help text
		lang = locale.getdefaultlocale()[0].lower()						# get language from operating system
#		if 'de' in lang:
#			f = open('mailnag_help_de.txt', 'r')							# get german help
#		else:
#			f = open('mailnag_help_en.txt', 'r')							# get english help for all other languages
#		self.help.set_text(f.read())
#		f.close()


	def load(self):														# set values to widgets from config
		self.autostart.set_active(int(cfg.get('general','autostart')))
		self.version.set_text(cfg.get('general','version'))
		version = self.version.get_text()

		if version == '0.27':											# check for version - 1 of config file
			print "Found version", version, "updated to new version", VERSION
			self.accounts.load()
		elif version != '0.28':											# check for old version of config file
			print "Found old version", version, "applying default settings"
			set_default_config(cfg)										# write default values to cfg
		else:															# correct current version
			self.accounts.load()

		self.version.set_text(VERSION)									# set to latest version

		for acc in self.accounts.account:								# load accounts into treeview
			row = acc.get_row()
			self.liststore_account.append(row)
		self.select_path((0,))											# select first line

		self.frequency.set_text(cfg.get('account','frequency'))
		self.check_once.set_active(int(cfg.get('account','check_once')))

		self.headline.set_text(cfg.get('indicate','headline'))
		self.show_sender.set_active(int(cfg.get('indicate','show_sender')))

		sender_format = cfg.get('indicate','sender_format')						# index of the radio button group
		self.sender_format_radio_group[int(sender_format)].set_active(True)		# switch-on the radio button
		message_format = cfg.get('indicate','message_format')
		self.message_format_radio_group[int(message_format)].set_active(True)
		sort_by = cfg.get('indicate','sort_by')
		self.sort_radio_group[int(sort_by)].set_active(True)

		self.show_subject.set_active(int(cfg.get('indicate','show_subject')))
		self.show_provider.set_active(int(cfg.get('indicate','show_provider')))
		self.subject_length.set_text(cfg.get('indicate','subject_length'))
		self.remember.set_active(int(cfg.get('indicate','remember')))
		self.start_on_click.set_text(cfg.get('indicate','start_on_click'))
		self.clear_on_click.set_active(int(cfg.get('indicate','clear_on_click')))
		self.show_only_new.set_active(int(cfg.get('indicate','show_only_new')))
		self.remove_single_email.set_active(int(cfg.get('indicate','remove_single_email')))

		for i in ('1','2','3'):
			getattr(self, 'show_menu_' + i).set_active(int(cfg.get('indicate','show_menu_' + i)))
			getattr(self, 'name_menu_' + i).set_text(cfg.get('indicate','name_menu_' + i))
			getattr(self, 'cmd_menu_' + i).set_text(cfg.get('indicate','cmd_menu_' + i))

		self.notify.set_active(int(cfg.get('notify','notify')))
		self.notify_text_one.set_text(cfg.get('notify','text_one'))
		self.notify_text_multi.set_text(cfg.get('notify','text_multi'))
		self.playsound.set_active(int(cfg.get('notify','playsound')))
		self.soundfile.set_text(cfg.get('notify','soundfile'))
		self.speak.set_active(int(cfg.get('notify','speak')))

		self.dd_on.set_active(int(cfg.get('dd','on')))
		self.dd_pos_x.set_text(cfg.get('dd','pos_x'))
		self.dd_pox_y.set_text(cfg.get('dd','pos_y'))
		self.dd_width.set_text(cfg.get('dd','width'))
		self.dd_height.set_text(cfg.get('dd','height'))
		self.dd_bg_color.set_color(gtk.gdk.Color(cfg.get('dd','bg_color')))
		self.dd_transparency.set_value(int(cfg.get('dd','transparency')))
		self.dd_text_color.set_color(gtk.gdk.Color(cfg.get('dd','text_color')))
		self.dd_font.set_font_name(cfg.get('dd','font_name'))
		self.dd_click_close.set_active(int(cfg.get('dd','click_close')))
		self.dd_click_launch.set_active(int(cfg.get('dd','click_launch')))

		for i in ('0','1','2','3','4','5'):
			getattr(self, 'script' + i + '_on').set_active(int(cfg.get('script','script' + i + '_on')))
			getattr(self, 'script' + i + '_file').set_text(cfg.get('script','script' + i + '_file'))

		self.filter_on.set_active(int(cfg.get('filter','filter_on')))
		self.filter_text.set_text(cfg.get('filter','filter_text'))

		self.window.show()


	def restore(self, widget):											# restore to lasted saved settings
		self.liststore_account.clear()									# empty account list model
		self.load()														# reload from config file


	def cancel(self, widget):											# exit program without doing anything else
		exit(1)															# exit code used in mailnag_config.sh


	def exit(self, widget):												# save and exit
		autostart = int(self.autostart.get_active())
		cfg.set('general', 'autostart', autostart)
		cfg.set('general', 'version', VERSION)

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

		cfg.set('account', 'frequency', self.frequency.get_text())
		cfg.set('account', 'check_once', int(self.check_once.get_active()))

		cfg.set('indicate', 'headline', self.headline.get_text())
		cfg.set('indicate', 'show_sender', int(self.show_sender.get_active()))

		sender_format = [self.sender_format_radio_group.index(radio) \
			for radio in self.sender_format_radio_group if radio.get_active()][0]
		cfg.set('indicate', 'sender_format', sender_format)
		message_format = [self.message_format_radio_group.index(radio) \
			for radio in self.message_format_radio_group if radio.get_active()][0]
		cfg.set('indicate', 'message_format', message_format)
		sort_by = [self.sort_radio_group.index(radio) \
			for radio in self.sort_radio_group if radio.get_active()][0]
		cfg.set('indicate', 'sort_by', sort_by)

		cfg.set('indicate', 'show_subject', int(self.show_subject.get_active()))
		cfg.set('indicate', 'show_provider', int(self.show_provider.get_active()))
		cfg.set('indicate', 'subject_length', self.subject_length.get_text())
		cfg.set('indicate', 'remember', int(self.remember.get_active()))
		cfg.set('indicate', 'start_on_click', self.start_on_click.get_text())
		cfg.set('indicate', 'clear_on_click', int(self.clear_on_click.get_active()))
		cfg.set('indicate', 'show_only_new', int(self.show_only_new.get_active()))
		cfg.set('indicate', 'remove_single_email', int(self.remove_single_email.get_active()))

		for i in ('1','2','3'):
			cfg.set('indicate', 'show_menu_' + i, int(getattr(self, 'show_menu_' + i).get_active()))
			cfg.set('indicate', 'name_menu_' + i, getattr(self, 'name_menu_' + i).get_text())
			cfg.set('indicate', 'cmd_menu_' + i, getattr(self, 'cmd_menu_' + i).get_text())

		cfg.set('dd', 'on', int(self.dd_on.get_active()))
		cfg.set('dd', 'pos_x', self.dd_pos_x.get_text())
		cfg.set('dd', 'pos_y', self.dd_pox_y.get_text())
		cfg.set('dd', 'width', self.dd_width.get_text())
		cfg.set('dd', 'height', self.dd_height.get_text())
		cfg.set('dd', 'bg_color', self.dd_bg_color.get_color())
		cfg.set('dd', 'transparency', int(self.dd_transparency.get_value()))
		cfg.set('dd', 'text_color', self.dd_text_color.get_color())
		cfg.set('dd', 'font_name', self.dd_font.get_font_name())
		cfg.set('dd', 'click_close', int(self.dd_click_close.get_active()))
		cfg.set('dd', 'click_launch', int(self.dd_click_launch.get_active()))

		cfg.set('notify', 'notify', int(self.notify.get_active()))
		cfg.set('notify', 'text_one', self.notify_text_one.get_text())
		cfg.set('notify', 'text_multi', self.notify_text_multi.get_text())
		cfg.set('notify', 'playsound', int(self.playsound.get_active()))
		cfg.set('notify', 'soundfile', self.soundfile.get_text())
		cfg.set('notify', 'speak', int(self.speak.get_active()))

		for i in ('0','1','2','3','4','5'):
			cfg.set('script', 'script' + i + '_on', int(getattr(self, 'script' + i + '_on').get_active()))
			cfg.set('script', 'script' + i + '_file', getattr(self, 'script' + i + '_file').get_text())

		cfg.set('filter', 'filter_on', int(self.filter_on.get_active()))
		start, end = self.filter_text.get_bounds()
		cfg.set('filter', 'filter_text', self.filter_text.get_text(start, end))

		cfg_file = user_folder + ".mailnag/mailnag.cfg"					# folder: /home/user/.mailnag/mailnag.cfg
		with open(cfg_file, 'wb') as configfile: cfg.write(configfile)

		headline = self.headline.get_text()								# always write headline..
		update_desktop_file(headline)									# ..to mailnag.desktop

		if autostart == 1: create_autostart()							# write autostart
		else: delete_autostart()

		if self.accounts.ok(self)[0] \
		and self.menu_entries_ok() \
		and self.scripts_ok() \
		and self.filter_ok():											# do final consistency checks ..
			keyring.remove(self.accounts.account)						# delete obsolete entries from Keyring
			gtk.main_quit()												# .. before app is closed


	def test(self, widget):												# test account connectivity
		if self.accounts.ok(self):
			self.test.delete(self.test.get_start_iter(), self.test.get_end_iter())
			for acc in self.accounts.account:
				if bool(acc.on):
					self.test.insert_at_cursor('\n')
					self.test.insert_at_cursor(_('Testing account ' + acc.name + '\n'))
					if bool(acc.imap):									# IMAP
						try:
							if acc.port == '':
								try: srv = imaplib.IMAP4_SSL(acc.server)	# connect to Email-Server via SSL
								except: srv = imaplib.IMAP4(acc.server)		# non SSL
							else:
								try: srv = imaplib.IMAP4_SSL(acc.server, acc.port)
								except: srv = imaplib.IMAP4(acc.server, acc.port)

							response = srv.login(acc.user, acc.password)
							response_text = response[0] + ', ' + response[1][0] + '\n'
							self.test.insert_at_cursor(response_text)

							typ, mailboxes = srv.list()					# get folder list from server
							response_text = 'Folder:\n'
							for box in mailboxes:
								boxname = box.split()[-1]				# last element from list
								response_text += boxname + '\n'
							self.test.insert_at_cursor(response_text)	# show list of mailboxes

							folder_list = acc.folder.split(',')			# make a list of folders
							if folder_list[0] == '':
								response = srv.select()
								response_text = response[0] + ', ' + response[1][0] + ' messages'
								self.test.insert_at_cursor(response_text)	# number of mails in INBOX
							else:
								for folder in folder_list:
									response = srv.select(folder.strip())
									response_text = response[0] + ', ' + response[1][0]
									self.test.insert_at_cursor(response_text)	# number of mails in folders
							srv.close()
							srv.logout()
						except:
							self.test.insert_at_cursor(_("Test failed. " \
								"Could not connect to %s.\n" % acc.server))
					else:												# POP
						try:
							if acc.port == '':
								try: srv = poplib.POP3_SSL(acc.server)	# connect to Email-Server via SSL
								except: srv = poplib.POP3(acc.server)	# non SSL
							else:
								try: srv = poplib.POP3_SSL(acc.server, acc.port)
								except: srv = poplib.POP3(acc.server, acc.port)

							self.test.insert_at_cursor(srv.getwelcome() + '\n')
							self.test.insert_at_cursor(srv.user(acc.user) + '\n')
							self.test.insert_at_cursor(srv.pass_(acc.password) + '\n')
							srv.quit()									# disconnect from Email-Server
						except:
							self.test.insert_at_cursor(_("Test failed. " \
								"Could not connect to %s.\n" % acc.server))
			return True
		else:
			return False


	def plausibility(self, widget, event):
		name = gtk.Buildable.get_name(widget)
		text = widget.get_text()
		if name == 'entry_account_frequency':
			if text.isdigit():
				text = int(text)
				if text < 1 or text > 1440:								# between 1 Minute and 24 Hours
					self.show_message(_('Value: ' + str(text) + \
					' is not allowed.\nIt must be between 1 and 1440\nReset to last value.'))
					self.frequency.set_text(cfg.get('account','frequency'))
			else:
				self.show_message(_('Value: "' + text + '" must be a number.\nReset to last value.'))
				self.frequency.set_text(cfg.get('account','frequency'))
		elif name == 'entry_numberofentries':
			if text.isdigit():
				text = int(text)
				if text < 0 or text > 99:								# between 0 and 99 entries
					self.show_message(_('Value: ' + str(text) + \
					' is not allowed.\nIt must be between 0 and 99\nReset to last value.'))
					self.number_of_entries.set_text(cfg.get('indicate','number'))
			else:
				self.show_message(_('Value: "' + text + '" must be a number.\nReset to last value.'))
				self.number_of_entries.set_text(cfg.get('indicate','number'))
		elif name == 'entry_headline':
			if text == '':
				self.show_message(_('This field must not be empty.\nReset to last value.'))
				self.headline.set_text(cfg.get('indicate','headline'))
		elif name == 'entry_soundfile':
			if text == '':
				self.show_message(_('This field must not be empty.\nReset to last value.'))
				self.soundfile.set_text(cfg.get('notify','soundfile'))
		elif name == 'entry_notify_text_multi':
			if '%s' not in text:
				self.show_message(_('This field must contain %s\nReset to last value.'))
				self.notify_text_multi.set_text(cfg.get('notify','text_multi'))
		elif name == 'entry_subject_length':
			if text.isdigit():
				text = int(text)
				if text < 10 or text > 999:								# between 10 and 999 characters
					self.show_message(_('Value: ' + str(text) + \
					' is not allowed.\nIt must be between 10 and 999\nReset to last value.'))
					self.subject_length.set_text(cfg.get('indicate','subject_length'))


	def menu_entries_ok(self):
		status = True
		if self.show_menu_1.get_active() \
		and (self.name_menu_1.get_text() == '' \
		or self.cmd_menu_1.get_text() == ''):
			status = False
		if self.show_menu_2.get_active() \
		and (self.name_menu_2.get_text() == '' \
		or self.cmd_menu_2.get_text() == ''):
			status = False
		if self.show_menu_3.get_active() \
		and (self.name_menu_3.get_text() == '' \
		or self.cmd_menu_3.get_text() == ''):
			status = False
		if status == False:
			self.show_message(_("Inconsistent menu entry on 'Indicator' tab.\n" + \
			"Please check name and command\nor switch it off."))
		return status


	def scripts_ok(self):
		status = True
		if self.script0_on.get_active() \
		and self.script0_file.get_text() == '':
			status = False

		if self.script1_on.get_active() \
		and self.script1_file.get_text() == '':
			status = False

		if self.script2_on.get_active() \
		and self.script2_file.get_text() == '':
			status = False

		if self.script3_on.get_active() \
		and self.script3_file.get_text() == '':
			status = False

		if self.script4_on.get_active() \
		and self.script4_file.get_text() == '':
			status = False

		if self.script5_on.get_active() \
		and self.script5_file.get_text() == '':
			status = False

		if status == False:
			self.show_message(_("Inconsistent entry on 'Script' tab.\n" + \
			"Please check script file entry\nor switch it off."))
		return status


	def filter_ok(self):
		status = True
		start, end = self.filter_text.get_bounds()
		if self.filter_on.get_active() \
		and self.filter_text.get_text(start, end) == '':
			status = False

		if status == False:
			self.show_message(_("Filter is switched on but filter text is empty.\n" + \
			"Please enter text or switch filter off."))
		return status


	def select_script(self, widget):									# open file chooser for script_file
		dialog = gtk.FileChooserDialog("Open..", None, \
			gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, \
			gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))		# create file dialog
		dialog.set_current_folder(user_folder + ".mailnag")				# set default folder
		dialog.set_default_response(gtk.RESPONSE_OK)					# set default button to OK
		response = dialog.run()											# show file dialog
		if response == gtk.RESPONSE_OK:									# if OK clicked
			selection = dialog.get_filename(), 'selected'				# get selection object
			pathfilename = selection[0]									# get path and filename
			name = gtk.Buildable.get_name(widget)						# get widget's name
			if name == 'select_script0': self.script0_file.set_text(pathfilename)
			if name == 'select_script1': self.script1_file.set_text(pathfilename)
			if name == 'select_script2': self.script2_file.set_text(pathfilename)
			if name == 'select_script3': self.script3_file.set_text(pathfilename)
			if name == 'select_script4': self.script4_file.set_text(pathfilename)
			if name == 'select_script5': self.script5_file.set_text(pathfilename)
		dialog.destroy()												# close file dialog


	def select_soundfile(self, widget):									# open file chooser for sound_file
		dialog = gtk.FileChooserDialog("Open..", None, \
			gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, \
			gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))		# create file dialog
		dialog.set_current_folder("/usr/lib/openoffice/basis3.2/share/gallery/sounds")	# set default folder
		dialog.set_default_response(gtk.RESPONSE_OK)					# set default button to OK
		response = dialog.run()											# show file dialog
		if response == gtk.RESPONSE_OK:									# if OK clicked
			selection = dialog.get_filename(), 'selected'				# get selection object
			pathfilename = selection[0]									# get path and filename
			self.soundfile.set_text(pathfilename)
		dialog.destroy()												# close file dialog


	def play_sound(self, widget):										# play sound file
		soundfile = self.soundfile.get_text()							# get sound file
		subprocess.Popen(['aplay', '-q', soundfile]).wait()				# play sound and wait until it is finished
		if self.speak.get_active():
			lang = locale.getdefaultlocale()[0].lower()					# get language from operating system
			if 'de' in lang:
				lang = 'de'
			else:
				lang = 'en'
			subprocess.Popen(['espeak', '-s', '140','-v' + lang, text])


	def show_message(self, text):										# Show Message Dialog
		message = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, \
			gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE, text)
		message.add_button(gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE)
		resp = message.run()											# show dialog window
		if resp == gtk.RESPONSE_CLOSE:									# if CLOSE clicked
			message.destroy()											# close message dialog


	def show_yesno_dialog(self, text):									# Show YesNo Dialog
		message = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, \
			gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, text)
		resp = message.run()											# show dialog window
		message.destroy()												# close dialog
		if resp == gtk.RESPONSE_YES: return True						# if YES clicked
		else: return False												# if NO clicked


	def show_imported_accounts(self, widget):							# get email accounts and put it in GUI fields
		accounts = keyring.import_accounts(self)						# list of imported accounts [server, user, password, imap]
		if len(accounts) > 0:
			for acc in accounts:
				if self.show_yesno_dialog(_('Import email account:') + \
				'\n\nServer: ' + acc[0] + '\nUser: ' + acc[1]):
					id = self.accounts.add(0, acc[0], acc[0], acc[1], acc[2], acc[3], '', '')
					# on, name, server, user, password, imap, folder, port
					row = [id, 0, acc[0]]								# id, on=0, server
					iter = self.liststore_account.append(row)			# put in treeview
					model = self.treeview_account.get_model()
					path = model.get_path(iter)
					treeselection = self.treeview_account.get_selection()	# get tree selection object
					self.treeview_account.set_cursor(path)
					self.treeview_account.grab_focus()					# put focus on treeview
		else:
			self.show_message(_('No additional email accounts available in keyring.'))


	def get_selected_account(self):										# return selected row
		treeselection = self.treeview_account.get_selection()			# get tree_selection object
		selection = treeselection.get_selected()						# get selected tupel (model, iter)
		model, iter = selection											# get selected iter
		if iter != None: id = model.get_value(iter, 0)					# get account_id from treeviews 1. column
		else: id = None
		return id, model, iter


	def select_path(self, path):										# select path in treeview
		treeselection = self.treeview_account.get_selection()			# get tree selection object
		treeselection.select_path(path)									# select path
		self.treeview_account.grab_focus()								# put focus on treeview


	def account_changed(self, treeview):								# account treeview row changed
		id, model, iter = self.get_selected_account()
		account = self.accounts.get(id)									# get data of selected account

		self.account_id.set_text(account.id)
		model.set_value(iter, 1, account.on)
		self.account_name.set_text(account.name)
		self.account_server.set_text(account.server)
		self.account_user.set_text(account.user)
		self.account_password.set_text(account.password)
		self.account_imap.set_active(account.imap)
		self.account_folder.set_text(account.folder)
		self.account_port.set_text(account.port)


	def account_field_changed(self, widget):							# update treeview and account model on field changes
		id, model, iter = self.get_selected_account()
		if len(model) > 0:												# account list not empty
			name = gtk.Buildable.get_name(widget)
			current_account = self.accounts.get_current()
			if name == 'entry_account_name':
				id, model, iter = self.get_selected_account()
				if iter != None:
					model.set_value(iter, 2, widget.get_text())
				current_account.name = widget.get_text()
			if name == 'entry_account_server':
				current_account.server = widget.get_text()
			if name == 'entry_account_user':
				current_account.user = widget.get_text()
			if name == 'entry_account_password':
				current_account.password = widget.get_text()
			if name == 'chk_account_imap':
				current_account.imap = bool(int(widget.get_active()))
			if name == 'entry_account_folder':
				current_account.folder = widget.get_text()
			if name == 'entry_account_port':
				current_account.port = widget.get_text()


	def account_on_toggled(self, cell, path):							# chk_box account_on toggled
		model = self.liststore_account
		iter = model.get_iter(path)
		id = model.get_value(iter, 0)
		acc = self.accounts.get(id)										# get account by id
		acc.on = not acc.on												# update account.on


	def add_account(self, widget):										# add new account
		id = self.accounts.add()										# create account
		row = [id, 0, '???']
		iter = self.liststore_account.append(row)						# put in treeview
		model = self.treeview_account.get_model()
		path = model.get_path(iter)
		treeselection = self.treeview_account.get_selection()			# get tree selection object
		self.treeview_account.set_cursor(path)
		self.treeview_account.grab_focus()								# put focus on treeview
		return id, iter


	def del_account(self, widget):										# delete account
		id, model, iter = self.get_selected_account()
		if iter != None:
			name = model.get_value(iter, 2)								# get account_name
			if self.show_yesno_dialog(_('Delete this account:') + \
				'\n\n' + name):
				model.remove(iter)										# delete in treeview
				self.accounts.remove(id)								# delete in accounts list
				path = model.get_path(iter)
				if path == None:
					path = (len(model)-1,)
				self.select_path(path)									# select first row in treeview
				if len(model) == 0:										# tree is empty
					self.clear_account_fields()
					self.add_account(None)


	def clear_account_fields(self):										# empty all account fields
		self.account_id.set_text('')
		self.account_name.set_text('')
		self.account_server.set_text('')
		self.account_user.set_text('')
		self.account_password.set_text('')
		self.account_imap.set_active(False)
		self.account_folder.set_text('')
		self.account_port.set_text('')


	def preview_dd(self, widget):										# preview desktop display
		if self.desktop_display == None:
			content = [['Sender 1 - 2010.12.31 13:57:01','This is an example subject text'], \
					   ['Sender 2 - 2010.12.31 13:57:02','This is another example subject text'], \
					   ['Sender 3 - 2010.12.31 13:57:03','This is a very very very very long example subject text'], \
					   ['Sender 3 - 2010.12.31 13:57:04','This is the last example subject text']]
			cfg.set('dd', 'pos_x', self.dd_pos_x.get_text())			# get all current values
			cfg.set('dd', 'pos_y', self.dd_pox_y.get_text())
			cfg.set('dd', 'width', self.dd_width.get_text())
			cfg.set('dd', 'height', self.dd_height.get_text())
			cfg.set('dd', 'bg_color', self.dd_bg_color.get_color())
			cfg.set('dd', 'transparency', self.dd_transparency.get_value())
			cfg.set('dd', 'text_color', self.dd_text_color.get_color())
			cfg.set('dd', 'font_name', self.dd_font.get_font_name())
			cfg.set('dd', 'click_close', int(self.dd_click_close.get_active()))
			cfg.set('dd', 'click_launch', int(self.dd_click_launch.get_active()))

			self.desktop_display = DesktopDisplay(content)
			self.desktop_display.show()
		else:
			self.desktop_display.destroy()
			self.desktop_display = None


# Keyring ==============================================================

class Keyring:
	def __init__(self):
		glib.set_application_name('mailnag')
		self.was_locked = False											# True if Dialog shown. Required for Sortorder problem
		self.keyring_password = ''
		self.defaultKeyring = gnomekeyring.get_default_keyring_sync()
		if self.defaultKeyring == None:
			self.defaultKeyring = 'login'

		while gnomekeyring.get_info_sync(self.defaultKeyring).get_is_locked():		# Keyring locked?
			self.message_response = 'cancel'							# default response for message dialog
			try:
				try: gnomekeyring.unlock_sync(self.defaultKeyring, \
						self.keyring_password)
				except gnomekeyring.IOError:
					self.show_keyring_dialog()							# get keyring password
					gtk.main()											# wait until dialog is closed
					result = gnomekeyring.unlock_sync(self.defaultKeyring, \
								self.keyring_password)
			except gnomekeyring.IOError:
				self.show_message(_('Failed to unlock Keyring "' + self.defaultKeyring + '".' + \
									'\nWrong password.\n\nDo you want to try again?'))
				gtk.main()												# wait until dialog is closed
				if self.message_response == 'cancel': exit(1)			# close application (else: continue getting password)


	def get(self, protocol, user, server):												# get password for account from Gnome Keyring
		if gnomekeyring.list_item_ids_sync(self.defaultKeyring):
			displayNameDict = {}
			for identity in gnomekeyring.list_item_ids_sync(self.defaultKeyring):
				item = gnomekeyring.item_get_info_sync(self.defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity

			if 'Mailnag password for %s://%s@%s' % (protocol, user, server) in displayNameDict:

				if gnomekeyring.item_get_info_sync(self.defaultKeyring, \
				displayNameDict['Mailnag password for %s://%s@%s' % \
				(protocol, user, server)]).get_secret() != '':
					return gnomekeyring.item_get_info_sync(self.defaultKeyring, \
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


	def import_accounts(self, gui):										# get email accounts from Gnome-Keyring
		accounts = []
		if gnomekeyring.list_item_ids_sync(self.defaultKeyring):
			displayNameDict = {}
			for identity in gnomekeyring.list_item_ids_sync(self.defaultKeyring):
				item = gnomekeyring.item_get_info_sync(self.defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity
			for displayName in displayNameDict:
				if displayName.startswith('pop://') \
				or displayName.startswith('imap://'):
					server = displayName.split('@')[1][:-1]
					if displayName.startswith('imap://'):
						imap = 1
						user = displayName.split('@')[0][7:]
					else:
						imap = 0
						user = displayName.split('@')[0][6:]
					user = user.replace('%40','@')
					if ';' in user:
						user = user.split(';')[0]
					password = gnomekeyring.item_get_info_sync(self.defaultKeyring, \
						displayNameDict[displayName]).get_secret()
					accounts.append([server, user, password, imap])
		return accounts


	def set(self, protocol, user, server, password):					# store password in Gnome-Keyring
		if password != '':
			displayNameDict = {}
			for identity in gnomekeyring.list_item_ids_sync(self.defaultKeyring):
				item = gnomekeyring.item_get_info_sync(self.defaultKeyring, identity)
				displayNameDict[item.get_display_name()] = identity

			if 'Mailnag password for %s://%s@%s' % (protocol, user, server) in displayNameDict:

				if password != gnomekeyring.item_get_info_sync(self.defaultKeyring, \
				displayNameDict['Mailnag password for %s://%s@%s' % \
				(protocol, user, server)]).get_secret():
					gnomekeyring.item_create_sync(self.defaultKeyring, \
						gnomekeyring.ITEM_GENERIC_SECRET, \
						'Mailnag password for %s://%s@%s' % (protocol, user, server), \
						{'application':'Mailnag', 'protocol':protocol, 'user':user, 'server':server}, \
						password, True)
			else:
				gnomekeyring.item_create_sync(self.defaultKeyring, \
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
				if key[:19] == 'Mailnag password for' \
				and key not in valid_accounts:
					gnomekeyring.item_delete_sync(defaultKeyring, displayNameDict[key])


	def show_keyring_dialog(self):										# dialog to get password to unlock keyring
		self.was_locked = True
		builder = gtk.Builder()
		builder.set_translation_domain('mailnag_config')
		builder.add_from_file("mailnag_keyring.glade")
		builder.connect_signals({"gtk_main_quit" : self.exit_keyring_dialog, \
			"on_button_cancel_clicked" : self.exit_keyring_dialog, \
			"on_button_ok_clicked" : self.ok_keyring_dialog, \
			"on_entry_password_activate" : self.ok_keyring_dialog})		# hit RETURN in entry field
		self.window = builder.get_object("dialog_keyring")
		self.password = builder.get_object("entry_password")
		self.window.show()


	def exit_keyring_dialog(self, widget):								# password dialog exit or cancel clicked
		self.window.destroy()
		gtk.main_quit()													# terminate loop to allow continuation


	def ok_keyring_dialog(self, widget):								# password dialog ok clicked
		self.keyring_password = self.password.get_text()				# get text from widget
		self.exit_keyring_dialog(widget)


	def show_message(self, message):									# dialog to show keyring messages
		builder = gtk.Builder()
		builder.set_translation_domain('mailnag_config')
		builder.add_from_file("mailnag_message.glade")
		builder.connect_signals({"gtk_main_quit" : self.exit_message, \
			"on_button_cancel_clicked" : self.exit_message, \
			"on_button_ok_clicked" : self.ok_message})
		self.window = builder.get_object("dialog_message")
		self.message = builder.get_object("label_message")
		self.message.set_text(message)									# put message text into label
		self.window.show()


	def exit_message(self, widget):										# keyring message dialog exit or cancel clicked
		self.window.destroy()
		gtk.main_quit()													# terminate loop to allow continuation


	def ok_message(self, widget):										# keyring message dialog ok clicked
		self.message_response = 'ok'
		self.exit_message(widget)


# Account and Accounts =================================================

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


	def add(self, on = 0, name = '???', server = '', user= '' , \
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
			on = int(on_list[i])
			name = name_list[i]
			if name == '': continue
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
			message_text = _("Missing data in account(s):\n\n")
			for acc_name in nok:
				message_text += acc_name + '\n'
			message_text += _("\nPlease correct this first.")
			window.show_message(message_text)
			return False, nok
		else:
			return True, True


# Desktop Display ======================================================
class DesktopDisplay(gtk.Window):										# displays a transparent frameless window on the desktop
	__gsignals__ = {
		'expose-event': 'override'
		}

	def __init__(self, content):
		super(DesktopDisplay, self).__init__()

		self.content = content											# array of text lists

		self.set_title('Mailnag Desktop Display')
		self.set_app_paintable(True)									# no window border
		self.set_decorated(False)
		self.set_position(gtk.WIN_POS_CENTER)
		pixbuf = gtk.gdk.pixbuf_new_from_file('mailnag.png')				# get icon from png
		self.set_icon(pixbuf)											# set window icon
		pos_x = int(cfg.get('dd', 'pos_x'))
		pos_y = int(cfg.get('dd', 'pos_y'))
		self.move(pos_x, pos_y)											# move window to position x,y

		screen = self.get_screen()										# see if we can do transparency
		alphamap = screen.get_rgba_colormap()
		rgbmap   = screen.get_rgb_colormap()
		if alphamap is not None:
			self.set_colormap(alphamap)
		else:
			self.set_colormap(rgbmap)
			print _("Warning: transparency is not supported")

		width = int(cfg.get('dd','width'))
		height = int(cfg.get('dd','height'))
		self.set_size_request(width, height)

		font = cfg.get('dd','font_name').split(' ')						# make list ['ubuntu', 12]
		self.font_name = ' '.join(font[:-1])							# everything except the last one
		try:
			self.font_size = int(font[-1])								# only the last one
		except ValueError:												# if something wrong, use defaults
			self.font_name = 'ubuntu'
			self.font_size = '14'


	def do_expose_event(self, event):
		width, height = self.get_size()
		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
		ctx = cairo.Context(surface)

		# Background
		red, green, blue = self.get_rgb(str(cfg.get('dd','bg_color')))	# convert hex color to (r, g, b) / 100 values
		alpha = (100 - int(cfg.get('dd','transparency'))) / 100.0
		ctx.set_source_rgba(red, green, blue, alpha)					# background is red, green, blue, alpha
		ctx.paint()

		# Text
		ctx.select_font_face(self.font_name, cairo.FONT_SLANT_NORMAL, \
			cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size(self.font_size)
		red, green, blue = self.get_rgb(str(cfg.get('dd','text_color')))
		ctx.set_source_rgb(red, green, blue)
		self.show_text(ctx, self.content)								# write text to surface

		dest_ctx = self.window.cairo_create()							# now copy to our window surface
		dest_ctx.rectangle(event.area.x, event.area.y, \
			event.area.width, event.area.height)						# only update what needs to be drawn
		dest_ctx.clip()

		dest_ctx.set_operator(cairo.OPERATOR_SOURCE)					# source operator means replace, don't draw on top of
		dest_ctx.set_source_surface(surface, 0, 0)
		dest_ctx.paint()


	def show_text(self, ctx, content):									# write text to surface
		x = 10
		y = 20
		mail_offset = 10
		line_offset = self.font_size
		width = int(cfg.get('dd','width'))
		x_cut = int(width / self.font_size * 1.7)						# end of line
		height = int(cfg.get('dd','height'))
		y_cut = int(height / (2 * line_offset + mail_offset)) - 2		# end of page
		mail_count = 0

		for mail in content:											# iterate all mails
			mail_count += 1
			for line in mail:											# iterate lines in mail
				ctx.move_to(x, y)
				if len(line) > x_cut: continuation = '...'
				else: continuation = ''
				ctx.show_text(line[:x_cut] + continuation)				# print stripped line
				y += line_offset
			y += mail_offset
			if mail_count > y_cut:										# end of page
				if len(content) > mail_count:
					ctx.move_to(x, y)
					ctx.show_text('...')
				break


	def get_rgb(self, hexcolor):										# convert hex color to (r, g, b) / 100 values
		color = gtk.gdk.color_parse(hexcolor)
		divisor = 65535.0
		red = color.red / divisor
		green = color.green / divisor
		blue = color.blue / divisor
		return red, green, blue											# exp.: 0.1, 0.5, 0.8


# Miscellaneous ========================================================

def read_config():														# read config file or create it
	cfg = ConfigParser.RawConfigParser()
	cfg_file = user_folder + ".mailnag/mailnag.cfg"						# folder: /home/user/.mailnag/mailnag.cfg
	if not os.path.exists(cfg_file):									# create a fresh config file
		print _("Config file does not exist, creating new one")
		cfg = set_default_config(cfg)									# write default values to cfg
		with open(cfg_file, 'wb') as configfile: cfg.write(configfile)

	cfg.read(cfg_file)
	return cfg


def set_default_config(cfg):
	try: cfg.add_section('general')
	except ConfigParser.DuplicateSectionError: pass
	cfg.set('general', 'autostart', 1)
	cfg.set('general', 'version', VERSION)

	try: cfg.add_section('account')
	except ConfigParser.DuplicateSectionError: pass
	cfg.set('account', 'on', '1|0')
	cfg.set('account', 'name', 'GMX|Gmail')
	cfg.set('account', 'server', 'pop.gmx.net|imap.googlemail.com')
	cfg.set('account', 'user', 'john.doe@gmx.net|john.dow@gmail.com')
	cfg.set('account', 'imap', '0|1')
	cfg.set('account', 'folder', '|INBOX,ARCHIVE')
	cfg.set('account', 'port', '|')

	cfg.set('account', 'frequency', '30')
	cfg.set('account', 'check_once', 0)

	try: cfg.add_section('indicate')
	except ConfigParser.DuplicateSectionError: pass
	cfg.set('indicate', 'headline', 'New Emails')
	cfg.set('indicate', 'show_sender', 1)
	cfg.set('indicate', 'sender_format', 1)
	cfg.set('indicate', 'message_format', 1)
	cfg.set('indicate', 'sort_by', 1)
	cfg.set('indicate', 'show_subject', 1)
	cfg.set('indicate', 'show_provider', 1)
	cfg.set('indicate', 'subject_length', '30')
	cfg.set('indicate', 'remember', 1)
	cfg.set('indicate', 'start_on_click', 'evolution')
	cfg.set('indicate', 'clear_on_click', 1)
	cfg.set('indicate', 'show_only_new', 0)
	cfg.set('indicate', 'remove_single_email', 0)

	cfg.set('indicate', 'show_menu_1', 0)
	cfg.set('indicate', 'show_menu_2', 0)
	cfg.set('indicate', 'show_menu_3', 0)
	cfg.set('indicate', 'name_menu_1', 'Write new email')
	cfg.set('indicate', 'name_menu_2', 'Open address book')
	cfg.set('indicate', 'name_menu_3', '')
	cfg.set('indicate', 'cmd_menu_1', 'evolution mailto:')
	cfg.set('indicate', 'cmd_menu_2', 'evolution -c contacts')
	cfg.set('indicate', 'cmd_menu_3', '')

	try: cfg.add_section('notify')
	except ConfigParser.DuplicateSectionError: pass
	cfg.set('notify', 'notify', 1)
	cfg.set('notify','text_one', 'You have a new mail.')
	cfg.set('notify','text_multi', 'You have %s new mails.')
	cfg.set('notify', 'playsound', 1)
	cfg.set('notify', 'soundfile', 'mailnag.wav')
	cfg.set('notify', 'speak', 0)

	try: cfg.add_section('dd')
	except ConfigParser.DuplicateSectionError: pass
	cfg.set('dd', 'on', 0)
	cfg.set('dd', 'pos_x', '1000')
	cfg.set('dd', 'pos_y', '30')
	cfg.set('dd', 'width', '300')
	cfg.set('dd', 'height', '800')
	cfg.set('dd', 'bg_color', '#E5E5E5')
	cfg.set('dd', 'transparency', '80')
	cfg.set('dd', 'text_color', '#000000')
	cfg.set('dd', 'font_name', 'ubuntu 14')
	cfg.set('dd', 'click_close', 1)
	cfg.set('dd', 'click_launch', 0)

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

	try: cfg.add_section('filter')
	except ConfigParser.DuplicateSectionError: pass
	cfg.set('filter', 'filter_on', 0)
	cfg.set('filter', 'filter_text', '')

	return cfg


def update_desktop_file(headline):
	desktop_content = "[Desktop Entry]\n" + \
		"Encoding=UTF-8\n" + \
		"Name=" + headline + "\n" + \
		"GenericName=Email Notifier\n" + \
		"X-GNOME-FullName=Mailnag Email Notifier\n" + \
		"Comment=Get notified about new emails\n" + \
		"Icon=applications-email-panel\n" + \
		"Type=Application\n" + \
		"Categories=GNOME;GTK;Email;Network;\n" + \
		"Exec=mailnag.py\n" + \
		"StartupNotify=false\n" + \
		"Terminal=false\n" + \
		"X-Ayatana-Desktop-Shortcuts=Compose;Contacts\n"

	desktop_file = user_folder + ".mailnag/mailnag.desktop"				# folder: /home/user/.mailnag/mailnag.desktop
	f = open(desktop_file,'w')
	f.write(desktop_content)
	f.close()


# Autostart ============================================================

def create_autostart():
	curdir = os.getcwd()												# get working directory
	exec_file = os.path.join(curdir, "mailnag.sh")						# path of the shell script to start mailnag.py

	content = "\n" + \
	"[Desktop Entry]\n" + \
	"Type=Application\n" + \
	"Exec=" + exec_file + "\n" + \
	"Hidden=false\n" + \
	"NoDisplay=false\n" + \
	"X-GNOME-Autostart-enabled=true\n" + \
	"Name=Mailnag\n" + \
	"Comment=Email notifier for GNOME 3"

	autostart_folder = "%s/.config/autostart/" % (user_folder)
	if not os.path.exists(autostart_folder):
		os.popen("mkdir -p " + autostart_folder)
	autostart_file = autostart_folder + "mailnag.sh.desktop"
	f = open(autostart_file, 'w')
	f.write(content)													# create it
	f.close()


def delete_autostart():
	autostart_folder = "%s/.config/autostart/" % (user_folder)
	autostart_file = autostart_folder + "mailnag.sh.desktop"
	if os.path.exists(autostart_file):
		os.popen("rm " + autostart_file)								# delete it


# Main =================================================================

def main():
	global cfg, user_folder, keyring, VERSION, _
	VERSION = "0.28"

	try:
		locale.setlocale(locale.LC_ALL, '')								# locale language, e.g.: de_CH.utf8
	except locale.Error:
		locale.setlocale(locale.LC_ALL, 'en_US.utf8')					# english for all unsupported locale languages
	locale.bindtextdomain('mailnag_config', 'locale')
	gettext.bindtextdomain('mailnag_config', 'locale')
	gettext.textdomain('mailnag_config')
	_ = gettext.gettext

	user_folder = os.path.expanduser("~/")								# folder: /home/user/
	mailnag_folder = user_folder + ".mailnag"								# folder: /home/user/.mailnag
	if not os.path.exists(mailnag_folder):
		os.popen("mkdir -p " + mailnag_folder)							# create: "/home/user/.mailnag" if not exists

	cfg = read_config()													# get configurations
	keyring = Keyring()
	settings = Settings()												# start settings GUI

	gtk.main()															# start main loop


if __name__ == "__main__":  main()

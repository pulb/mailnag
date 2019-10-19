#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# spamfilterplugin.py
#
# Copyright 2013 - 2016 Patrick Ulbrich <zulu99@gmx.net>
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

from gi.repository import Gtk
from Mailnag.common.plugins import Plugin, HookTypes
from Mailnag.common.i18n import _

plugin_defaults = { 'filter_text' : 'newsletter, viagra' }


class SpamfilterPlugin(Plugin):
	def __init__(self):
		self._filter_mails_hook = None
		self._filter_list = None
	
	def enable(self):
		config = self.get_config()
		self._filter_list = config['filter_text'].replace('\n', '').split(',')
		
		def filter_mails_hook(mails):
			lst = []
			for m in mails:
				if not self._is_filtered(m):
					lst.append(m)
			return lst
		
		self._filter_mails_hook = filter_mails_hook
		
		controller = self.get_mailnag_controller()
		hooks = controller.get_hooks()
		
		hooks.register_hook_func(HookTypes.FILTER_MAILS, 
			self._filter_mails_hook)
		
	
	def disable(self):
		controller = self.get_mailnag_controller()
		hooks = controller.get_hooks()
		
		if self._filter_mails_hook != None:
			hooks.unregister_hook_func(HookTypes.FILTER_MAILS,
				self._filter_mails_hook)
			self._filter_mails_hook = None
		
		self._filter_list = None
	
	
	def get_manifest(self):
		return (_("Spam Filter"),
				_("Filters out unwanted mails."),
				"1.1",
				"Patrick Ulbrich <zulu99@gmx.net>",
				False)


	def get_default_config(self):
		return plugin_defaults
	
	
	def has_config_ui(self):
		return True
	
	
	def get_config_ui(self):
		box = Gtk.Box()
		box.set_spacing(12)
		box.set_orientation(Gtk.Orientation.VERTICAL)
		#box.set_size_request(100, -1)
		
		desc =  _('Mailnag will ignore mails containing at least one of \nthe following words in subject or sender.')
		
		label = Gtk.Label(desc)
		label.set_line_wrap(True)
		#label.set_size_request(100, -1);
		box.pack_start(label, False, False, 0)
		
		scrollwin = Gtk.ScrolledWindow()
		scrollwin.set_shadow_type(Gtk.ShadowType.IN)
		scrollwin.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		scrollwin.set_size_request(-1, 60)
		
		txtbuffer = Gtk.TextBuffer()
		txtview = Gtk.TextView()
		txtview.set_buffer(txtbuffer)
		txtview.set_wrap_mode(Gtk.WrapMode.WORD)
		
		scrollwin.add(txtview)
		
		box.pack_start(scrollwin, True, True, 0)
		
		return box
	
	
	def load_ui_from_config(self, config_ui):
		config = self.get_config()
		txtview = config_ui.get_children()[1].get_child()
		txtview.get_buffer().set_text(config['filter_text'])
	
	
	def save_ui_to_config(self, config_ui):
		config = self.get_config()
		txtview = config_ui.get_children()[1].get_child()
		txtbuffer = txtview.get_buffer()
		start, end = txtbuffer.get_bounds()
		config['filter_text'] = txtbuffer.get_text(start, end, False)
	
	
	def _is_filtered(self, mail):
		is_filtered = False
		
		for f in self._filter_list:
			# remove CR and white space
			f = f.strip()			
			
			if len (f) == 0:
				continue
			
			f = f.lower()
			sender_name, sender_addr = mail.sender
			if (f in sender_name.lower()) or (f in sender_addr.lower()) \
				or (f in mail.subject.lower()):
				# sender or subject contains filter string
				is_filtered = True
				break
		
		return is_filtered

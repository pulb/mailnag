#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# soundplugin.py
#
# Copyright 2013 Patrick Ulbrich <zulu99@gmx.net>
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
import threading
from common.plugins import Plugin, HookTypes
from common.utils import get_data_file
from gi.repository import Gst, Gio

plugin_defaults = { 'soundfile' : 'mailnag.ogg' }


class SoundPlugin(Plugin):
	def __init__(self):
		self._mails_added_hook = None
		self._gsettings = None

	
	def enable(self):
		self._gsettings = Gio.Settings.new('org.gnome.shell')
		
		def mails_added_hook(all_mails, new_mail_count):
			if self._gsettings.get_int('saved-session-presence') != 2:
				config = self.get_config()
				gstplay(get_data_file(config['soundfile']))
		
		self._mails_added_hook = mails_added_hook
		
		controller = self.get_mailnag_controller()
		
		controller.hooks.register_hook_func(HookTypes.MAILS_ADDED, 
			self._mails_added_hook)
		
	
	def disable(self):
		controller = self.get_mailnag_controller()
		
		if self._mails_added_hook != None:
			controller.hooks.unregister_hook_func(HookTypes.MAILS_ADDED,
				self._mails_added_hook)
			self._mails_added_hook = None
		
		self._gsettings = None

	
	def get_manifest(self):
		return ("Sound notifications",
				"Plays a sound when new mails arrive.",
				"1.0",
				"Patrick Ulbrich <zulu99@gmx.net>",
				False)


	def get_default_config(self):
		return plugin_defaults
	
	
	def has_config_ui(self):
		return False
	
	
	def get_config_ui(self):
		return None
	
	
	def load_ui_from_config(self, config_ui):
		pass
	
	
	def save_ui_to_config(self, config_ui):
		pass


class _GstPlayThread(threading.Thread):
	def __init__(self, ply):
		self.ply = ply
		threading.Thread.__init__(self)
	
	
	def run(self):
		def on_eos(bus, msg):
#			print "EOS" # debug
			self.ply.set_state(Gst.State.NULL)
			return True
		
		bus = self.ply.get_bus()
		bus.add_signal_watch()
		bus.connect('message::eos', on_eos)
		
		self.ply.set_state(Gst.State.PLAYING)


_gst_initialized = False

def gstplay(filename):
	global _gst_initialized
	if not _gst_initialized:
		Gst.init(None)
		_gst_initialized = True
		
	try:
		cwd = os.getcwd()
		location = os.path.join(cwd, filename)
		ply = Gst.ElementFactory.make("playbin", "player")
		ply.set_property("uri", "file://" + location)
		pt = _GstPlayThread(ply)
		pt.start()
	except:
		pass

#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# soundplugin.py
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
gi.require_version('Gst', '1.0')

import os
import threading
from gi.repository import Gst
from Mailnag.common.plugins import Plugin, HookTypes
from Mailnag.common.utils import get_data_file
from Mailnag.common.i18n import _


plugin_defaults = { 'soundfile' : 'mailnag.ogg' }


class SoundPlugin(Plugin):
	def __init__(self):
		self._mails_added_hook = None

	
	def enable(self):
		def mails_added_hook(new_mails, all_mails):
			config = self.get_config()
			gstplay(get_data_file(config['soundfile']))
		
		self._mails_added_hook = mails_added_hook
		
		controller = self.get_mailnag_controller()
		hooks = controller.get_hooks()
		
		hooks.register_hook_func(HookTypes.MAILS_ADDED, 
			self._mails_added_hook)
		
	
	def disable(self):
		controller = self.get_mailnag_controller()
		hooks = controller.get_hooks()
		
		if self._mails_added_hook != None:
			hooks.unregister_hook_func(HookTypes.MAILS_ADDED,
				self._mails_added_hook)
			self._mails_added_hook = None

	
	def get_manifest(self):
		return (_("Sound Notifications"),
				_("Plays a sound when new mails arrive."),
				"1.1",
				"Patrick Ulbrich <zulu99@gmx.net>",
				False)


	def get_default_config(self):
		return plugin_defaults
	
	
	def has_config_ui(self):
		return False
	
	
	def get_config_ui(self):
		# TODO : Add ui to specify the path 
		# of a custom sound file.
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
#			loggin.debug('EOS')
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
		ply = Gst.ElementFactory.make("playbin", "player")
		ply.set_property("uri", "file://" + os.path.abspath(filename))
		pt = _GstPlayThread(ply)
		pt.start()
	except:
		pass

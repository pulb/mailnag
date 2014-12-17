#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# plugindialog.py
#
# Copyright 2013, 2014 Patrick Ulbrich <zulu99@gmx.net>
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
from common.dist_cfg import PACKAGE_NAME
from common.utils import get_data_file

class PluginDialog:
	def __init__(self, parent, plugin):
		self._plugin = plugin
		
		builder = Gtk.Builder()
		builder.set_translation_domain(PACKAGE_NAME)
		builder.add_from_file(get_data_file("plugin_dialog.ui"))
		builder.connect_signals({ \
			"btn_cancel_clicked" : self._on_btn_cancel_clicked, \
			"btn_save_clicked" : self._on_btn_save_clicked \
		})

		self._window = builder.get_object("plugin_dialog")
		self._window.set_transient_for(parent)

		self._vbox = builder.get_object("vbox")
		
		
	def run(self):
		widget = self._plugin.get_config_ui()
		
		if widget != None:
			self._vbox.pack_start(widget, True, True, 0)
			widget.show_all()
			self._plugin.load_ui_from_config(widget)
		
		res = self._window.run()
		
		if res == 1:
			if widget != None:
				self._plugin.save_ui_to_config(widget)
		
		self._window.destroy()
		return res

	
	def _on_btn_cancel_clicked(self, widget):
		pass


	def _on_btn_save_clicked(self, widget):
		pass

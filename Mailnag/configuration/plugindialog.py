# Copyright 2013 - 2019 Patrick Ulbrich <zulu99@gmx.net>
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
from Mailnag.common.i18n import _


class PluginDialog:
	def __init__(self, parent, plugin):
		self._plugin = plugin
		
		self._window = Gtk.Dialog(title = _('Plugin Configuration'), parent = parent, use_header_bar = True, \
			buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
		
		self._window.set_default_response(Gtk.ResponseType.OK)
		self._window.set_default_size(480, 0)
		
		self._box = self._window.get_content_area()
		self._box.set_border_width(12)
		self._box.set_spacing(12)

		
	def run(self):
		widget = self._plugin.get_config_ui()
		
		if widget != None:
			self._box.pack_start(widget, True, True, 0)
			widget.show_all()
			self._plugin.load_ui_from_config(widget)
		
		res = self._window.run()
		
		if res == Gtk.ResponseType.OK:
			if widget != None:
				self._plugin.save_ui_to_config(widget)
		
		self._window.destroy()
		return res

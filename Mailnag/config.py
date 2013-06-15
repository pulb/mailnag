#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# config.py
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
import subprocess
from gi.repository import Gtk
from dbus.mainloop.glib import DBusGMainLoop

from common.utils import set_procname, shutdown_existing_instance
from common.dist_cfg import BIN_DIR
from configuration.configwindow import ConfigWindow


def main():
	set_procname("mailnag_config")
	confwin = ConfigWindow()
	Gtk.main()
	
	if confwin.daemon_enabled:
		try:
			# the launched daemon shuts down 
			# an already running daemon
			print "Launching Mailnag daemon."
			subprocess.Popen(os.path.join(BIN_DIR, "mailnag"))
		except:
			print "ERROR: Failed to launch Mailnag daemon."
	else:
		DBusGMainLoop(set_as_default = True)
		# shutdown running Mailnag daemon
		shutdown_existing_instance()


if __name__ == "__main__":  main()

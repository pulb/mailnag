#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mails.py
#
# Copyright 2011 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2007 Marco Ferragina <marco.ferragina@gmail.com>
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

import xdg.BaseDirectory as base
from gi.repository import Gst
import threading
import os

PACKAGE_NAME = "mailnag"

def get_data_file(filename):
	"""
	Return path to @filename if it exists
	anywhere in the data paths, else return None
	"""
	# Add "./data" in workdir for running from builddir
	data_paths = []
	data_paths.append("./data")
	data_paths.extend(base.load_data_paths(PACKAGE_NAME))

	for direc in data_paths:
		file_path = os.path.join(direc, filename)
		if os.path.exists(file_path):
			return file_path
	return None


def set_procname(newname):
	from ctypes import cdll, byref, create_string_buffer
	libc = cdll.LoadLibrary('libc.so.6')
	buff = create_string_buffer(len(newname)+1)
	buff.value = newname
	libc.prctl(15, byref(buff), 0, 0, 0)


class _GstPlayThread(threading.Thread):
	def __init__(self, ply):
		self.ply = ply
		threading.Thread.__init__(self)
	
	
	def run(self):
		self.ply.set_state(Gst.State.PLAYING)
		
		def on_eos(bus, msg):
			self.ply.set_state(Gst.State.NULL)
			return True
		
		bus = self.ply.get_bus()		
		bus.add_signal_watch()
		bus.connect('message::eos', on_eos)
			

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

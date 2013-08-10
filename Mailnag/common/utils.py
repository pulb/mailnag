#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# utils.py
#
# Copyright 2011 - 2013 Patrick Ulbrich <zulu99@gmx.net>
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
import os
import sys
import time
import dbus
import urllib2
import subprocess
import threading

from common.dist_cfg import PACKAGE_NAME, DBUS_BUS_NAME, DBUS_OBJ_PATH

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


# check for internet connection
def is_online():
	try:
		urllib2.urlopen("http://www.google.com/")
		return True
	except:
		return False


def shutdown_existing_instance():
	bus = dbus.SessionBus()
	
	if bus.name_has_owner(DBUS_BUS_NAME):
		sys.stdout.write('Shutting down existing Mailnag process...')
		sys.stdout.flush()
		
		try:
			proxy = bus.get_object(DBUS_BUS_NAME, DBUS_OBJ_PATH)
			shutdown = proxy.get_dbus_method('Shutdown', DBUS_BUS_NAME)
			
			shutdown()
			
			while bus.name_has_owner(DBUS_BUS_NAME):
				time.sleep(2)
			
			print 'OK'
		except:
			print 'FAILED'


def start_subprocess(args, shell = False, callback = None):
	def thread():
		p = subprocess.Popen(args, shell = shell)
		retcode = p.wait()
		if callback != None:
			callback(retcode)
	
	t = threading.Thread(target = thread)
	t.start()

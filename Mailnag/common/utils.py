#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# utils.py
#
# Copyright 2011 - 2019 Patrick Ulbrich <zulu99@gmx.net>
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
import logging
import logging.handlers
import inspect

from Mailnag.common.dist_cfg import PACKAGE_NAME, DBUS_BUS_NAME, DBUS_OBJ_PATH

LOG_FORMAT = '%(levelname)s (%(asctime)s): %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def init_logging(enable_stdout = True, enable_syslog = True, log_level = logging.DEBUG):
	logging.basicConfig(
		format = LOG_FORMAT,
		datefmt = LOG_DATE_FORMAT,
		level = log_level)
	
	logger = logging.getLogger('')
	
	if not enable_stdout:
		stdout_handler = logger.handlers[0]
		logger.removeHandler(stdout_handler)
	
	if enable_syslog:
		syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
		syslog_handler.setLevel(log_level)
		syslog_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
	
		logger.addHandler(syslog_handler)


def get_data_paths():
	# Add "./data" in workdir for running from builddir
	data_paths = []
	data_paths.append("./data")
	data_paths.extend(base.load_data_paths(PACKAGE_NAME))
	return data_paths


def get_data_file(filename):
	"""
	Return path to @filename if it exists
	anywhere in the data paths, else return None
	"""
	
	data_paths = get_data_paths()

	for direc in data_paths:
		file_path = os.path.join(direc, filename)
		if os.path.exists(file_path):
			return file_path
	return None


def splitstr(strn, delimeter):
	return [s.strip() for s in strn.split(delimeter) if s.strip()]

			
def fix_cwd():
	# Change into local Mailnag source dir, where paths 
	# in dist_cfg.py point to (e.g. "./locale").
	# Only required when running Mailnag locally (wihout installation).
	main_script_path = os.path.realpath(inspect.stack()[-1][1])
	main_script_dir = os.path.dirname(main_script_path)
	os.chdir(main_script_dir)


def set_procname(newname):
	from ctypes import cdll, byref, create_string_buffer
	libc = cdll.LoadLibrary('libc.so.6')
	buff = create_string_buffer(len(newname)+1)
	buff.value = newname
	libc.prctl(15, byref(buff), 0, 0, 0)


def try_call(f, err_retval = None):
	try:
		return f()
	except:
		logging.exception('Caught an exception.')
		return err_retval


def shutdown_existing_instance(wait_for_completion = True):
	bus = dbus.SessionBus()
	
	if bus.name_has_owner(DBUS_BUS_NAME):
		sys.stdout.write('Shutting down existing Mailnag process...')
		sys.stdout.flush()
		
		try:
			proxy = bus.get_object(DBUS_BUS_NAME, DBUS_OBJ_PATH)
			shutdown = proxy.get_dbus_method('Shutdown', DBUS_BUS_NAME)
			
			shutdown()
			
			if wait_for_completion:
				while bus.name_has_owner(DBUS_BUS_NAME):
					time.sleep(2)
			
			print('OK')
		except:
			print('FAILED')

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# config.py
#
# Copyright 2011 - 2013 Patrick Ulbrich <zulu99@gmx.net>
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
import xdg.BaseDirectory as bd
from ConfigParser import RawConfigParser
from common.i18n import _

mailnag_defaults = {
	'general':
	{
		'check_interval'	: '5',
		'sender_format'		: '1',
		'playsound'		: '1',
		'soundfile'		: 'mailnag.ogg',
		'autostart'		: '1'
	},
	'filter':
	{
		'filter_enabled'	: '0',
		'filter_text'		: 'newsletter, viagra'
	},
	'script':
	{
		'script0_enabled'	: '0',
		'script1_enabled'	: '0',
		'script0_file'		: '',
		'script1_file'		: ''
	}
}

cfg_folder = os.path.join(bd.xdg_config_home, "mailnag")
cfg_file = os.path.join(cfg_folder, "mailnag.cfg")

def cfg_exists():
	return os.path.exists(cfg_file)


def read_cfg():
	cfg = RawConfigParser()
	cfg._sections = mailnag_defaults # HACK : use cfg.read_dict(mailnag_defaults) in python 3

	if os.path.exists(cfg_file):
		cfg.read(cfg_file)

	return cfg


def write_cfg(cfg):
	if not os.path.exists(cfg_folder):
		os.makedirs(cfg_folder)
	
	with open(cfg_file, 'wb') as configfile: cfg.write(configfile)

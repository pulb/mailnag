# Copyright 2011 - 2021 Patrick Ulbrich <zulu99@gmx.net>
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
from configparser import RawConfigParser

mailnag_defaults = {
	'core':
	{
		'poll_interval'		 : '10',
		'imap_idle_timeout'	 : '10',
		'mailbox_seen_flags' : '1',
		'autostart'			 : '1',
		'connectivity_test'	 : 'networkmonitor',
		'enabled_plugins'	 : 'dbusplugin, soundplugin, libnotifyplugin'
	}
}

cfg_folder = os.path.join(bd.xdg_config_home, "mailnag")
cfg_file = os.path.join(cfg_folder, "mailnag.cfg")

def cfg_exists():
	return os.path.exists(cfg_file)


def read_cfg():
	cfg = RawConfigParser()
	cfg.read_dict(mailnag_defaults)

	if os.path.exists(cfg_file):
		cfg.read(cfg_file)

	return cfg


def write_cfg(cfg):
	if not os.path.exists(cfg_folder):
		os.makedirs(cfg_folder)


	
	with open(cfg_file, 'w') as configfile:
		cfg.write(configfile)

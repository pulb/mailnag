# -*- coding: utf-8 -*-
#
# test_backends.py
#
# Copyright 2016 Timo Kankare <timo.kankare@iki.fi>
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

"""Test cases for account manager."""

from ConfigParser import RawConfigParser
from io import StringIO
import pytest

from Mailnag.backends import get_mailbox_parameter_specs
from Mailnag.common.accounts import AccountManager


sample_config_file = u"""
[account1]
enabled = 1
name = IMAP mailbox config
user = you
password =
server = imap.example.org
port =
ssl = 1
imap = 1
idle = 1
folder = []

[account2]
enabled = 1
name = POP3 mailbox config
user = me
password =
server = pop.example.org
port =
ssl = 1
imap = 0
idle = 0
folder = []

[account3]
enabled = 1
name = Empty account config for testing default values

[account4]
enabled = 1
name = Imap config with empty folder option
folder =

[account5]
enabled = 1
name = Imap config with old style folder option
folder = folderA, folderB, folderC

[account6]
enabled = 1
name = Imap config with json folder option
folder = folderA, folderB, folderC
"""

@pytest.fixture
def config():
	cp = RawConfigParser()
	cp.readfp(StringIO(sample_config_file), filename='sample_config_file')
	return cp


def test_imap_config_options(config):
	am = AccountManager()
	option_spec = get_mailbox_parameter_specs('imap')
	options = am._get_cfg_options(config, 'account1', option_spec)
	expected_options = {
		'user': 'you',
		'password': '',
		'server': 'imap.example.org',
		'port': '',
		'ssl': True,
		'imap': True,
		'idle': True,
		'folders': [],
	}
	assert expected_options == options


def test_imap_config_defaults(config):
	am = AccountManager()
	option_spec = get_mailbox_parameter_specs('imap')
	options = am._get_cfg_options(config, 'account3', option_spec)
	expected_options = {
		'user': '',
		'password': '',
		'server': '',
		'port': '',
		'ssl': True,
		'imap': True,
		'idle': True,
		'folders': [],
	}
	assert expected_options == options


def test_imap_empty_folder_option(config):
	am = AccountManager()
	option_spec = get_mailbox_parameter_specs('imap')
	options = am._get_cfg_options(config, 'account4', option_spec)
	assert options['folders'] == []


def test_imap_old_folder_option(config):
	am = AccountManager()
	option_spec = get_mailbox_parameter_specs('imap')
	options = am._get_cfg_options(config, 'account5', option_spec)
	assert options['folders'] == ['folderA', 'folderB', 'folderC']


def test_imap_new_folder_option(config):
	am = AccountManager()
	option_spec = get_mailbox_parameter_specs('imap')
	options = am._get_cfg_options(config, 'account6', option_spec)
	assert options['folders'] == ['folderA', 'folderB', 'folderC']


def test_pop3_config_options(config):
	am = AccountManager()
	option_spec = get_mailbox_parameter_specs('pop3')
	options = am._get_cfg_options(config, 'account2', option_spec)
	expected_options = {
		'user': 'me',
		'password': '',
		'server': 'pop.example.org',
		'port': '',
		'ssl': True,
		'imap': False,
		'idle': False,
	}
	assert expected_options == options


def test_pop3_config_defaults(config):
	am = AccountManager()
	option_spec = get_mailbox_parameter_specs('pop3')
	options = am._get_cfg_options(config, 'account3', option_spec)
	expected_options = {
		'user': '',
		'password': '',
		'server': '',
		'port': '',
		'ssl': True,
		'imap': False,
		'idle': False,
	}
	assert expected_options == options


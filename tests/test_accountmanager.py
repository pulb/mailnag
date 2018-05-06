# -*- coding: utf-8 -*-
#
# test_accountmanager.py
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
from Mailnag.common.credentialstore import CredentialStore


class FakeCredentialStore(CredentialStore):
	"""Helper class to be used in tests."""

	def __init__(self):
		self.secrets = {}

	def get(self, key):
		return self.secrets[key]

	def set(self, key, secret):
		self.secrets[key] = secret

	def remove(self, key):
		if key in self.secrets:
			del self.secrets[key]


sample_config_file = u"""
[account1]
enabled = 1
name = IMAP mailbox config
user = you
password = drowssap
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
password = poppoppop
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
folder = ["folderA", "folderB", "folderC"]
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
		'password': 'drowssap',
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
		'password': 'poppoppop',
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


def test_imap_config_values_should_be_stored():
	am = AccountManager()
	option_spec = get_mailbox_parameter_specs('imap')
	options = {
		'user': 'you',
		'password': '',
		'server': 'imap.example.org',
		'port': '',
		'ssl': True,
		'imap': True,
		'idle': True,
		'folders': ['a', 'b'],
	}
	config = RawConfigParser()
	config.add_section('account1')
	am._set_cfg_options(config, 'account1', options, option_spec)
	expected_config_items = [
		('user', 'you'),
		('password', ''),
		('server', 'imap.example.org'),
		('port', ''),
		('ssl', '1'),
		('imap', '1'),
		('idle', '1'),
		('folder', '["a", "b"]'),
	]
	assert set(expected_config_items) == set(config.items('account1'))


# Load from config

def get_account(accounts, name):
	"""Finds and returns account which has given name."""
	return next(account for account in accounts if account.name == name)


def test_load_from_config(config):
	am = AccountManager()
	am.load_from_cfg(config, enabled_only=False)
	accounts = am.to_list()
	assert len(accounts) == 6
	imap_account = get_account(am.to_list(), 'IMAP mailbox config')
	pop3_account = get_account(am.to_list(), 'POP3 mailbox config')
	assert imap_account.get_config()['password'] == 'drowssap'
	assert pop3_account.get_config()['password'] == 'poppoppop'


def test_load_from_config_with_credential_store(config):
	cs = FakeCredentialStore()
	cs.set('Mailnag password for imap://you@imap.example.org', 'verry seecret')
	cs.set('Mailnag password for pop://me@pop.example.org', 'seecret too')
	am = AccountManager(cs)
	am.load_from_cfg(config, enabled_only=False)
	accounts = am.to_list()
	assert len(accounts) == 6
	imap_account = get_account(am.to_list(), 'IMAP mailbox config')
	pop3_account = get_account(am.to_list(), 'POP3 mailbox config')
	assert imap_account.get_config()['password'] == 'verry seecret'
	assert pop3_account.get_config()['password'] == 'seecret too'


# Save to config

def test_save_zero_accounts_to_config(config):
	am = AccountManager()
	am.save_to_cfg(config)
	assert len(config.sections()) == 0


def test_save_all_accounts_to_config(config):
	am = AccountManager()
	am.load_from_cfg(config, enabled_only=False)
	am.save_to_cfg(config)
	assert len(config.sections()) == 6


def test_save_zero_accounts_to_config_with_credential_store(config):
	cs = FakeCredentialStore()
	am = AccountManager(cs)
	am.save_to_cfg(config)
	assert len(config.sections()) == 0
	assert cs.secrets == {}


def test_save_all_accounts_to_config_with_credential_store(config):
	cs = FakeCredentialStore()
	cs.set('Mailnag password for imap://you@imap.example.org', 'verry seecret')
	cs.set('Mailnag password for pop://me@pop.example.org', 'seecret too')
	am = AccountManager(cs)
	am.load_from_cfg(config, enabled_only=False)
	am.save_to_cfg(config)
	assert len(config.sections()) == 6
	assert cs.secrets == {
	    'Mailnag password for imap://@': '',
	    'Mailnag password for imap://you@imap.example.org': 'verry seecret',
	    'Mailnag password for pop://me@pop.example.org': 'seecret too'
	}


def test_save_removed_accounts_to_config_with_credential_store(config):
	cs = FakeCredentialStore()
	cs.set('Mailnag password for imap://you@imap.example.org', 'verry seecret')
	cs.set('Mailnag password for pop://me@pop.example.org', 'seecret too')
	am = AccountManager(cs)
	am.load_from_cfg(config, enabled_only=False)
	am.clear()
	am.save_to_cfg(config)
	assert len(config.sections()) == 0
	assert cs.secrets == {}


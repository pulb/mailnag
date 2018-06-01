# -*- coding: utf-8 -*-
#
# test_account.py
#
# Copyright 2016, 2018 Timo Kankare <timo.kankare@iki.fi>
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

"""Test cases for Account."""

from Mailnag.common.accounts import Account


def test_account_get_id_should_be_unique():
	accounts = [
		Account(name='a', mailbox_type='imap', enabled=True, user='x', server='xx'),
		Account(name='b', mailbox_type='pop3', enabled=True, user='y', server='yy'),
		Account(name='c', mailbox_type='mbox', enabled=True),
		Account(name='d', mailbox_type='maildir', enabled=True),
	]
	ids = set(acc.get_id() for acc in accounts)

	assert len(ids) == len(accounts)


def test_account_get_id_should_be_consistent():
	account = Account(name='a', mailbox_type='imap', enabled=True, user='x', server='xx')
	expected_id = account.get_id()
	for i in range(20):
		assert account.get_id() == expected_id


def test_account_should_keep_configuration():
	account = Account(enabled=True,
					  name='my name',
					  user='who',
					  password='secret',
					  oauth2string='who knows',
					  server='example.org',
					  port='1234',
					  ssl=True,
					  imap=True,
					  idle=True,
					  folders=['a', 'b'],
					  mailbox_type='mybox')
	config = account.get_config()
	expected_config = {
		'enabled': True,
		'name': 'my name',
		'user': 'who',
		'password': 'secret',
		'oauth2string': 'who knows',
		'server': 'example.org',
		'port': '1234',
		'ssl': True,
		'imap': True,
		'idle': True,
		'folders': ['a', 'b'],
		'mailbox_type': 'mybox',
	}
	assert expected_config == config


def test_account_should_store_configuration():
	new_config = {
		'user': 'who',
		'password': 'secret',
		'oauth2string': 'who knows',
		'server': 'example.org',
		'port': '1234',
		'ssl': True,
		'imap': True,
		'idle': True,
		'folders': ['a', 'b'],
	}
	account = Account()
	account.set_config(mailbox_type='mybox', name='my name', enabled=True, config=new_config)
	config = account.get_config()
	expected_config = {
		'enabled': True,
		'name': 'my name',
		'user': 'who',
		'password': 'secret',
		'oauth2string': 'who knows',
		'server': 'example.org',
		'port': '1234',
		'ssl': True,
		'imap': True,
		'idle': True,
		'folders': ['a', 'b'],
		'mailbox_type': 'mybox',
	}
	assert expected_config == config


def test_account_config_should_always_contain_certain_values():
	account = Account()
	config = account.get_config()
	assert 'enabled' in config
	assert 'name' in config
	assert 'mailbox_type' in config


def test_type_should_be_empty_by_default():
	account = Account()
	config = account.get_config()
	assert account.mailbox_type == ''
	assert config['mailbox_type'] == ''


def test_account_should_configurable_with_any_parameters():
	account = Account(weird='odd', odd='weird')
	config = account.get_config()
	assert config['weird'] == 'odd'
	assert config['odd'] == 'weird'


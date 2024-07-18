# -*- coding: utf-8 -*-
#
# test_account.py
#
# Copyright 2018, 2024 Timo Kankare <timo.kankare@iki.fi>
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

"""Test cases for MailSyncer."""

import pytest

import email
from Mailnag.daemon.mails import MailSyncer
from Mailnag.common.accounts import Account
from Mailnag.backends.base import MailboxBackend


class FakeBackend(MailboxBackend):
	"""Fake mailbox backend implementation for testing."""

	def __init__(self, **kw):
		self._opened = False
		self.messages = []


	def open(self):
		self._opened = True


	def close(self):
		self._opened = False


	def is_open(self):
		return self._opened


	def list_messages(self):
		for msg in self.messages:
			yield "samplefolder", msg, {}


	def mark_as_seen(self, mails):
		raise NotImplementedError


	def request_folders(self):
		raise NotImplementedError("no folder support")


	def notify_next_change(self, callback=None, timeout=None):
		raise NotImplementedError("no notification support")


	def cancel_notifications(self):
		raise NotImplementedError("no notification support")


class FakeAccount(Account):
	"""Fake account implementation to use special test backend."""

	def __init__(self, **kw):
		Account.__init__(self, **kw)
		self._backend = FakeBackend()


	def set_current_messages(self, messages):
		self._backend.messages = messages

message_template = """\
From: You <you@example.org>
To: Me <me@example.org>
Subject: Hello...
Message-ID: mid-{mid}
Date: Tue, 01 May 2018 16:28:08 +0300

...World!
"""

message_template_without_mid = """\
From: You <you@example.org>
To: Me <me@example.org>
Subject: Hello...
Date: Tue, 01 May 2018 16:28:08 +0300

...World!
"""


def make_messages(a, b):
	"""Make list of messages with message ids in range(a, b)."""
	make_msg = email.message_from_string
	return [make_msg(message_template.format(mid=i)) for i in range(a, b)]


def make_messages_without_mid():
	"""Make list of messages with message ids in range(a, b)."""
	return [message_template_without_mid]


def test_no_mails_with_no_accounts():
	syncer = MailSyncer([])
	accounts = []
	mails = syncer.sync(accounts)
	assert len(mails) == 0


def test_no_mails_in_an_account():
	syncer = MailSyncer([])
	account = FakeAccount()
	mails = syncer.sync([account])
	assert len(mails) == 0


def test_mails_in_an_account():
	syncer = MailSyncer([])
	account = FakeAccount()
	messages = make_messages(0, 10)
	account.set_current_messages(messages)
	mails = syncer.sync([account])
	assert len(mails) == 10


def test_syncing_account_multiple_times_should_not_affect():
	syncer = MailSyncer([])
	account = FakeAccount()
	messages = make_messages(0, 10)
	account.set_current_messages(messages)
	mails_in_first_sync = syncer.sync([account])
	mails_in_second_sync = syncer.sync([account])
	assert mails_in_first_sync == mails_in_second_sync


def test_syncing_should_remove_read_messages():
	syncer = MailSyncer([])
	account = FakeAccount()
	messages = make_messages(0, 10)
	account.set_current_messages(messages)
	mails_in_first_sync = syncer.sync([account])
	account.set_current_messages(messages[3:])
	mails_in_second_sync = syncer.sync([account])
	assert len(mails_in_second_sync) == 7
	assert all(mail in mails_in_first_sync for mail in mails_in_second_sync)


def test_syncing_should_add_new_messages():
	syncer = MailSyncer([])
	account = FakeAccount()
	messages = make_messages(0, 10)
	account.set_current_messages(messages)
	mails_in_first_sync = syncer.sync([account])
	new_messages = make_messages(10, 14)
	account.set_current_messages(messages + new_messages)
	mails_in_second_sync = syncer.sync([account])
	assert len(mails_in_second_sync) == 14
	assert all(mail in mails_in_second_sync for mail in mails_in_first_sync)


def test_syncing_should_update_messages():
	syncer = MailSyncer([])
	account = FakeAccount()
	messages = make_messages(0, 10)
	account.set_current_messages(messages)
	mails_in_first_sync = syncer.sync([account])
	new_messages = make_messages(10, 14)
	account.set_current_messages(messages[3:] + new_messages)
	mails_in_second_sync = syncer.sync([account])
	assert len(mails_in_second_sync) == 11


def test_syncing_without_account_should_keep_already_synced_messages():
	syncer = MailSyncer([])
	account = FakeAccount()
	messages = make_messages(0, 10)
	account.set_current_messages(messages)
	mails_in_first_sync = syncer.sync([account])
	mails_in_second_sync = syncer.sync([])
	assert mails_in_first_sync == mails_in_second_sync


def test_syncing_multiple_accounts_should_collect_all_messages():
	syncer = MailSyncer([])
	account1 = FakeAccount()
	account2 = FakeAccount()
	account3 = FakeAccount()
	account1.set_current_messages(make_messages(0, 10))
	account2.set_current_messages(make_messages(10, 20))
	account3.set_current_messages(make_messages(20, 30))
	mails = syncer.sync([account1, account2, account3])
	assert len(mails) == 30


def test_syncing_multiple_account_separately_should_collect_all_messages():
	syncer = MailSyncer([])
	# Note: Accounts are identified by user, server and folders attributes, 
	#       see Account.get_id()
	account1 = FakeAccount(name='1', user='a')
	account2 = FakeAccount(name='2', server='b')
	account3 = FakeAccount(name='3')
	account1.set_current_messages(make_messages(0, 10))
	account2.set_current_messages(make_messages(10, 20))
	account3.set_current_messages(make_messages(20, 30))
	syncer.sync([account1])
	syncer.sync([account2])
	mails = syncer.sync([account3])
	assert len(mails) == 30


def test_syncing_same_mail_twice_from_same_account():
	syncer = MailSyncer([])
	account = FakeAccount()
	messages1 = make_messages(0, 1)
	messages2 = make_messages(0, 1)
	account.set_current_messages(messages1 + messages2)
	mails = syncer.sync([account])
	assert len(mails) == 1


def test_syncing_same_mail_from_different_accounts():
	syncer = MailSyncer([])
	account1 = FakeAccount(name='1', user='a')
	account2 = FakeAccount(name='2', server='b')
	messages1 = make_messages(0, 1)
	messages2 = make_messages(0, 1)
	account1.set_current_messages(messages1)
	account2.set_current_messages(messages2)
	mails = syncer.sync([account1, account2])

	# Note: Is this ok, or should it list message in both accounts?
	assert len(mails) == 1


def test_syncing_with_messages_without_message_ids():
	syncer = MailSyncer([])
	account1 = FakeAccount(name='1', user='a')
	account2 = FakeAccount(name='2', server='b')
	account3 = FakeAccount(name='3')
	messages1 = make_messages_without_mid()
	messages2 = make_messages_without_mid()
	messages3 = make_messages_without_mid()
	account1.set_current_messages(messages1)
	account2.set_current_messages(messages2)
	account3.set_current_messages(messages3)
	mails = syncer.sync([account1, account2, account3])
	assert len(mails) == 3


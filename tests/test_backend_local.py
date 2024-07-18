# -*- coding: utf-8 -*-
#
# test_backend_local.py
#
# Copyright 2016, 2024 Timo Kankare <timo.kankare@iki.fi>
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

"""Tests for local backends."""

import mailbox
import pytest

from Mailnag.backends import create_backend


@pytest.fixture
def sample_path(tmpdir):
	"""Temporary path for mailbox used in tests."""
	return str(tmpdir.join('sample'))


class TestMBox:
	"""Tests for mbox backend."""

	@pytest.fixture(autouse=True)
	def sample_mbox(self, sample_path):
		"""Temporary mbox instance for tests."""
		return mailbox.mbox(sample_path, create=True)

	def test_create_mbox_backend(self):
		be = create_backend('mbox')
		assert be is not None

	def test_initially_mailbox_should_be_closed(self):
		be = create_backend('mbox')
		assert not be.is_open()

	def test_mailbox_should_be_open_when_opened(self, sample_path):
		be = create_backend('mbox', path=sample_path)
		be.open()
		assert be.is_open()

	def test_closed_mailbox_should_be_closed(self, sample_path):
		be = create_backend('mbox', path=sample_path)
		be.open()
		be.close()
		assert not be.is_open()

	def test_lists_no_messages_from_empty_mailbox(self, sample_path):
		be = create_backend('mbox', name='sample', path=sample_path)
		be.open()
		try:
			msgs = list(be.list_messages())
			assert len(msgs) == 0
		finally:
			be.close()

	def test_lists_unread_messages_from_mailbox(self, sample_path, sample_mbox):
		self._add_message(sample_mbox, 'blaa-blaa-1', '')
		self._add_message(sample_mbox, 'blaa-blaa-2', 'O')
		self._add_message(sample_mbox, 'blaa-blaa-3', 'RO')
		sample_mbox.close()

		be = create_backend('mbox', name='sample', path=sample_path)
		be.open()
		try:
			msgs = list(be.list_messages())
			folders = [folder for folder, msg, flags in msgs]
			msg_ids = set(msg.get('message-id') for folder, msg, flags in msgs)
		finally:
			be.close()
		assert len(msgs) == 2
		assert all(folder == '' for folder in folders)
		assert msg_ids == set(['blaa-blaa-1', 'blaa-blaa-2'])

	def test_mbox_should_not_have_folders(self, sample_path):
		be = create_backend('mbox', path=sample_path)
		be.open()
		with pytest.raises(NotImplementedError):
			be.request_folders()

	def test_mbox_does_not_support_notifications(self, sample_path):
		be = create_backend('mbox', path=sample_path)
		be.open()
		with pytest.raises(NotImplementedError):
			be.notify_next_change()
		with pytest.raises(NotImplementedError):
			be.cancel_notifications()

	def test_open_should_fail_if_mailbox_does_not_exist(self, tmpdir):
		path = str(tmpdir.join('not-exist'))

		be = create_backend('mbox', path=path)
		with pytest.raises(IOError):
			be.open()

	def _add_message(self, mbox, msg_id, flags):
		m = mailbox.mboxMessage()
		m.set_payload('Hello world!', 'ascii')
		m.add_header('from', 'me@example.org')
		m.add_header('to', 'you@example.org')
		m.add_header('subject', 'Hi!')
		m.add_header('message-id', msg_id)
		m.set_flags(flags)
		mbox.lock()
		try:
			mbox.add(m)
		finally:
			mbox.unlock()


class TestMaildir:
	"""Tests for maildir backend."""

	@pytest.fixture(autouse=True)
	def sample_maildir(self, sample_path):
		"""Temporary maildir instance for tests."""
		return mailbox.Maildir(sample_path, create=True)

	def test_create_maildir_backend(self):
		be = create_backend('maildir')
		assert be is not None

	def test_initially_mailbox_should_be_closed(self):
		be = create_backend('maildir')
		assert not be.is_open()

	def test_mailbox_should_be_open_when_opened(self, sample_path):
		be = create_backend('maildir', path=sample_path)
		be.open()
		assert be.is_open()

	def test_mailbox_should_be_closed(self, sample_path):
		be = create_backend('maildir', path=sample_path)
		be.open()
		be.close()
		assert not be.is_open()

	def test_lists_no_messages_from_empty_mailbox(self, sample_path):
		be = create_backend('maildir', name='sample', path=sample_path)
		be.open()
		try:
			msgs = list(be.list_messages())
			assert len(msgs) == 0
		finally:
			be.close()

	def test_lists_unread_messages_from_mailbox(self, sample_path, sample_maildir):
		self._add_message(sample_maildir, 'blaa-blaa-1', None, 'new')
		self._add_message(sample_maildir, 'blaa-blaa-2', None, 'cur')
		self._add_message(sample_maildir, 'blaa-blaa-3', 'S', 'cur')
		sample_maildir.close()

		be = create_backend('maildir', name='sample', path=sample_path)
		be.open()
		try:
			msgs = list(be.list_messages())
			folders = [folder for folder, msg, flags in msgs]
			msg_ids = set(msg.get('message-id') for folder, msg, flags in msgs)
		finally:
			be.close()
		assert len(msgs) == 2
		assert all(folder == '' for folder in folders)
		assert msg_ids == set(['blaa-blaa-1', 'blaa-blaa-2'])

	def test_lists_unread_messages_from_selected_folders(self, sample_path, sample_maildir):
		f = sample_maildir.add_folder('folder1')
		sample_maildir.add_folder('folder2')
		s = sample_maildir.add_folder('folder1.subfolder')
		self._add_message(sample_maildir, 'blaa-blaa-1', None, 'new')
		self._add_message(f, 'blaa-blaa-2', None, 'cur')
		self._add_message(s, 'blaa-blaa-3', None, 'cur')
		sample_maildir.close()

		be = create_backend('maildir', name='sample', path=sample_path, folders=['', 'folder1.subfolder'])
		be.open()
		try:
			msgs = list(be.list_messages())
			folders = [folder for folder, msg, flags in msgs]
			msg_ids = set(msg.get('message-id') for folder, msg, flags in msgs)
		finally:
			be.close()
		assert len(msgs) == 2
		assert set(['', 'folder1.subfolder']) == set(folders)
		assert msg_ids == set(['blaa-blaa-1', 'blaa-blaa-3'])

	def test_should_support_unicode_folder_names(self, sample_path, sample_maildir):
		"""Python2 maildir folders must be str, not unicode.
		However folder in Mailnag configuration is represented as a json
		list, and json.loads converts strings to unicode. This test is here
		to ensure that unicode folder names work.
		Note: This is probably not needed with Python3.
		"""
		f = sample_maildir.add_folder('folder1')
		self._add_message(f, 'blaa-blaa-2', 'S', 'cur')
		sample_maildir.close()

		be = create_backend('maildir', name='sample', path=sample_path, folders=['', 'folder1'])
		be.open()
		try:
			msgs = list(be.list_messages())
		finally:
			be.close()

	def test_folders_should_be_listed(self, sample_path, sample_maildir):
		sample_maildir.add_folder('folder1')
		sample_maildir.add_folder('folder2')
		sample_maildir.add_folder('folder1.subfolder')
		sample_maildir.close()

		be = create_backend('maildir', path=sample_path)
		be.open()
		folders = be.request_folders()
		assert set(['', 'folder1', 'folder2', 'folder1.subfolder']) == set(folders)

	def test_maildir_does_not_support_notifications(self, sample_path):
		be = create_backend('maildir', path=sample_path)
		be.open()
		with pytest.raises(NotImplementedError):
			be.notify_next_change()
		with pytest.raises(NotImplementedError):
			be.cancel_notifications()

	def test_open_should_fail_if_mailbox_does_not_exist(self, tmpdir):
		path = str(tmpdir.join('not-exist'))

		be = create_backend('maildir', path=path)
		with pytest.raises(IOError):
			be.open()

	def _add_message(self, maildir, msg_id, flags, subdir):
		m = mailbox.MaildirMessage()
		m.set_payload('Hello world!', 'ascii')
		m.add_header('from', 'me@example.org')
		m.add_header('to', 'you@example.org')
		m.add_header('subject', 'Hi!')
		m.add_header('message-id', msg_id)
		if flags:
			m.set_flags(flags)
		m.set_subdir(subdir)
		maildir.lock()
		try:
			maildir.add(m)
		finally:
			maildir.unlock()


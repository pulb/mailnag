# -*- coding: utf-8 -*-
#
# test_backend_local.py
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

"""Tests for local backends."""

import mailbox
import pytest

from Mailnag.backends import create_backend


# mbox tests

def test_create_mbox_backend():
	be = create_backend('mbox')
	assert be is not None


def test_initially_mailbox_should_be_closed():
	be = create_backend('mbox')
	assert not be.is_open()


def test_when_opened_mailbox_should_be_open(tmpdir):
	tmpdir.join('sample').write('')
	path = str(tmpdir.join('sample'))
	be = create_backend('mbox', path=path)
	be.open()
	assert be.is_open()


def test_closed_mailbox_should_be_closed(tmpdir):
	tmpdir.join('sample').write('')
	path = str(tmpdir.join('sample'))
	be = create_backend('mbox', path=path)
	be.open()
	be.close()
	assert not be.is_open()


def test_mbox_lists_no_messages_from_empty_mailbox(tmpdir):
	path = str(tmpdir.join('sample'))
	sample_mbox = mailbox.mbox(path, create=True)

	be = create_backend('mbox', name='sample', path=path)
	be.open()
	try:
		msgs = list(be.list_messages())
		assert len(msgs) == 0
	finally:
		be.close()


def test_mbox_lists_two_messages_from_mailbox(tmpdir):
	path = str(tmpdir.join('sample'))
	sample_mbox = mailbox.mbox(path, create=True)
	add_mbox_message(sample_mbox, 'blaa-blaa-1', '')
	add_mbox_message(sample_mbox, 'blaa-blaa-2', 'O')
	add_mbox_message(sample_mbox, 'blaa-blaa-3', 'RO')
	sample_mbox.close()

	be = create_backend('mbox', name='sample', path=path)
	be.open()
	try:
		msgs = list(be.list_messages())
		folders = [folder for folder, msg in msgs]
		msg_ids = set(msg.get('message-id') for folder, msg in msgs)
	finally:
		be.close()
	assert len(msgs) == 2
	assert all(folder == '' for folder in folders)
	assert msg_ids == set(['blaa-blaa-1', 'blaa-blaa-2'])


def test_mbox_should_not_have_folders(tmpdir):
	tmpdir.join('sample').write('')
	path = str(tmpdir.join('sample'))
	be = create_backend('mbox', path=path)
	be.open()
	with pytest.raises(NotImplementedError):
		be.request_folders()


def test_mbox_does_not_support_notifications(tmpdir): # for now
	tmpdir.join('sample').write('')
	path = str(tmpdir.join('sample'))
	be = create_backend('mbox', path=path)
	be.open()
	with pytest.raises(NotImplementedError):
		be.notify_next_change()
	with pytest.raises(NotImplementedError):
		be.cancel_notifications()


def test_mbox_open_should_fail_if_mailbox_does_not_exist(tmpdir):
	path = str(tmpdir.join('not-exist'))

	be = create_backend('mbox', path=path)
	with pytest.raises(IOError):
		be.open()


# maildir tests


def test_create_maildir_backend():
	be = create_backend('maildir')
	assert be is not None


def test_initially_maildir_should_be_closed():
	be = create_backend('maildir')
	assert not be.is_open()


def test_when_opened_maildir_should_be_open(tmpdir):
	path = str(tmpdir.join('sample'))
	sample_maildir = mailbox.Maildir(path, create=True)
	be = create_backend('maildir', path=path)
	be.open()
	assert be.is_open()


def test_closed_maildir_should_be_closed(tmpdir):
	path = str(tmpdir.join('sample'))
	sample_maildir = mailbox.Maildir(path, create=True)
	be = create_backend('maildir', path=path)
	be.open()
	be.close()
	assert not be.is_open()


def test_maildir_lists_no_messages_from_empty_mailbox(tmpdir):
	path = str(tmpdir.join('sample'))
	sample_maildir = mailbox.Maildir(path, create=True)

	be = create_backend('maildir', name='sample', path=path)
	be.open()
	try:
		msgs = list(be.list_messages())
		assert len(msgs) == 0
	finally:
		be.close()


def test_maildir_lists_two_messages_from_mailbox(tmpdir):
	path = str(tmpdir.join('sample'))
	sample_maildir = mailbox.Maildir(path, create=True)
	add_maildir_message(sample_maildir, 'blaa-blaa-1', '', 'new')
	add_maildir_message(sample_maildir, 'blaa-blaa-2', '', 'cur')
	add_maildir_message(sample_maildir, 'blaa-blaa-3', 'S', 'cur')
	sample_maildir.close()

	be = create_backend('maildir', name='sample', path=path)
	be.open()
	try:
		msgs = list(be.list_messages())
		folders = [folder for folder, msg in msgs]
		msg_ids = set(msg.get('message-id') for folder, msg in msgs)
	finally:
		be.close()
	assert len(msgs) == 2
	assert all(folder == '' for folder in folders)
	assert msg_ids == set(['blaa-blaa-1', 'blaa-blaa-2'])


def test_maildir_should_have_folders(tmpdir):
	path = str(tmpdir.join('sample'))
	sample_maildir = mailbox.Maildir(path, create=True)
	f = sample_maildir.add_folder('folder1')
	sample_maildir.add_folder('folder2')
	f.add_folder('subfolder')

	be = create_backend('maildir', path=path)
	be.open()
	folders = be.request_folders()
	assert set(['', 'folder1', 'folder2', 'folder1/subfolder']) == set(folders)


def test_maildir_does_not_support_notifications(tmpdir): # for now
	path = str(tmpdir.join('sample'))
	sample_maildir = mailbox.Maildir(path, create=True)
	be = create_backend('maildir', path=path)
	be.open()
	with pytest.raises(NotImplementedError):
		be.notify_next_change()
	with pytest.raises(NotImplementedError):
		be.cancel_notifications()


def test_maildir_open_should_fail_if_mailbox_does_not_exist(tmpdir):
	path = str(tmpdir.join('not-exist'))

	be = create_backend('maildir', path=path)
	with pytest.raises(IOError):
		be.open()



# Helper fuctions

def add_mbox_message(mbox, msg_id, flags):
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

def add_maildir_message(maildir, msg_id, flags, subdir):
	m = mailbox.MaildirMessage()
	m.set_payload('Hello world!', 'ascii')
	m.add_header('from', 'me@example.org')
	m.add_header('to', 'you@example.org')
	m.add_header('subject', 'Hi!')
	m.add_header('message-id', msg_id)
	m.set_flags(flags)
	m.set_subdir(subdir)
	maildir.lock()
	try:
		maildir.add(m)
	finally:
		maildir.unlock()


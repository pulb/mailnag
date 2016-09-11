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

from Mailnag.backends.local import MBoxBackend


def test_create_mbox_backend():
	be = MBoxBackend()
	assert be is not None


def test_initially_mailbox_should_be_closed():
	be = MBoxBackend()
	assert not be.is_open()


def test_when_opened_mailbox_should_be_open(tmpdir):
	tmpdir.join('sample').write('')
	path = str(tmpdir.join('sample'))
	be = MBoxBackend(path=path)
	be.open()
	assert be.is_open()


def test_closed_mailbox_should_be_closed(tmpdir):
	tmpdir.join('sample').write('')
	path = str(tmpdir.join('sample'))
	be = MBoxBackend(path=path)
	be.open()
	be.close()
	assert not be.is_open()


def test_mbox_lists_no_messages_from_empty_mailbox(tmpdir):
	path = str(tmpdir.join('sample'))
	sample_mbox = mailbox.mbox(path, create=True)

	be = MBoxBackend(name='sample', path=path)
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

	be = MBoxBackend(name='sample', path=path)
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
	be = MBoxBackend(path=path)
	be.open()
	assert be.request_folders() == []


def test_mbox_does_not_support_notifications(tmpdir): # for now
	tmpdir.join('sample').write('')
	path = str(tmpdir.join('sample'))
	be = MBoxBackend(path=path)
	be.open()
	with pytest.raises(NotImplementedError):
		be.notify_next_change()
	with pytest.raises(NotImplementedError):
		be.cancel_notifications()


def test_mbox_open_should_fail_if_mailbox_does_not_exist(tmpdir):
	path = str(tmpdir.join('not-exist'))

	be = MBoxBackend(path=path)
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


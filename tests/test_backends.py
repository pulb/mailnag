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

"""Test cases for backends."""

from Mailnag.backends import create_backend

def test_create_imap_backend():
	be = create_backend('imap', name='testing', user='nobody', password='', server='imap.example.org', port='', ssl=True, folders=['a', 'b'])
	assert be is not None
	assert not be.is_open()
	assert be.server == 'imap.example.org'

def test_create_imap_backend_with_defaults():
	be = create_backend('imap', name='testing')
	assert be is not None
	assert not be.is_open()
	assert be.server == ''

def test_create_imap_backend_should_ignore_unknown_setting():
	be = create_backend('imap', name='testing', odd='weird', weird='odd')
	assert be is not None


def test_create_pop3_backend():
	be = create_backend('pop3', name='testing', user='nobody', password='', server='pop.example.org', port='', ssl=True)
	assert be is not None
	assert not be.is_open()
	assert be.server == 'pop.example.org'

def test_create_pop3_backend_with_defaults():
	be = create_backend('pop3', name='testing')
	assert be is not None
	assert not be.is_open()
	assert be.server == ''

def test_create_pop3_backend_should_ignore_unknown_setting():
	be = create_backend('pop3', name='testing', odd='weird', weird='odd')
	assert be is not None


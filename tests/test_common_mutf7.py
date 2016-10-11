# -*- coding: utf-8 -*-
#
# test_account.py
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

"""Test cases for mutf7."""

from Mailnag.common.mutf7 import encode_mutf7, decode_mutf7

def test_encode():
	expected = 'Die Katzen &- die M&AOQ-use'
	result = encode_mutf7(u'Die Katzen & die Mäuse')
	assert expected == result

def test_decode():
	expected = u'Die Katzen & die Mäuse'
	result = decode_mutf7('Die Katzen &- die M&AOQ-use')
	assert expected == result


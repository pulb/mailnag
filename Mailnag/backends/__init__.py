# -*- coding: utf-8 -*-
#
# __init__.py
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

"""Backends to implement mail box specific functionality, like IMAP and POP3."""

from Mailnag.backends.imap import IMAPMailboxBackend
from Mailnag.backends.pop3 import POP3MailboxBackend

_backends = {
	'imap' : IMAPMailboxBackend,
	'pop3' : POP3MailboxBackend,
}

def create_backend(mailbox_type, name, **kw):
	"""Create mailbox backend of specified type, name and other parameters."""
	return _backends[mailbox_type](name, **kw)


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

from collections import namedtuple
import json
import re

from Mailnag.backends.imap import IMAPMailboxBackend
from Mailnag.backends.pop3 import POP3MailboxBackend
from Mailnag.backends.local import MBoxBackend, MaildirBackend
from Mailnag.backends.gmail_rss import GMailRssBackend
from Mailnag.common.utils import splitstr


def _str_to_folders(folders_str):
	if re.match(r'^\[.*\]$', folders_str):
		folders	= json.loads(folders_str)
	else:
		folders	= splitstr(folders_str, ',')
	return folders


def _folders_to_str(folders):
	return json.dumps(folders, ensure_ascii=False)


def _str_to_bool(string):
	return bool(int(string))


def _bool_to_str(b):
	return str(int(b))


Param = namedtuple('Param',
    ['param_name', 'option_name', 'from_str', 'to_str', 'default_value']
)
Backend = namedtuple('Backend', ['backend_class', 'params'])

_backends = {
	'imap' : Backend(IMAPMailboxBackend, [
				Param('user', 'user', str, str, ''),
				Param('password', 'password', str, str, ''),
				Param('server', 'server', str, str, ''),
				Param('port', 'port', str, str, ''),
				Param('ssl', 'ssl', _str_to_bool, _bool_to_str, True),
				Param('imap', 'imap', _str_to_bool, _bool_to_str, True),
				Param('idle', 'idle', _str_to_bool, _bool_to_str, True),
				Param('folders', 'folder', _str_to_folders, _folders_to_str, []),
			 ]),
	'pop3' : Backend(POP3MailboxBackend, [
				Param('user', 'user', str, str, ''),
				Param('password', 'password', str, str, ''),
				Param('server', 'server', str, str, ''),
				Param('port', 'port', str, str, ''),
				Param('ssl', 'ssl', _str_to_bool, _bool_to_str, True),
				Param('imap', 'imap', _str_to_bool, _bool_to_str, False),
				Param('idle', 'idle', _str_to_bool, _bool_to_str, False),
			 ]),
	'mbox' : Backend(MBoxBackend, [
				Param('path', 'path', str, str, ''),
			 ]),
	'maildir' : Backend(MaildirBackend, [
				Param('path', 'path', str, str, ''),
				Param('folders', 'folder', _str_to_folders, _folders_to_str, []),
			]),
        'gmail_rss' : Backend(GMailRssBackend, [
                		Param('gmail_labels', 'gmail_labels', _str_to_folders, _folders_to_str, []),
				Param('password', 'password', str, str, ''),
                	])
}

def create_backend(mailbox_type, **kw):
	"""Create mailbox backend of specified type and parameters."""
	return _backends[mailbox_type].backend_class(**kw)


def get_mailbox_parameter_specs(mailbox_type):
	"""Returns mailbox backend specific parameter specification.
	The specification is a list objects which have atributes:
	* param_name - the name of argument in which parameter value is given to
				   backend constructor
	* option_name - the name used in configuration
	* from_str - the function to convert string to parameter specific type
	* default_value - the value used when the option is not found
	"""
	return _backends[mailbox_type].params


# -*- coding: utf-8 -*-
#
# local.py
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

"""Implementation of local mailboxes, like mbox and maildir."""

import email
import mailbox
import logging
import os.path

from Mailnag.backends.base import MailboxBackend

class MBoxBackend(MailboxBackend):
	"""Implementation of mbox mail boxes."""
	
	def __init__(self, name = '', path=None, **kw):
		"""Initialize mbox mailbox backend with a name and path."""
		self.name = name
		self.path = path
		self.opened = False


	def open(self, reopen=False):
		"""'Open' mbox. (Actually just checks that mailbox file exists.)"""
		if not os.path.isfile(self.path):
			raise IOError('Mailbox {} does not exist.'.format(self.path))
		self.opened = True


	def close(self):
		"""Close mbox."""
		self.opened = False


	def is_open(self):
		"""Return True if mailbox is opened."""
		return self.opened


	def list_messages(self):
		"""List unread messages from the mailbox.
		Yields pairs (folder, message) where folder is always ''.
		"""
		mbox = mailbox.mbox(self.path, create=False)
		folder = ''
		try:
			for msg in mbox:
				if 'R' not in msg.get_flags():
					yield folder, msg
		finally:
			mbox.close()


	def request_folders(self):
		"""mbox does not suppoert folders."""
		raise NotImplementedError("mbox does not support folders")


	def notify_next_change(self, callback=None, timeout=None):
		raise NotImplementedError("mbox does not support notifications")


	def cancel_notifications(self):
		raise NotImplementedError("mbox does not support notifications")


class MaildirBackend(MailboxBackend):
	"""Implementation of maildir mail boxes."""

	def __init__(self, name = '', path=None, **kw):
		"""Initialize maildir mailbox backend with a name and path."""
		self.name = name
		self.path = path
		self.opened = False


	def open(self, reopen=False):
		"""'Open' mailbox. (Actually just checks that maildir directory exists.)"""
		if not os.path.isdir(self.path):
			raise IOError('Mailbox {} does not exist.'.format(self.path))
		self.opened = True


	def close(self):
		"""Close mailbox."""
		self.opened = False


	def is_open(self):
		"""Return True if mailbox is opened."""
		return self.opened


	def list_messages(self):
		"""List unread messages from the mailbox.
		Yields pairs (folder, message) where folder is always ''.
		"""
		maildir = mailbox.Maildir(self.path, factory=None, create=False)
		folder = ''
		try:
			for msg in maildir:
				if 'S' not in msg.get_flags():
					yield folder, msg
		finally:
			maildir.close()


	def request_folders(self):
		"""Lists folder from maildir recursively."""

		def list_folders(maildir, parent):
			for folder in  maildir.list_folders():
				this_folder = parent + folder
				yield this_folder
				for subfolder in list_folders(maildir.get_folder(folder), this_folder + '/'):
					yield subfolder

		maildir = mailbox.Maildir(self.path, factory=None, create=False)
		return [''] + list(list_folders(maildir, ''))


	def notify_next_change(self, callback=None, timeout=None):
		raise NotImplementedError("mbox does not support notifications")


	def cancel_notifications(self):
		raise NotImplementedError("mbox does not support notifications")


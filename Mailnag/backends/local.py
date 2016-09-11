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

class MBoxBackend:
	"""Implementation of mbox mail boxes."""
	
	def __init__(self, name = '', path=None):
		"""Initialize mbox mailbox backens with a name and path."""
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
		"""List folders in mailbox.
		This returns always empty list, because mbox does not support folders.
		"""
		lst = []
		return lst


	def notify_next_change(self, callback=None, timeout=None):
		raise NotImplementedError("mbox does not support notifications")


	def cancel_notifications(self):
		raise NotImplementedError("mbox does not support notifications")


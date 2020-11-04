# Copyright 2020 Patrick Ulbrich <zulu99@gmx.net>
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

"""Interface and base implementation for mailbox backends."""

from abc import ABCMeta, abstractmethod


class MailboxBackend(object, metaclass=ABCMeta):
	"""Interface for mailbox backends.

	Mailbox backend implements access to the specific type of mailbox.
	"""

	def __init__(self, **kw):
		"""Constructor should accept any kind of backend specific
		parameters.
		"""

	@abstractmethod
	def open(self):
		"""Opens the mailbox."""
		raise NotImplementedError

	@abstractmethod
	def close(self):
		"""Closes the mailbox."""
		raise NotImplementedError

	@abstractmethod
	def is_open(self):
		"""Returns true if mailbox is open."""
		raise NotImplementedError

	@abstractmethod
	def list_messages(self):
		"""Lists unseen messages from the mailbox for this account.
		Yields tuples (folder, message, flags) for every message.
		"""
		raise NotImplementedError

	@abstractmethod
	def request_folders(self):
		"""Returns list of folder names available in the mailbox.
		Raises an exceptions if mailbox does not support folders.
		"""
		raise NotImplementedError

	def supports_mark_as_seen(self):
		"""Returns True if mailbox supports flagging mails as seen."""
		# Default implementation
		return False

	@abstractmethod
	def mark_as_seen(self, mails):
		"""Asks mailbox to flag mails in the list as seen.
		This may raise an exception if mailbox does not support this action.
		"""
		raise NotImplementedError
		
	def supports_notifications(self):
		"""Returns True if mailbox supports notifications."""
		# Default implementation
		return False

	@abstractmethod
	def notify_next_change(self, callback=None, timeout=None):
		"""Asks mailbox to notify next change.
		Callback is called when new mail arrives or a mail is removed.
		This may raise an exception if mailbox does not support
		notifications.
		"""
		raise NotImplementedError

	@abstractmethod
	def cancel_notifications(self):
		"""Cancels notifications.
		This may raise an exception if mailbox does not support
		notifications.
		"""
		raise NotImplementedError


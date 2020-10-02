# Copyright 2013 - 2020 Andreas Angerer <andreas.angerer>
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

import os
import dbus
import threading
from Mailnag.common.plugins import Plugin
from Mailnag.common.i18n import _


class MarkAsReadPlugin(Plugin):
	def _mark_mail_as_read(self, mail_id):
		mails = self.controller._mailchecker._all_mails
		found = False
		for mail in mails:
			if mail_id == mail.id:
				found = True
				break
		if not found:
			self.controller._ensure_not_disposed()
			self.controller._memorizer.set_to_seen(mail_id)
			self.controller._memorizer.save()
			return
		backend = mail.account._get_backend()
		mailid = mail.strID
		conn = backend._conn
		if type(backend).__name__ == 'IMAPMailboxBackend':
			status, res = conn.uid("STORE", mailid, "+FLAGS", "(\Seen)")
		self.controller._ensure_not_disposed()
		self.controller._memorizer.set_to_seen(mail_id)
		self.controller._memorizer.save()
		

	
	def _mark_mail_as_read_bak(self, mail_id, mail):
		self.controller._ensure_not_disposed()
		self.controller._memorizer.set_to_seen(mail_id)
		self.controller._memorizer.save()

	def enable(self):
		self.controller = self.get_mailnag_controller()
		self.controller.mark_mail_as_read = self._mark_mail_as_read

	
	def disable(self):
		self.controller.mark_mail_as_read = self._mark_mail_as_read_bak

	
	def get_manifest(self):
		return (_("MarkAsReadPlugin"),
				_("Marks mails as read on the IMAP server upon clicking them away."),
				"1.0",
				"Andreas Angerer")


	def get_default_config(self):
		return {}
	
	
	def has_config_ui(self):
		return False

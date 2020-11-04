# Copyright 2013 - 2020 Patrick Ulbrich <zulu99@gmx.net>
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

import dbus
import dbus.service
import logging
from Mailnag.common.dist_cfg import DBUS_BUS_NAME, DBUS_OBJ_PATH
from Mailnag.common.exceptions import InvalidOperationException

MAX_INT32 = ((0xFFFFFFFF // 2) - 1)


# DBUS server that exports Mailnag signals and methods 
class DBusService(dbus.service.Object):
	def __init__(self, mailnag_daemon):
		self._mails = []
		self._daemon = mailnag_daemon
		bus_name = dbus.service.BusName(DBUS_BUS_NAME, bus = dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, DBUS_OBJ_PATH)
	

	@dbus.service.signal(dbus_interface = DBUS_BUS_NAME, signature = 'aa{sv}aa{sv}')
	def MailsAdded(self, new_mails, all_mails):
		pass
	
	
	@dbus.service.signal(dbus_interface = DBUS_BUS_NAME, signature = 'aa{sv}')
	def MailsRemoved(self, remaining_mails):
		pass
	
		
	@dbus.service.method(dbus_interface = DBUS_BUS_NAME, out_signature = 'aa{sv}')
	def GetMails(self):
		return self._mails
		
	
	@dbus.service.method(dbus_interface = DBUS_BUS_NAME, out_signature = 'u')
	def GetMailCount(self):
		return len(self._mails)


	@dbus.service.method(dbus_interface = DBUS_BUS_NAME)
	def Shutdown(self):
		try:
			self._daemon.shutdown()
		except InvalidOperationException:
			pass
	
	
	@dbus.service.method(dbus_interface = DBUS_BUS_NAME)
	def CheckForMails(self):
		try:
			self._daemon.check_for_mails()
		except InvalidOperationException:
			pass


	@dbus.service.method(dbus_interface = DBUS_BUS_NAME, in_signature = 's')
	def MarkMailAsRead(self, mail_id):
		self._mails = [m for m in self._mails if m['id'] != mail_id]
		try:
			self._daemon.mark_mail_as_read(mail_id)
		except InvalidOperationException:
			pass
			
	
	def signal_mails_added(self, new_mails, all_mails):
		conv_new_mails = self._convert_mails(new_mails)
		conv_all_mails = self._convert_mails(all_mails)
		self._mails = conv_all_mails
		self.MailsAdded(conv_new_mails, conv_all_mails)
		
		
	def signal_mails_removed(self, remaining_mails):
		conv_remaining_mails = self._convert_mails(remaining_mails)
		self._mails = conv_remaining_mails
		self.MailsRemoved(conv_remaining_mails)
	
		
	def _convert_mails(self, mails):
		converted_mails = []
		for m in mails:
			d = {}
			name, addr = m.sender
			
			if m.datetime > MAX_INT32:
				logging.warning('dbusservice: datetime out of range (mailnag dbus api uses int32 timestamps).')
				datetime = 0
			else:
				datetime = m.datetime
			
			d['datetime'] = datetime			# int32 (i)
			d['subject'] = m.subject			# string (s)
			d['sender_name'] = name				# string (s)
			d['sender_addr'] = addr				# string (s)
			d['account_name'] = m.account.name	# string (s)
			d['id'] = m.id						# string (s)
			
			converted_mails.append(d)
		
		return converted_mails

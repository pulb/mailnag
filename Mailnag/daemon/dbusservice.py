#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dbusservice.py
#
# Copyright 2013 Patrick Ulbrich <zulu99@gmx.net>
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

# DBUS server that exports mailnag signals end methods 
class DBUSService(dbus.service.Object):
	def __init__(self):
		self._mails = []
		bus_name = dbus.service.BusName('mailnag.MailnagService', bus = dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, '/mailnag/MailnagService')
	
	
	def set_mails(self, mails):
		self._mails = mails
	
	
	@dbus.service.signal(dbus_interface = 'mailnag.MailnagService', signature = 'u')
	def MailsAdded(self, new_count):
		pass
	
	
	@dbus.service.signal(dbus_interface = 'mailnag.MailnagService', signature = 'u')
	def MailsRemoved(self, new_count):
		pass
	
		
	@dbus.service.method(dbus_interface = 'mailnag.MailnagService', out_signature = 'aa{sv}')
	def GetMails(self):
		mails = []
		for m in self._mails:
			d = {}
			d['datetime'] = m.datetime	# int32 (i)
			d['subject'] = m.subject	# string (s)
			d['sender'] = m.sender		# string (s)
			d['id'] = m.id				# string (s)

			mails.append(d)
		
		return mails
	
	
	@dbus.service.method(dbus_interface = 'mailnag.MailnagService', out_signature = 'u')
	def GetMailCount(self):
		return len(self._mails)

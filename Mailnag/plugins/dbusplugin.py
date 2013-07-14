#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# dbusplugin.py
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
from common.dist_cfg import DBUS_BUS_NAME, DBUS_OBJ_PATH
from common.plugins import Plugin, HookTypes

plugin_defaults = {}


class DBusPlugin(Plugin):
	def __init__(self):
		self._dbusservice = None
		self._mails_added_hook = None
		self._mails_removed_hook = None

	
	def enable(self):
		controller = self.get_mailnag_controller()
		self._dbusservice = DBusService(controller)
		
		def mails_added_hook(all_mails, new_mail_count):
			self._dbusservice.set_mails(all_mails)
			self._dbusservice.MailsAdded(new_mail_count)
		
		def mails_removed_hook(remaining_mails):
			self._dbusservice.set_mails(remaining_mails)
			self._dbusservice.MailsRemoved(len(remaining_mails))
		
		self._mails_added_hook = mails_added_hook
		self._mails_removed_hook = mails_removed_hook
		
		controller.hooks.register_hook_func(HookTypes.MAILS_ADDED, 
			self._mails_added_hook)
		controller.hooks.register_hook_func(HookTypes.MAILS_REMOVED, 
			self._mails_removed_hook)
		
	
	def disable(self):
		self._dbusservice = None
		controller = self.get_mailnag_controller()
		
		if self._mails_added_hook != None:
			controller.hooks.unregister_hook_func(HookTypes.MAILS_ADDED,
				self._mails_added_hook)
			self._mails_added_hook = None
		
		if self._mails_removed_hook != None:
			controller.hooks.unregister_hook_func(HookTypes.MAILS_REMOVED,
				self._mails_removed_hook)
			self._mails_removed_hook = None

	
	def get_manifest(self):
		return ("DBus Service",
				"Exposes Mailnag's functionality via a DBus service.",
				"1.0",
				"Patrick Ulbrich <zulu99@gmx.net>",
				True)


	def get_default_config(self):
		return plugin_defaults
	
	
	def has_config_ui(self):
		return False
	
	
	def get_config_ui(self):
		return None
	
	
	def load_ui_from_config(self, config_ui):
		pass
	
	
	def save_ui_to_config(self, config_ui):
		pass


# DBUS server that exports Mailnag signals end methods 
class DBusService(dbus.service.Object):
	def __init__(self, mailnag_controller):
		self._mails = []
		self._mailnag_controller = mailnag_controller
		bus_name = dbus.service.BusName(DBUS_BUS_NAME, bus = dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, DBUS_OBJ_PATH)
	
	
	def set_mails(self, mails):
		self._mails = mails
	
	
	@dbus.service.signal(dbus_interface = DBUS_BUS_NAME, signature = 'u')
	def MailsAdded(self, new_count):
		pass
	
	
	@dbus.service.signal(dbus_interface = DBUS_BUS_NAME, signature = 'u')
	def MailsRemoved(self, new_count):
		pass
	
		
	@dbus.service.method(dbus_interface = DBUS_BUS_NAME, out_signature = 'aa{sv}')
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
	
	
	@dbus.service.method(dbus_interface = DBUS_BUS_NAME, out_signature = 'u')
	def GetMailCount(self):
		return len(self._mails)


	@dbus.service.method(dbus_interface = DBUS_BUS_NAME)
	def Shutdown(self):
		self._mailnag_controller.shutdown()

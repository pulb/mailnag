#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# libnotifyplugin.py
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
import threading
from gi.repository import Notify, Gio
from common.plugins import Plugin, HookTypes
from common.i18n import _
from common.utils import start_subprocess
from daemon.mails import sort_mails

NOTIFICATION_MODE_SINGLE = '0'
NOTIFICATION_MODE_SUMMARY = '1'

plugin_defaults = { 'notification_mode' : NOTIFICATION_MODE_SUMMARY }


class LibNotifyPlugin(Plugin):
	def __init__(self):
		# prevent flooding of the messaging tray
		self.MAIL_LIST_LIMIT = 10
		
		# dict that tracks all notifications that need to be closed
		self._notifications = {}
		self._initialized = False
		self._lock = threading.Lock()
		self._notification_server_wait_event = threading.Event()
		self._notification_server_ready = False
		self._mails_added_hook = None
		self._mails_removed_hook = None
		
	
	def enable(self):
		self._notification_server_wait_event.clear()
		self._notification_server_ready = False
		self._notifications = {}
		
		# initialize Notification
		if not self._initialized:
			Notify.init("Mailnag")
			self._initialized = True
		
		def mails_added_hook(new_mails, all_mails):
			self._notify_async(new_mails, all_mails)
		
		def mails_removed_hook(remaining_mails):
			if remaining_mails == 0:
				# no mails (e.g. email client has been launched) -> close notifications
				self._close_notifications()
		
		self._mails_added_hook = mails_added_hook
		self._mails_removed_hook = mails_removed_hook
		
		controller = self.get_mailnag_controller()
		
		controller.hooks.register_hook_func(HookTypes.MAILS_ADDED, 
			self._mails_added_hook)
		controller.hooks.register_hook_func(HookTypes.MAILS_REMOVED, 
			self._mails_removed_hook)
		
	
	def disable(self):
		controller = self.get_mailnag_controller()
		
		if self._mails_added_hook != None:
			controller.hooks.unregister_hook_func(HookTypes.MAILS_ADDED,
				self._mails_added_hook)
			self._mails_added_hook = None
		
		if self._mails_removed_hook != None:
			controller.hooks.unregister_hook_func(HookTypes.MAILS_REMOVED,
				self._mails_removed_hook)
			self._mails_removed_hook = None
		
		# Abort possible notification server wait
		self._notification_server_wait_event.set()
		# Close all open notifications 
		# (must be called after _notification_server_wait_event.set() 
		# to prevent a possible deadlock)
		self._close_notifications()

	
	def get_manifest(self):
		return (_("LibNotify notifications"),
				_("Shows a popup when new mails arrive."),
				"1.0",
				"Patrick Ulbrich <zulu99@gmx.net>",
				False)


	def get_default_config(self):
		return plugin_defaults
	
	
	def has_config_ui(self):
		return False
	
	
	def get_config_ui(self):
		# TODO : Add ui to specify the
		# notification mode.
		return None
	
	
	def load_ui_from_config(self, config_ui):
		pass
	
	
	def save_ui_to_config(self, config_ui):
		pass


	def _notify_async(self, new_mails, all_mails):
		def thread():
			with self._lock:
				# The desktop session may have started Mailnag 
				# before the libnotify dbus daemon.
				if not self._notification_server_ready:
					if not self._wait_for_notification_server():
						return
					self._notification_server_ready = True
			
				config = self.get_config()
				if config['notification_mode'] == NOTIFICATION_MODE_SINGLE:
					self._notify_single(new_mails)
				else:
					self._notify_summary(all_mails)
		
		t = threading.Thread(target = thread)
		t.start()
	
	
	def _notify_summary(self, mails):
		summary = ""		
		body = ""
		
		if len(self._notifications) == 0:
			self._notifications['0'] = self._get_notification(" ", None, None) # empty string will emit a gtk warning

		ubound = len(mails) if len(mails) <= self.MAIL_LIST_LIMIT else self.MAIL_LIST_LIMIT

		for i in range(ubound):
			body += mails[i].sender + ":\n<i>" + mails[i].subject + "</i>\n\n"

		if len(mails) > self.MAIL_LIST_LIMIT:
			body += "<i>" + _("(and {0} more)").format(str(len(mails) - self.MAIL_LIST_LIMIT)) + "</i>"

		if len(mails) > 1: # multiple new emails
			summary = _("You have {0} new mails.").format(str(len(mails)))
		else:
			summary = _("You have a new mail.")

		self._notifications['0'].update(summary, body, "mail-unread")
		self._notifications['0'].show()
	
	
	def _notify_single(self, mails):
		# In single notification mode new mails are
		# added to the *bottom* of the notification list.
		mails = sort_mails(mails, sort_desc = False)
		
		for mail in mails:
			n = self._get_notification(mail.sender, mail.subject, "mail-unread")
			notification_id = str(id(n))
			# n.add_action("mark-as-read", _("Mark as read"), self._notification_action_handler, (mail, notification_id), None)			
			n.show()
			self._notifications[notification_id] = n


	def _close_notifications(self):
		with self._lock:
			for n in self._notifications.itervalues():
				n.close()
			self._notifications = {}
	
	
	def _get_notification(self, summary, body, icon):
		n = Notify.Notification.new(summary, body, icon)		
		n.set_category("email")
		n.add_action("default", "default", self._notification_action_handler, None, None)

		return n
	
	
	def _wait_for_notification_server(self):
		bus = dbus.SessionBus()
		while not bus.name_has_owner('org.freedesktop.Notifications'):
			self._notification_server_wait_event.wait(5)
			if self._notification_server_wait_event.is_set():
				return False
		return True

	
	def _notification_action_handler(self, n, action, user_data):
		with self._lock:
			if action == "default":
				mailclient = get_default_mail_reader()
				if mailclient != None:
					start_subprocess(mailclient)

				# clicking the notification bubble has closed all notifications
				# so clear the reference array as well. 
				self._notifications = {}
		
		
def get_default_mail_reader():
	mail_reader = None
	app_info = Gio.AppInfo.get_default_for_type ("x-scheme-handler/mailto", False)

	if app_info != None:
		executable = Gio.AppInfo.get_executable(app_info)

		if (executable != None) and (len(executable) > 0):
			mail_reader = executable

	return mail_reader


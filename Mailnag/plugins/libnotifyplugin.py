# Copyright 2013 - 2019 Patrick Ulbrich <zulu99@gmx.net>
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

import gi

gi.require_version('Notify', '0.7')
gi.require_version('GLib', '2.0')
gi.require_version('Gtk', '3.0')

import os
import dbus
import threading
from gi.repository import Notify, Gio, Gtk
from Mailnag.common.plugins import Plugin, HookTypes
from Mailnag.common.i18n import _
from Mailnag.common.subproc import start_subprocess
from Mailnag.common.exceptions import InvalidOperationException

NOTIFICATION_MODE_COUNT			= '0'
NOTIFICATION_MODE_SHORT_SUMMARY	= '3'
NOTIFICATION_MODE_SUMMARY		= '1'
NOTIFICATION_MODE_SINGLE		= '2'

plugin_defaults = { 
	'notification_mode' : NOTIFICATION_MODE_SHORT_SUMMARY,
	'max_visible_mails' : '10'
}


class LibNotifyPlugin(Plugin):
	def __init__(self):
		# dict that tracks all notifications that need to be closed
		self._notifications = {}
		self._initialized = False
		self._lock = threading.Lock()
		self._notification_server_wait_event = threading.Event()
		self._notification_server_ready = False
		self._is_gnome = False
		self._mails_added_hook = None
		
	
	def enable(self):
		self._max_mails = int(self.get_config()['max_visible_mails'])
		self._notification_server_wait_event.clear()
		self._notification_server_ready = False
		self._notifications = {}
		
		# initialize Notification
		if not self._initialized:
			Notify.init("Mailnag")
			self._is_gnome = 'GDMSESSION' in os.environ and \
				(os.environ['GDMSESSION'] == 'gnome')
			self._initialized = True
		
		def mails_added_hook(new_mails, all_mails):
			self._notify_async(new_mails, all_mails)
		
		self._mails_added_hook = mails_added_hook
		
		controller = self.get_mailnag_controller()
		hooks = controller.get_hooks()
		
		hooks.register_hook_func(HookTypes.MAILS_ADDED, 
			self._mails_added_hook)
		
	
	def disable(self):
		controller = self.get_mailnag_controller()
		hooks = controller.get_hooks()
		
		if self._mails_added_hook != None:
			hooks.unregister_hook_func(HookTypes.MAILS_ADDED,
				self._mails_added_hook)
			self._mails_added_hook = None
		
		# Abort possible notification server wait
		self._notification_server_wait_event.set()
		# Close all open notifications 
		# (must be called after _notification_server_wait_event.set() 
		# to prevent a possible deadlock)
		self._close_notifications()

	
	def get_manifest(self):
		return (_("LibNotify Notifications"),
				_("Shows a popup when new mails arrive."),
				"1.1.1",
				"Patrick Ulbrich <zulu99@gmx.net>",
				False)


	def get_default_config(self):
		return plugin_defaults
	
	
	def has_config_ui(self):
		return True
	
	
	def get_config_ui(self):
		radio_mapping = [
			(NOTIFICATION_MODE_COUNT,				Gtk.RadioButton(label = _('Count of new mails'))),
			(NOTIFICATION_MODE_SHORT_SUMMARY,		Gtk.RadioButton(label = _('Short summary of new mails'))),
			(NOTIFICATION_MODE_SUMMARY,				Gtk.RadioButton(label = _('Detailed summary of new mails'))),
			(NOTIFICATION_MODE_SINGLE,				Gtk.RadioButton(label = _('One notification per new mail')))
		]

		box = Gtk.Box()
		box.set_spacing(12)
		box.set_orientation(Gtk.Orientation.VERTICAL)
		
		label = Gtk.Label()
		label.set_markup('<b>%s</b>' % _('Notification mode:'))
		label.set_alignment(0.0, 0.0)
		box.pack_start(label, False, False, 0)
		
		inner_box = Gtk.Box()
		inner_box.set_spacing(6)
		inner_box.set_orientation(Gtk.Orientation.VERTICAL)
		
		last_radio = None
		for m, r in radio_mapping:
			if last_radio != None:
				r.join_group(last_radio)
			inner_box.pack_start(r, False, False, 0)
			last_radio = r
		
		alignment = Gtk.Alignment()
		alignment.set_padding(0, 6, 18, 0)
		alignment.add(inner_box)
		box.pack_start(alignment, False, False, 0)
		
		box._radio_mapping = radio_mapping
		
		return box
	
	
	def load_ui_from_config(self, config_ui):
		config = self.get_config()		
		radio = [ r for m, r in config_ui._radio_mapping if m == config['notification_mode'] ][0]
		radio.set_active(True)
	
	
	def save_ui_to_config(self, config_ui):
		config = self.get_config()
		mode = [ m for m, r in config_ui._radio_mapping if r.get_active() ] [0]
		config['notification_mode'] = mode


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
				if config['notification_mode'] == NOTIFICATION_MODE_COUNT:
					self._notify_count(len(all_mails))
				elif config['notification_mode'] == NOTIFICATION_MODE_SHORT_SUMMARY:
					self._notify_short_summary(new_mails, all_mails)
				elif config['notification_mode'] == NOTIFICATION_MODE_SUMMARY:
					self._notify_summary(new_mails, all_mails)
				else:
					self._notify_single(new_mails)
					
		
		t = threading.Thread(target = thread)
		t.start()
	
	
	def _notify_short_summary(self, new_mails, all_mails):
		summary = ""
		body = ""
		lst = []
		mails = self._prepend_new_mails(new_mails, all_mails)
		mail_count = len(mails)
		
		if len(self._notifications) == 0:
			self._notifications['0'] = self._get_notification(" ", None, None) # empty string will emit a gtk warning
		
		i = 0
		n = 0
		while (n < 3) and (i < mail_count):
			s = self._get_sender(mails[i])
			if s not in lst:
				lst.append(s)
				n += 1
			i += 1
		
		if self._is_gnome:
			senders = "<i>%s</i>" % ", ".join(lst)
		else:
			senders = ", ".join(lst)
		
		if mail_count > 1:
			summary = _("{0} new mails").format(str(mail_count))
			if (mail_count - i) > 1:
				body = _("from {0} and others.").format(senders)
			else:
				body = _("from {0}.").format(senders)
		else:
			summary = _("New mail")
			body = _("from {0}.").format(senders)
		
		self._notifications['0'].update(summary, body, "mail-unread")
		self._notifications['0'].show()
		
	
	def _notify_summary(self, new_mails, all_mails):
		summary = ""		
		body = ""
		mails = self._prepend_new_mails(new_mails, all_mails)
		
		if len(self._notifications) == 0:
			self._notifications['0'] = self._get_notification(" ", None, None) # empty string will emit a gtk warning

		ubound = len(mails) if len(mails) <= self._max_mails else self._max_mails

		for i in range(ubound):
			if self._is_gnome:
				body += "%s:\n<i>%s</i>\n\n" % (self._get_sender(mails[i]), mails[i].subject)
			else:
				body += "%s  -  %s\n" % (ellipsize(self._get_sender(mails[i]), 20), ellipsize(mails[i].subject, 20))

		if len(mails) > self._max_mails:
			if self._is_gnome:
				body += "<i>%s</i>" % _("(and {0} more)").format(str(len(mails) - self._max_mails))
			else:
				body += _("(and {0} more)").format(str(len(mails) - self._max_mails))

		if len(mails) > 1: # multiple new emails
			summary = _("{0} new mails").format(str(len(mails)))
		else:
			summary = _("New mail")

		self._notifications['0'].update(summary, body, "mail-unread")
		self._notifications['0'].show()
	
	
	def _notify_single(self, mails):
		# In single notification mode new mails are
		# added to the *bottom* of the notification list.
		mails.sort(key = lambda m: m.datetime, reverse = False)
		
		for mail in mails:
			n = self._get_notification(self._get_sender(mail), mail.subject, "mail-unread")
			notification_id = str(id(n))
			if self._is_gnome:
				n.add_action("mark-as-read", _("Mark as read"), 
					self._notification_action_handler, (mail, notification_id))			
			n.show()
			self._notifications[notification_id] = n


	def _notify_count(self, count):
		if len(self._notifications) == 0:
			self._notifications['0'] = self._get_notification(" ", None, None) # empty string will emit a gtk warning
		
		if count > 1: # multiple new emails
			summary = _("{0} new mails").format(str(count))
		else:
			summary = _("New mail")
		
		self._notifications['0'].update(summary, None, "mail-unread")
		self._notifications['0'].show()
	
	
	def _close_notifications(self):
		with self._lock:
			for n in self._notifications.values():
				n.close()
			self._notifications = {}
	
	
	def _get_notification(self, summary, body, icon):
		n = Notify.Notification.new(summary, body, icon)		
		n.set_category("email")
		n.set_hint_string("desktop-entry", "mailnag")
		
		if self._is_gnome:
			n.add_action("default", "default", self._notification_action_handler, None)

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
			elif action == "mark-as-read":
				controller = self.get_mailnag_controller()
				try:
					controller.mark_mail_as_read(user_data[0].id)
				except InvalidOperationException:
					pass
				
				# clicking the action has closed the notification
				# so remove its reference.
				del self._notifications[user_data[1]]
	

	def _get_sender(self, mail):
		name, addr = mail.sender
		if len(name) > 0: return name
		else: return addr
	
	
	def _prepend_new_mails(self, new_mails, all_mails):
		# The mail list (all_mails) is sorted by date (mails with most recent 
		# date on top). New mails with no date or older mails that come in 
		# delayed won't be listed on top. So if a mail with no or an older date 
		# arrives, it gives the impression that the top most mail (i.e. the mail 
		# with the most recent date) is re-notified.
		# To fix that, simply put new mails on top explicitly.  
		return new_mails + [m for m in all_mails if m not in new_mails]


def get_default_mail_reader():
	mail_reader = None
	app_info = Gio.AppInfo.get_default_for_type ("x-scheme-handler/mailto", False)

	if app_info != None:
		executable = Gio.AppInfo.get_executable(app_info)

		if (executable != None) and (len(executable) > 0):
			mail_reader = executable

	return mail_reader


def ellipsize(str, max_len):
	if max_len < 3: max_len = 3
	if len(str) <= max_len:
		return str
	else:
		return str[0:max_len - 3] + '...'

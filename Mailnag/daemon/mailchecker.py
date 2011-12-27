#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mailchecker.py
#
# Copyright 2011 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2011 Ralf Hersel <ralf.hersel@gmx.net>
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

from gi.repository import Notify
import threading
import sys
import subprocess
import os
import time

from common.utils import get_data_file, gstplay, get_default_mail_reader
from common.i18n import _
from daemon.reminder import Reminder
from daemon.mails import Mails
from daemon.pid import Pid

class MailChecker:
	def __init__(self, cfg, accounts):
		self.MAIL_LIST_LIMIT = 10 # prevent flooding of the messaging tray
		self.firstcheck = True; # first check after startup
		self.mailcheck_lock = threading.Lock()
		self.mails = Mails(cfg, accounts)
		self.reminder = Reminder()
		self.pid = Pid()
		self.cfg = cfg
		# dict that tracks all notifications that need to be closed
		self.notifications = {}
		
		self.reminder.load()
		Notify.init(cfg.get('general', 'messagetray_label')) # initialize Notification		
		

	def check(self):
		with self.mailcheck_lock:
			print 'Checking email accounts at:', time.asctime()
			self.pid.kill() # kill all zombies	

			self.mail_list = self.mails.get_mail('desc') # get all mails from all inboxes
		
			unseen_mails = []
			new_mails = []
		
			script_data = ""
			script_data_mailcount = 0
			
			for mail in self.mail_list:
				if self.reminder.contains(mail.id): # mail was fetched before
					if self.reminder.unseen(mail.id): # mail was not marked as seen
						unseen_mails.append(mail)
						if self.firstcheck:
							new_mails.append(mail)
				
				else: # mail is fetched the first time
					unseen_mails.append(mail)
					new_mails.append(mail)
					script_data += ' "<%s> %s"' % (mail.sender, mail.subject)
					script_data_mailcount += 1
			
			script_data = str(script_data_mailcount) + script_data
		
			if len(self.mail_list) == 0:
				 # no mails (e.g. email client has been launched) -> close notifications
				for n in self.notifications.itervalues():
					n.close()
				self.notifications = {}
			elif len(new_mails) > 0:
				if self.cfg.get('general', 'notification_mode') == '1':
					self.__notify_summary(unseen_mails)
				else:
					self.__notify_single(new_mails)

				if self.cfg.get('general', 'playsound') == '1': # play sound?
					gstplay(get_data_file(self.cfg.get('general', 'soundfile')))

			self.reminder.save(self.mail_list)
			self.firstcheck = False
			
		self.__run_user_scripts("on_mail_check", script_data) # process user scripts
		
		sys.stdout.flush() # write stdout to log file
		return True


	def __notify_summary(self, unseen_mails):
		summary = ""		
		body = ""

		if len(self.notifications) == 0:
			self.notifications['0'] = self.__get_notification(" ", None, None) # empty string will emit a gtk warning
		
		ubound = len(unseen_mails) if len(unseen_mails) <= self.MAIL_LIST_LIMIT else self.MAIL_LIST_LIMIT
		
		for i in range(ubound):
			body += unseen_mails[i].sender + ":\n<i>" + unseen_mails[i].subject + "</i>\n\n"
		
		if len(unseen_mails) > self.MAIL_LIST_LIMIT:
			body += "<i>" + _("(and {0} more)").format(str(len(unseen_mails) - self.MAIL_LIST_LIMIT)) + "</i>"

		if len(unseen_mails) > 1: # multiple new emails
			summary = _("You have {0} new mails.").format(str(len(unseen_mails)))
		else:
			summary = _("You have a new mail.")

		self.notifications['0'].update(summary, body, "mail-unread")
		self.notifications['0'].show()

	
	def __notify_single(self, new_mails):
		for mail in new_mails:
			n = self.__get_notification(mail.sender, mail.subject, "mail-unread")
			notification_id = str(id(n))
			n.add_action("mark-as-read", _("Mark as read"), self.__notification_action_handler, (mail, notification_id), None)			
			n.show()
			self.notifications[notification_id] = n


	def __get_notification(self, summary, body, icon):
		n = Notify.Notification.new(summary, body, icon)		
		n.set_category("email")
		n.add_action("default", "default", self.__notification_action_handler, None, None)

		return n
	

	def __notification_action_handler(self, n, action, user_data):
		with self.mailcheck_lock:
			if action == "default":
				mailclient = get_default_mail_reader()
				if mailclient != None:
					self.pid.append(subprocess.Popen(mailclient))
				
				# clicking the notification bubble has closed all notifications
				# so clear the reference array as well. 
				self.notifications = {}
			
			elif action == "mark-as-read":
				self.reminder.set_to_seen(user_data[0].id)
				self.reminder.save(self.mail_list)

				# clicking the action has closed the notification
				# so remove its reference
				del self.notifications[user_data[1]]


	def clear(self):
		with self.mailcheck_lock:
			# mark all mails to seen
			for mail in self.mail_list:
				self.reminder.set_to_seen(mail.id)
			self.reminder.save(self.mail_list)
		
			# close all notifications
			for n in self.notifications.itervalues():
				n.close()
			self.notifications = {}
		
			self.mail_list = []
	
	
	def __run_user_scripts(self, event, data):
		if event == "on_mail_check":
			if self.cfg.get('script', 'script0_enabled') == '1':
				script_file = self.cfg.get('script', 'script0_file')
				if script_file != '' and os.path.exists(script_file):
					self.pid.append(subprocess.Popen("%s %s" % (script_file, data), shell = True))
				else:
					print 'Warning: cannot execute script:', script_file
		
			if (data != '0') and (self.cfg.get('script', 'script1_enabled') == '1'):
				script_file = self.cfg.get('script', 'script1_file')
				if script_file != '' and os.path.exists(script_file):
					self.pid.append(subprocess.Popen("%s %s" % (script_file, data), shell = True))
				else:
					print 'Warning: cannot execute script:', script_file


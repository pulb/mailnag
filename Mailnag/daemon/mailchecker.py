#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mailchecker.py
#
# Copyright 2011 - 2013 Patrick Ulbrich <zulu99@gmx.net>
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

import threading
import sys
import subprocess
import os
import time

from common.utils import get_data_file, is_online
from common.i18n import _
from daemon.reminder import Reminder
from daemon.mailsyncer import MailSyncer
from daemon.pid import Pid

class MailChecker:
	def __init__(self, cfg, dbusservice):
		self._firstcheck = True; # first check after startup
		self._mailcheck_lock = threading.Lock()
		self._mailsyncer = MailSyncer(cfg)
		self._reminder = Reminder()
		self._dbusservice = dbusservice
		self._pid = Pid()
		self._cfg = cfg
		
		self._reminder.load()
		
	
	def check(self, accounts):
		# make sure multiple threads (idler and polling thread) 
		# don't check for mails simultaneously.
		with self._mailcheck_lock:
			print 'Checking %s email account(s) at: %s' % (len(accounts), time.asctime())
			# kill all zombies
			self._pid.kill()

			if not is_online():
				print 'Error: No internet connection'
				return
			
			all_mails = self._mailsyncer.sync(accounts)
			unseen_mails = []
			new_mail_count = 0
		
			script_data = ""
			script_data_mailcount = 0
			
			for mail in all_mails:
				if self._reminder.contains(mail.id): # mail was fetched before
					if self._reminder.unseen(mail.id): # mail was not marked as seen
						unseen_mails.append(mail)
						if self._firstcheck:
							new_mail_count += 1
				
				else: # mail is fetched the first time
					unseen_mails.append(mail)
					new_mail_count += 1
					script_data += ' "<%s> %s"' % (mail.sender, mail.subject)
					script_data_mailcount += 1
			
			script_data = str(script_data_mailcount) + script_data
			
			self._dbusservice.set_mails(unseen_mails)
			# TODO : signal MailsRemoved if not all mails have been removed
			# (i. e. if mailcount has been decreased)
			if len(all_mails) == 0:
				self._dbusservice.MailsRemoved(0)
			elif new_mail_count > 0:
				self._dbusservice.MailsAdded(new_mail_count)
			
			self._reminder.save(all_mails)
			# process user scripts
			self._run_user_scripts("on_mail_check", script_data)
			# write stdout to log file
			sys.stdout.flush()
			self._firstcheck = False
		
		return

			
	def _run_user_scripts(self, event, data):
		if event == "on_mail_check":
			if self._cfg.get('script', 'script0_enabled') == '1':
				script_file = self._cfg.get('script', 'script0_file')
				if script_file != '' and os.path.exists(script_file):
					self._pid.append(subprocess.Popen("%s %s" % (script_file, data), shell = True))
				else:
					print 'Warning: cannot execute script:', script_file
		
			if (data != '0') and (self._cfg.get('script', 'script1_enabled') == '1'):
				script_file = self._cfg.get('script', 'script1_file')
				if script_file != '' and os.path.exists(script_file):
					self._pid.append(subprocess.Popen("%s %s" % (script_file, data), shell = True))
				else:
					print 'Warning: cannot execute script:', script_file


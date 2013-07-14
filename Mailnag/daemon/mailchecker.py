#!/usr/bin/env python2
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
import time
import traceback

from common.utils import is_online
from common.i18n import _
from common.plugins import HookTypes
from daemon.reminder import Reminder
from daemon.mailsyncer import MailSyncer


def try_call(f, err_retval = None):
	try:
		return f()
	except:
		traceback.print_exc()
		return err_retval

			
class MailChecker:
	def __init__(self, cfg, hookreg):
		self._firstcheck = True # first check after startup
		self._mailcheck_lock = threading.Lock()
		self._mailsyncer = MailSyncer(cfg)
		self._reminder = Reminder()
		self._hookreg = hookreg
		
		self._reminder.load()
		
	
	def check(self, accounts):
		# make sure multiple threads (idler and polling thread) 
		# don't check for mails simultaneously.
		with self._mailcheck_lock:
			print 'Checking %s email account(s) at: %s' % (len(accounts), time.asctime())
			
			for f in self._hookreg.get_hook_funcs(HookTypes.MAIL_CHECK):
				try_call( f )
				
			if not is_online():
				print 'Error: No internet connection'
				return
			
			all_mails = self._mailsyncer.sync(accounts)
			unseen_mails = []
			new_mail_count = 0
			
			for mail in all_mails:
				if self._reminder.contains(mail.id): # mail was fetched before
					if self._reminder.unseen(mail.id): # mail was not marked as seen
						unseen_mails.append(mail)
						if self._firstcheck:
							new_mail_count += 1
				
				else: # mail is fetched the first time
					unseen_mails.append(mail)
					new_mail_count += 1
			
			# apply filter plugin hooks
			for f in self._hookreg.get_hook_funcs(HookTypes.FILTER_MAILS):
				unseen_mails = try_call( lambda: f(unseen_mails), unseen_mails )
			
			# TODO : signal MailsRemoved if not all mails have been removed
			# (i.e. if mailcount has been decreased)
			if len(all_mails) == 0:
				for f in self._hookreg.get_hook_funcs(HookTypes.MAILS_REMOVED):
					try_call( lambda: f(unseen_mails) )	
			elif new_mail_count > 0:
				for f in self._hookreg.get_hook_funcs(HookTypes.MAILS_ADDED):
					try_call( lambda: f(unseen_mails, new_mail_count) )
			
			self._reminder.save(all_mails)
			
			# write stdout to log file
			sys.stdout.flush()
			self._firstcheck = False
		
		return

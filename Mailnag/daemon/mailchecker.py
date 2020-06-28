# Copyright 2011 - 2020 Patrick Ulbrich <zulu99@gmx.net>
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
import logging

from Mailnag.common.utils import try_call
from Mailnag.common.i18n import _
from Mailnag.common.plugins import HookTypes
from Mailnag.daemon.mails import MailSyncer


class MailChecker:
	def __init__(self, cfg, memorizer, hookreg, conntest, dbus_service):
		self._firstcheck = True # first check after startup
		self._mailcheck_lock = threading.Lock()
		self._mailsyncer = MailSyncer(cfg)
		self._memorizer = memorizer
		self._hookreg = hookreg
		self._conntest = conntest
		self._dbus_service = dbus_service
		self._count_on_last_check = 0
		
	
	def check(self, accounts):
		# make sure multiple threads (idler and polling thread) 
		# don't check for mails simultaneously.
		with self._mailcheck_lock:
			logging.info('Checking %s email account(s).' % len(accounts))
			
			for f in self._hookreg.get_hook_funcs(HookTypes.MAIL_CHECK):
				try_call( f )
				
			if self._conntest.is_offline():
				logging.warning('No internet connection.')
				return
			
			all_mails = self._mailsyncer.sync(accounts)
			unseen_mails = []
			new_mails = []
			
			for mail in all_mails:
				if self._memorizer.contains(mail.id): # mail was fetched before
					if self._memorizer.is_unseen(mail.id): # mail was not marked as seen
						unseen_mails.append(mail)
						if self._firstcheck:
							new_mails.append(mail)
				
				else: # mail is fetched the first time
					unseen_mails.append(mail)
					new_mails.append(mail)
			
			self._memorizer.sync(all_mails)
			self._memorizer.save()
			self._firstcheck = False
			
			# apply filter plugin hooks
			filtered_unseen_mails = unseen_mails
			for f in self._hookreg.get_hook_funcs(HookTypes.FILTER_MAILS):
				filtered_unseen_mails = try_call( lambda: f(filtered_unseen_mails), filtered_unseen_mails )
			
			filtered_new_mails = [m for m in new_mails if m in filtered_unseen_mails]
			
			if len(filtered_new_mails) > 0:
				self._dbus_service.signal_mails_added(filtered_new_mails, filtered_unseen_mails)
				
				for f in self._hookreg.get_hook_funcs(HookTypes.MAILS_ADDED):
					try_call( lambda: f(filtered_new_mails, filtered_unseen_mails) )
			elif len(filtered_unseen_mails) != self._count_on_last_check:
				self._dbus_service.signal_mails_removed(filtered_unseen_mails)
				
				for f in self._hookreg.get_hook_funcs(HookTypes.MAILS_REMOVED):
					try_call( lambda: f(filtered_unseen_mails) )
			
			self._count_on_last_check = len(filtered_unseen_mails)
		
		return

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mailsyncer.py
#
# Copyright 2012 Patrick Ulbrich <zulu99@gmx.net>
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

from daemon.mails import Mails

class MailSyncer:
	def __init__(self, cfg):
		self._cfg = cfg
		self._mails_by_account = {}
		self._mail_list = []
	
	
	def sync(self, accounts):
		needs_rebuild = False
		
		# get mails from given accounts
		rcv_lst = Mails(self._cfg, accounts).get_mail()
	
		# group received mails by account
		tmp = {}
		for acc in accounts:
			tmp[acc.get_id()] = {}
		for mail in rcv_lst:
			tmp[mail.account_id][mail.id] = mail
	
		# compare current mails against received mails
		# and remove those that are gone (probably opened in mail client).
		for acc_id in self._mails_by_account.iterkeys():
			if acc_id in tmp:
				del_ids = []
				for mail_id in self._mails_by_account[acc_id].iterkeys():
					if not (mail_id in tmp[acc_id]):
						del_ids.append(mail_id)
						needs_rebuild = True
				for mail_id in del_ids:
					del self._mails_by_account[acc_id][mail_id]
	
		# compare received mails against current mails
		# and add new mails.
		for acc_id in tmp:
			if not (acc_id in self._mails_by_account):
				self._mails_by_account[acc_id] = {}
			for mail_id in tmp[acc_id]:
				if not (mail_id in self._mails_by_account[acc_id]):
					self._mails_by_account[acc_id][mail_id] = tmp[acc_id][mail_id]
					needs_rebuild = True
		
		# rebuild and sort mail list
		if needs_rebuild:
			self._mail_list = []
			for acc_id in self._mails_by_account:
				for mail_id in self._mails_by_account[acc_id]:
					self._mail_list.append(self._mails_by_account[acc_id][mail_id])
			self._mail_list = Mails.sort_mails(self._mail_list, 'desc')
		
		return self._mail_list

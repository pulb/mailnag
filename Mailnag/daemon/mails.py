# Copyright 2011 - 2021 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2020 Andreas Angerer
# Copyright 2016, 2018 Timo Kankare <timo.kankare@iki.fi>
# Copyright 2011 Leighton Earl <leighton.earl@gmx.com>
# Copyright 2011 Ralf Hersel <ralf.hersel@gmx.net>
# Copyright 2019 razer <razerraz@free.fr>
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

import time
import email
import os
import logging
import hashlib

from email.header import decode_header, make_header
from Mailnag.common.i18n import _
from Mailnag.common.config import cfg_folder


#
# Mail class
#
class Mail:
	def __init__(self, datetime, subject, sender, id, account, flags):
		self.datetime = datetime
		self.subject = subject
		self.sender = sender
		self.account = account
		self.id = id
		self.flags = flags


#
# MailCollector class
#
class MailCollector:
	def __init__(self, cfg, accounts):
		self._cfg = cfg
		self._accounts = accounts
		
		
	def collect_mail(self, sort = True):
		mail_list = []
		mail_ids = {}
		
		for acc in self._accounts:
			# open mailbox for this account
			try:
				if not acc.is_open():
					acc.open()
			except Exception as ex:
				logging.error("Failed to open mailbox for account '%s' (%s)." % (acc.name, ex),
					      exc_info=True)
				continue

			try:
				for folder, msg, flags in acc.list_messages():
					sender, subject, datetime, msgid = self._get_header(msg)
					id = self._get_id(msgid, acc, folder, sender, subject, datetime)
					# Discard mails with identical IDs (caused
					# by mails with a non-unique fallback ID,
					# i.e. mails received in the same folder with
					# identical sender and subject but *no datetime*,
					# see _get_id()).
					# Also filter duplicates caused by Gmail labels.
					if id not in mail_ids:
						mail_list.append(Mail(datetime, subject, \
							sender, id, acc, flags))
						mail_ids[id] = None
			except Exception as ex:
				# Catch exceptions here, so remaining accounts will still be checked 
				# if a specific account has issues.
				#
				# Re-throw the exception for accounts that support notifications (i.e. imap IDLE),
				# so the calling idler thread can handle the error and reset the connection if needed (see idlers.py).
				# NOTE: Idler threads always check single accounts (i.e. len(self._accounts) == 1), 
				#       so there are no remaining accounts to be checked for now.
				if acc.supports_notifications():
					raise
				else:
					logging.error("An error occured while processing mails of account '%s' (%s)." % (acc.name, ex), exc_info=True)
			finally:
				# leave account with notifications open, so that it can
				# send notifications about new mails
				if not acc.supports_notifications():
					# disconnect from Email-Server
					acc.close()

			
		# sort mails
		if sort:
			mail_list.sort(key = lambda m: m.datetime, reverse = True)
		
		return mail_list


	def _get_header(self, msg_dict):
		# Get sender
		sender = ('', '')
		
		try:
			content = self._get_header_field(msg_dict, 'From')
			# get the two parts of the sender
			addr = email.utils.parseaddr(content)
			
			if len(addr) != 2:
				logging.warning('Malformed sender field in message.')
			else:
				sender_real = self._convert(addr[0])
				sender_addr = self._convert(addr[1])
			
				sender = (sender_real, sender_addr)
		except:
			pass

		# Get subject
		try:
			content = self._get_header_field(msg_dict, 'Subject')
			subject = self._convert(content)
		except:
			subject = _('No subject')
		
		# Get date
		try:
			content = self._get_header_field(msg_dict, 'Date')
			
			# make a 10-tupel (UTC)
			parsed_date = email.utils.parsedate_tz(content)
			# convert 10-tupel to seconds incl. timezone shift
			datetime = email.utils.mktime_tz(parsed_date)
		except:
			logging.warning('Email date set to zero.')
			datetime = 0
		
		# Get message id
		try:
			msgid = self._get_header_field(msg_dict, 'Message-ID')
		except:
			msgid = ''
		
		return (sender, subject, datetime, msgid)
	
	
	def _get_header_field(self, msg_dict, key):
		if key in msg_dict:
			value = msg_dict[key]
		elif key.lower() in msg_dict:
			value = msg_dict[key.lower()]
		else:
			logging.debug("Couldn't get %s from message." % key)
			raise KeyError
		
		return value


	# return utf-8 decoded string from multi-part/multi-charset header text
	def _convert(self, text):
		decoded = decode_header(text)
		if not decoded[0][1] or 'unknown' in decoded[0][1]:
			decoded = [(decoded[0][0], 'latin-1')]
		return str(make_header(decoded))


	def _get_id(self, msgid, acc, folder, sender, subject, datetime):
		if len(msgid) > 0:
			id = hashlib.md5(msgid.encode('utf-8')).hexdigest()
		else:
			# Fallback ID. 
			# Note: mails received on the same server, 
			# in the same folder with identical sender and 
			# subject but *no datetime* will have the same hash id, 
			# i.e. only the first mail is notified. 
			# (Should happen very rarely).
			id = hashlib.md5((acc.get_id() + folder +
				sender[1] + subject + str(datetime))
				.encode('utf-8')).hexdigest()
		
		return id


#
# MailSyncer class
#
class MailSyncer:
	def __init__(self, cfg):
		self._cfg = cfg
		self._mails_by_account = {}
		self._mail_list = []
	
	
	def sync(self, accounts):
		needs_rebuild = False
		
		# collect mails from given accounts
		rcv_lst = MailCollector(self._cfg, accounts).collect_mail(sort = False)
		
		# group received mails by account
		tmp = {}
		for acc in accounts:
			tmp[acc.get_id()] = {}
		for mail in rcv_lst:
			tmp[mail.account.get_id()][mail.id] = mail
	
		# compare current mails against received mails
		# and remove those that are gone (probably opened in mail client).
		for acc_id in self._mails_by_account.keys():
			if acc_id in tmp:
				del_ids = []
				for mail_id in self._mails_by_account[acc_id].keys():
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
			self._mail_list.sort(key = lambda m: m.datetime, reverse = True)
		
		return self._mail_list


#
# Memorizer class
#
class Memorizer(dict):
	def __init__(self):
		dict.__init__(self)
		self._changed = False
	
	
	def load(self):
		self.clear()
		self._changed = False
		
		# load last known messages from mailnag.dat
		dat_file = os.path.join(cfg_folder, 'mailnag.dat')
		
		if os.path.exists(dat_file):
			with open(dat_file, 'r') as f:
				for line in f:
					# remove CR at the end
					stripedline = line.strip()
					# get all items from one line in a list: [mailid, seen_flag]
					pair = stripedline.split(',')
					# add to dict [id : flag]
					self[pair[0]] = pair[1]

	
	# save mail ids to a file
	def save(self, force = False):
		if (not self._changed) and (not force):
			return
		
		if not os.path.exists(cfg_folder):
			os.makedirs(cfg_folder)
		
		dat_file = os.path.join(cfg_folder, 'mailnag.dat')
		with open(dat_file, 'w') as f:
			for id, seen_flag in list(self.items()):
				line = id + ',' + seen_flag + '\n'
				f.write(line)

		self._changed = False


	def sync(self, mail_list):
		for m in mail_list:
			if not m.id in self:
				# new mail is not yet known to the memorizer
				self[m.id] = '0'
				self._changed = True
		
		for id in list(self.keys()):
			found = False
			for m in mail_list:			
				if id == m.id:
					found = True
					# break inner for loop
					break
			if not found:
				del self[id]
				self._changed = True
	
	
	# check if mail id is in the memorizer list
	def contains(self, id):
		return (id in self)


	# set seen flag for this email
	def set_to_seen(self, id):
		self[id] = '1'
		self._changed = True


	def is_unseen(self, id):
		if id in self:
			flag = self[id]
			return (flag == '0')
		else:
			return True

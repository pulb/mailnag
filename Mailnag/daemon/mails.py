#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# mails.py
#
# Copyright 2011 - 2016 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2011 Leighton Earl <leighton.earl@gmx.com>
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

import time
import email
import os
import logging
import hashlib

from email.header import decode_header
from Mailnag.common.i18n import _
from Mailnag.common.config import cfg_folder


#
# Mail class
#
class Mail:
	def __init__(self, datetime, subject, sender, id, account):
		self.datetime = datetime
		self.subject = subject
		self.sender = sender
		self.account_name = account.name
		self.account_id = account.get_id()
		self.id = id


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
			# open mailbox for  this account
			try:
				acc.open(reopen = False)
			except Exception as ex:
				logging.error("Failed to open mailbox for account '%s' (%s)." % (acc.name, ex))
				continue

			for folder, msg in acc.list_messages():
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
						sender, id, acc))
					mail_ids[id] = None

			# don't close idle connections
			if not acc.idle:
				# disconnect from Email-Server
				acc.close()
		
		# sort mails
		if sort:
			mail_list = sort_mails(mail_list, sort_desc = True)
		
		return mail_list


	def _get_header(self, msg_dict):
		try:
			content = self._get_header_field(msg_dict, 'From')
			sender = self._format_header_field('sender', content)
		except:
			sender = ('', '')

		try:
			content = self._get_header_field(msg_dict, 'Subject')
		except:
			content = _('No subject')
		try:
			subject = self._format_header_field('subject', content)
		except:
			subject = ''
		
		try:
			content = self._get_header_field(msg_dict, 'Date')
			datetime = self._format_header_field('date', content)
		except:
			logging.warning('Email date set to zero.')
			datetime = 0
			
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

	
	# format sender, date, subject etc.
	def _format_header_field(self, field_name, content):
		if field_name == 'sender':
			# get the two parts of the sender
			sender_real, sender_addr = email.utils.parseaddr(content)
			sender_real = self._convert(sender_real)
			sender_addr = self._convert(sender_addr)
			# create decoded tupel
			return (sender_real, sender_addr)

		if field_name == 'date':
			# make a 10-tupel (UTC)
			parsed_date = email.utils.parsedate_tz(content)
			# convert 10-tupel to seconds incl. timezone shift
			return email.utils.mktime_tz(parsed_date)

		if field_name == 'subject':
			return self._convert(content)


	# decode and concatenate multi-coded header parts
	def _convert(self, raw_content):
		# replace newline by space
		content = raw_content.replace('\n',' ')
		# workaround a bug in email.header.decode_header()
		content = content.replace('?==?','?= =?')
		# list of (text_part, charset) tupels
		tupels = decode_header(content)
		content_list = []
		# iterate trough parts
		for text, charset in tupels:
			# set default charset for decoding
			if charset == None: charset = 'latin-1'
			# replace non-decodable chars with 'nothing'
			content_list.append(text.decode(charset, 'ignore'))
		
		# insert blanks between parts
		decoded_content = u' '.join(content_list)
		# get rid of whitespace
		decoded_content = decoded_content.strip()

		return decoded_content


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
			id = hashlib.md5((acc.server + folder + acc.user + 
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
			self._mail_list = sort_mails(self._mail_list, sort_desc = True)
		
		return self._mail_list


#
# sort_mails function
#
def sort_mails(mail_list, sort_desc = False):
	sort_list = []
	for mail in mail_list:
		sort_list.append([mail.datetime, mail])
	
	# sort asc
	sort_list.sort()
	if sort_desc:
		sort_list.reverse()

	# recreate mail_list
	mail_list = []
	for mail in sort_list:
		mail_list.append(mail[1])
	return mail_list


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
			for id, seen_flag in self.items():
				line = id + ',' + seen_flag + '\n'
				f.write(line)

		self._changed = False


	def sync(self, mail_list):
		for m in mail_list:
			if not m.id in self:
				# new mail is not yet known to the memorizer
				self[m.id] = '0'
				self._changed = True
		
		for id in self.keys():
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

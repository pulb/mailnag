#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mailnag.py
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

import poplib
import imaplib
import urllib2
import ConfigParser
import os
import subprocess
import pynotify
#import indicate
import gobject
import gtk
import time
import email
from email.header import decode_header
import sys
#import locale
import gettext
from mailnag_config import Keyring
#import cairo
import signal


gettext.bindtextdomain('mailnag', 'locale')
gettext.textdomain('mailnag')
_ = gettext.gettext

# Accounts and Account =================================================
class Account:
	def __init__(self, name, server, user, password, imap, folder, port):
		self.name = name
		self.server = server
		self.user = user
		self.password = password
		self.imap = imap												# int
		self.folder = folder
		self.port = port
		self.mail_count = 0


	def get_connection(self):											# get email server connection
		if self.imap:													# IMAP
			try:
				try:
					if self.port == '':
						srv = imaplib.IMAP4_SSL(self.server)			# SSL
					else:
						srv = imaplib.IMAP4_SSL(self.server, self.port)
				except:
					if self.port == '':
						srv = imaplib.IMAP4(self.server)				# non SSL
					else:
						srv = imaplib.IMAP4(self.server, self.port)
				srv.login(self.user, self.password)
			except:
				print "Warning: Cannot connect to IMAP account: %s. " \
					"Next try in 30 seconds." % self.server
				time.sleep(30)											# wait 30 seconds
				try:
					try:
						if self.port == '':
							srv = imaplib.IMAP4_SSL(self.server)		# SSL
						else:
							srv = imaplib.IMAP4_SSL(self.server, self.port)
					except:
						if self.port == '':
							srv = imaplib.IMAP4(self.server)			# non SSL
						else:
							srv = imaplib.IMAP4(self.server, self.port)
					srv.login(self.user, self.password)
				except:
					frequency = cfg.get('account', 'frequency')			# get email check frequency
					print "Error: Cannot connect to IMAP account: %s. " \
						"Next try in %s minutes." % (self.server, frequency)
					srv = False
		else:															# POP
			try:
				try:
					if self.port == '':
						srv = poplib.POP3_SSL(self.server)				# connect to Email-Server via SSL
					else:
						srv = poplib.POP3_SSL(self.server, self.port)
				except:
					if self.port == '':
						srv = poplib.POP3(self.server)					# non SSL
					else:
						srv = poplib.POP3(self.server, self.port)
				srv.getwelcome()
				srv.user(self.user)
				srv.pass_(self.password)
			except:
				print "Warning: Cannot connect to POP account: %s. " \
					"Next try in 30 seconds." % self.server
				time.sleep(30)											# wait 30 seconds
				try:
					try:
						if self.port == '':
							srv = poplib.POP3_SSL(self.server)			# try it again
						else:
							srv = poplib.POP3_SSL(self.server, self.port)
					except:
						if self.port == '':
							srv = poplib.POP3(self.server)				# non SSL
						else:
							srv = poplib.POP3(self.server, self.port)
					srv.getwelcome()
					srv.user(self.user)
					srv.pass_(self.password)
				except:
					frequency = cfg.get('account', 'frequency')			# get email check frequency
					print "Error: Cannot connect to POP account: %s. " \
						"Next try in %s minutes." % (self.server, frequency)
					srv = False

		return srv														# server object


class Accounts:
	def __init__(self):
		self.account = []
		keyring = Keyring()
		self.keyring_was_locked = keyring.was_locked

		on = cfg.get('account', 'on')
		name = cfg.get('account', 'name')
		server = cfg.get('account', 'server')
		user = cfg.get('account', 'user')
		imap = cfg.get('account', 'imap')
		folder = cfg.get('account', 'folder')
		port = cfg.get('account', 'port')

		separator = '|'
		on_list = on.split(separator)
		name_list = name.split(separator)
		server_list = server.split(separator)
		user_list = user.split(separator)
		imap_list = imap.split(separator)
		folder_list = folder.split(separator)
		port_list = port.split(separator)

		for i in range(len(name_list)):									# iterate 0 to nr of elements in name_list
			on = int(on_list[i])
			name = name_list[i]
			if not on or name == '': continue							# ignore accounts that are off or have no name
			server = server_list[i]
			user = user_list[i]
			imap = int(imap_list[i])
			folder = folder_list[i]
			port = port_list[i]
			if imap: protocol = 'imap'
			else: protocol = 'pop'
			password = keyring.get(protocol, user, server)
			self.account.append(Account(name, server, user, password, imap, folder, port))


	def get_count(self, name):											# get number of emails for this provider
		count = 'error'
		for acc in self.account:
			if acc.name == name:
				count = str(acc.mail_count)
				break
		if count == 'error':
			print 'Cannot find account (get_count)'
		return count


# Mail =================================================================
class Mail:
	def __init__(self, seconds, subject, sender, datetime, id, provider):
		self.seconds = seconds
		self.subject = subject
		self.sender = sender
		self.datetime = datetime
		self.id = id
		self.provider = provider


# Mails ================================================================
class Mails:
	def get_mail(self, sort_order):
		mail_list = []													# initialize list of mails
		mail_ids = []													# initialize list of mail ids
		while not self.is_online(): time.sleep(5)						# wait for internet connection
		filter_on = int(cfg.get('filter', 'filter_on'))					# get filter switch

		for acc in accounts.account:									# loop all email accounts
			srv = acc.get_connection()									# get server connection for this account
			if srv == False:
				continue												# continue with next account if server is empty
			elif acc.imap:												# IMAP
				folder_list = acc.folder.split(',')						# make a list of folders
				mail_count = 0											# reset email counter
				if folder_list[0] == '':
					folder_list = ['INBOX']
				for folder in folder_list:
					srv.select(folder.strip(), readonly=True)			# select IMAP folder
					status, data = srv.search(None, 'UNSEEN')				# ALL or UNSEEN
					if status != 'OK' or None in [d for d in data]:
						print "Folder", folder, "in status", status, "| Data:", data, "\n"
						continue										# Bugfix LP-735071
					for num in data[0].split():
						typ, msg_data = srv.fetch(num, '(BODY.PEEK[HEADER])')	# header only (without setting READ flag)
						for response_part in msg_data:
							if isinstance(response_part, tuple):
								try:
									msg = email.message_from_string(response_part[1])
								except:
									print "Could not get IMAP message:", response_part		# debug
									continue
								try:
									try:
										sender = self.format_header('sender', msg['From'])	# get sender and format it
									except KeyError:
										print "KeyError exception for key 'From' in message:", msg	# debug
										sender = self.format_header('sender', msg['from'])
								except:
									print "Could not get sender from IMAP message:", msg	# debug
									sender = "Error in sender"
								try:
									try:
										datetime, seconds = self.format_header('date', msg['Date'])	# get date and format it
									except KeyError:
										print "KeyError exception for key 'Date' in message:", msg	# debug
										datetime, seconds = self.format_header('date', msg['date'])
								except:
									print "Could not get date from IMAP message:", msg		# debug
									datetime = time.strftime('%Y.%m.%d %X')					# take current time as "2010.12.31 13:57:04"
									seconds = time.time()									# take current time as seconds
								try:
									try:
										subject = self.format_header('subject', msg['Subject'])	# get subject and format it
									except KeyError:
										print "KeyError exception for key 'Subject' in message:", msg	# debug
										subject = self.format_header('subject', msg['subject'])
								except:
									print "Could not get subject from IMAP message:", msg	# debug
									subject = 'Error in subject'
								try:
									id = msg['Message-Id']
								except:
									print "Could not get id from IMAP message:", msg		# debug
									id = str(hash(subject))				# create emergency id
						if id not in mail_ids:							# prevent duplicates caused by Gmail labels
							if not (filter_on and self.in_filter(sender + subject)):		# check filter
								mail_list.append(Mail(seconds, subject, \
									sender, datetime, id, acc.name))
								mail_count += 1							# increment mail counter for this IMAP folder
								mail_ids.append(id)						# add id to list
				acc.mail_count = mail_count								# store number of emails per account
				srv.close()
				srv.logout()
			else:														# POP
				mail_total = len(srv.list()[1])							# number of mails on the server
				mail_count = 0											# reset number of relevant mails
				for i in range(1, mail_total+1):						# for each mail
					try:
						message = srv.top(i, 0)[1]						# header plus first 0 lines from body
					except:
						print "Could not get POP message"				# debug
						continue
					message_string = '\n'.join(message)					# convert list to string
					try:
						msg = dict(email.message_from_string(message_string))	# put message into email object and make a dictionary
					except:
						print "Could not get msg from POP message:", message_string	# debug
						continue
					try:
						try:
							sender = self.format_header('sender', msg['From'])	# get sender and format it
						except KeyError:
							print "KeyError exception for key 'From' in message:", msg	# debug
							sender = self.format_header('sender', msg['from'])
					except:
						print "Could not get sender from POP message:", msg	# debug
						sender = "Error in sender"
					try:
						try:
							datetime, seconds = self.format_header('date', msg['Date'])	# get date and format it
						except KeyError:
							print "KeyError exception for key 'Date' in message:", msg	# debug
							datetime, seconds = self.format_header('date', msg['date'])
					except:
						print "Could not get date from POP message:", msg	# debug
						datetime = time.strftime('%Y.%m.%d %X')			# take current time as "2010.12.31 13:57:04"
						seconds = time.time()							# take current time as seconds
					try:
						try:
							subject = self.format_header('subject', msg['Subject'])	# get subject and format it
						except KeyError:
							print "KeyError exception for key 'Subject' in message:", msg	# debug
							subject = self.format_header('subject', msg['subject'])
					except:
						print "Could not get subject from POP message:", msg
						subject = 'Error in subject'
					try:
						uidl = srv.uidl(i)								# get id
					except:
						print "Could not get id from POP message:", message	# debug
						uidl = str(hash(subject))						# create emergency id
					id = acc.user + uidl.split(' ')[2]					# create unique id
					if not (filter_on and self.in_filter(sender + subject)):	# check filter
						mail_list.append(Mail(seconds, subject, sender, \
							datetime, id, acc.name))
						mail_count += 1									# increment mail counter for this IMAP folder
					acc.mail_count = mail_count							# store number of emails per account
				srv.quit()												# disconnect from Email-Server
		mail_list = self.sort_mails(mail_list, sort_order)				# sort mails
		sys.stdout.flush()												# write stdout to log file
		return mail_list


	def is_online(self):												# check for internet connection
		try:
			urllib2.urlopen("http://www.google.com/")
			return True
		except:
			return False


	def in_filter(self, sendersubject):									# check if filter appears in sendersubject
		status = False
		filter_text = cfg.get('filter', 'filter_text')
		filter_list = filter_text.split(',')							# convert text to list
		for filter_item in filter_list:
			filter_stripped_item = filter_item.strip()					# remove CR and white space
			if filter_stripped_item.lower() in sendersubject.lower():
				status = True											# subject contains filter item
				break
		return status


	def sort_mails(self, mail_list, sort_order):						# sort mail list
		sort_list = []
		for mail in mail_list:
			sort_list.append([mail.seconds, mail])						# extract seconds from mail instance
		sort_list.sort()												# sort asc
		if sort_order == 'desc':
			sort_list.reverse()											# sort desc
		mail_list = []													# sort by field 'seconds'
		for mail in sort_list:
			mail_list.append(mail[1])									# recreate mail_list
		return mail_list


	def format_header(self, field, content):							# format sender, date, subject etc.
		if field == 'sender':
			try:
				sender_real, sender_addr = email.utils.parseaddr(content) # get the two parts of the sender
				sender_real = self.convert(sender_real)
				sender_addr = self.convert(sender_addr)
				sender = (sender_real, sender_addr)						# create decoded tupel
			except:
				sender = ('','Error: cannot format sender')

			sender_format = cfg.get('indicate', 'sender_format')
			if sender_format == '1' and sender[0] != '':				# real sender name if not empty
				sender = sender_real
			else:
				sender = sender_addr
			return sender

		if field == 'date':
			try:
				parsed_date = email.utils.parsedate_tz(content)			# make a 10-tupel (UTC)
				seconds = email.utils.mktime_tz(parsed_date)			# convert 10-tupel to seconds incl. timezone shift
				tupel = time.localtime(seconds)							# convert seconds to tupel
				datetime = time.strftime('%Y.%m.%d %X', tupel)			# convert tupel to string
			except:
				print 'Error: cannot format date:', content
				datetime = time.strftime('%Y.%m.%d %X')					# take current time as "2010.12.31 13:57:04"
				seconds = time.time()									# take current time as seconds
			return datetime, seconds

		if field == 'subject':
			try:
				subject = self.convert(content)
			except:
				subject = 'Error: cannot format subject'
			return subject


	def convert(self, raw_content):										# decode and concatenate multi-coded header parts
		content = raw_content.replace('\n',' ')							# replace newline by space
		content = content.replace('?==?','?= =?')						# fix bug in email.header.decode_header()
		tupels = decode_header(content)									# list of (text_part, charset) tupels
		content_list = []
		for text, charset in tupels:									# iterate parts
			if charset == None: charset = 'latin-1'						# set default charset for decoding
			content_list.append(text.decode(charset, 'ignore'))			# replace non-decodable chars with 'nothing'
		decoded_content = ' '.join(content_list)						# insert blanks between parts
		decoded_content = decoded_content.strip()						# get rid of whitespace

		print "  raw    :", raw_content									# debug
		print "  tupels :", tupels										# debug
		print "  decoded:", decoded_content								# debug

		return decoded_content


# Misc =================================================================
def read_config(cfg_file):												# read config file or create it
	cfg = ConfigParser.RawConfigParser()
	if not os.path.exists(cfg_file):
		print 'Error: Cannot find configuration file: ', cfg_file
		exit(1)
	else:
		cfg.read(cfg_file)
		return cfg


def write_pid():														# write Mailnags's process id to file
	pid_file = user_path + 'mailnag.pid'
	f = open(pid_file, 'w')
	f.write(str(os.getpid()))											# get PID and write to file
	f.close()


def delete_pid():														# delete file mailnag.pid
	pid_file = user_path + 'mailnag.pid'
	if os.path.exists(pid_file):
		os.popen("rm " + pid_file)										# delete it


def user_scripts(event, data):											# process user scripts
	if event == "on_email_arrival":
		if cfg.get('script', 'script0_on') == '1' and data > 0:			# on new emails
			pathfile = cfg.get('script', 'script0_file')				# get script pathfile
			if pathfile != '' and os.path.exists(pathfile):				# not empty and existing
				pid.append(subprocess.Popen(pathfile))					# execute
			else:
				print 'Warning: cannot execute script:', pathfile

		if cfg.get('script', 'script1_on') == '1' and data == 0:		# on no new emails
			pathfile = cfg.get('script', 'script1_file')
			if pathfile != '' and os.path.exists(pathfile):
				pid.append(subprocess.Popen(pathfile))
			else:
				print 'Warning: cannot execute script:', pathfile

	elif cfg.get('script', 'script2_on') == '1' and event == "on_email_clicked":
		pathfile = cfg.get('script', 'script2_file')
		if pathfile != '' and os.path.exists(pathfile):
			pid.append(subprocess.Popen([pathfile, data[0], data[1], data[2]]))	# call script with 'sender, datetime, subject'
		else:
			print 'Warning: cannot execute script:', pathfile

	elif cfg.get('script', 'script3_on') == '1' and event == "on_account_clicked":
		pathfile = cfg.get('script', 'script3_file')
		if pathfile != '' and os.path.exists(pathfile):
			pid.append(subprocess.Popen([pathfile, data[0], data[1]]))	# call script with account_name
		else:
			print 'Warning: cannot execute script:', pathfile

	else:
		return False


def commandExecutor(command, context_menu_command=None):
	if context_menu_command != None:									# check origin of command
		command = context_menu_command

	if command == 'clear':												# clear indicator list immediatelly
		mailchecker.clear()
#		if indicator.desktop_display != None:
#			indicator.desktop_display.destroy()
	elif command == 'exit':												# exit mailnag immediatelly
		delete_pid()
		exit(0)
	elif command == 'check':											# check immediatelly for new emails
		mailchecker.timeout()
#	elif command == 'list':												# open summary window
#		rows = []
#		for mail in indicator.mail_list:
#			rows.append([mail.provider, mail.sender, \
#				mail.subject, mail.datetime])
#		ProviderEmailList(rows, self.sender)							# show email list for all providers
	else:
		command_list = command.split(' ')								# create list of arguments
		pid.append(subprocess.Popen(command_list))						# execute 'command'


# MailChecker ============================================================
class MailChecker:
	def __init__(self):
		self.MAIL_LIST_LIMIT = 5						# gnome-shell shows a scrollbar when more than 5 mails are listed
		self.mails = Mails()											# create Mails object
#		self.messages = []												# empty message list
		self.reminder = Reminder()										# create Reminder object
#		self.link = cfg.get('indicate', 'start_on_click')				# get link address
#		desktop_file = os.path.join(user_path, "popper.desktop")		# path of the desktop file
#		self.server = indicate.indicate_server_ref_default()			# create indicator server
#		self.server.set_type("message.mail")
#		self.server.set_desktop_file(desktop_file)
#		self.server.connect("server-display", self.headline_clicked)	# if clicked on headline
#		self.server.show()
		pynotify.init("Mailnag")								# initialize Notification
		
		self.notification = pynotify.Notification(" ", None, None)			# empty string will emit a gtk warning
		self.notification.set_category("email")
		self.notification.add_action("open", _("Open in mail reader"), self.__notification_action_handler)
		self.notification.add_action("close", _("Close"), self.__notification_action_handler)

#		self.desktop_display = None										# the Window object for Desktop_Display


	def timeout(self):
		print 'Checking email accounts at:', time.asctime()				# debug
		pid.kill()														# kill all Zombies
		new_mails = 0													# reset number of new mails
#		sort_by = cfg.get('indicate', 'sort_by')						# 1 = date	0 = provider
		show_only_new = bool(int(cfg.get('indicate', 'show_only_new')))	# get show_only_new flag
#		menu_count = self.number_of_menu_entries()						# nr of menu entries
		if firstcheck and autostarted:
			self.reminder.load()
#			self.add_menu_entries('asc')								# add menu entries to indicator menu
#			self.sort_order = 'asc'										# set sort order for mail_list and summary window
			self.mail_list = self.mails.get_mail('desc')		# get all mails from all inboxes
#			if sort_by == '1':											# sort by date
#				max = self.limit - menu_count							# calculate boundaries
#				if max > len(self.mail_list):
#					max = len(self.mail_list)							# calculate boundaries
#				for i in range(0, max):
#					if not show_only_new or \
#					self.reminder.unseen(self.mail_list[i].id):
#						self.messages.append(Message(self.mail_list[i]))# add new mail to messages
#			else:														# sort by provider
#				self.add_account_summaries()							# add providers to indicator menu
		else:
			if firstcheck:												# Manual firststart
				self.reminder.load()
#			self.sort_order = 'asc'										# set sort order for mail_list and summary window
			self.mail_list = self.mails.get_mail('desc')		# get all mails from all inboxes
#			if sort_by == '1':											# sort by date
#				for message in self.messages:							# clear indicator menu
#					message.set_property("draw-attention", "false")		# white envelope in panel
#					message.hide()										# hide message in indicator menu
#				self.messages = []										# clear message list
#
#				max = len(self.mail_list)								# calculate boundaries
#				low = max - self.limit + menu_count						# calculate boundaries
#				if low < 0:
#					low = 0												# calculate boundaries
#				for i in range(low, max):
#					if not show_only_new or \
#					self.reminder.unseen(self.mail_list[i].id):
#						self.messages.append(Message(self.mail_list[i]))# add new mail to messages
#			else:														# sort by provider
#				self.add_account_summaries()							# add providers to indicator menu
#			self.add_menu_entries('desc')								# add menu entries to indicator menu

#		sender = ''
#		subject = ''
		summary = ""		
		body = ""		
		for mail in self.mail_list:										# get number of new mails
			if not self.reminder.contains(mail.id):
				if new_mails < self.MAIL_LIST_LIMIT:
					body += mail.sender + ": <i>" + mail.subject + "</i>\n"
				new_mails += 1

		if new_mails > self.MAIL_LIST_LIMIT:
			body += "...\n"

#		# Notify =======================================================
		if new_mails > 0:												# new mails?
			if new_mails > 1:											# multiple new emails
				summary = _("You have " + str(new_mails) + " new mails.")
#				notify_text = cfg.get('notify', 'text_multi') % str(new_mails)
			else:
				summary = _("You have a new mail.")
#				notify_text = cfg.get('notify', 'text_one')				# only one new email
#				notify_text += "\n" + sender + "\n" + subject
#
			if cfg.get('notify', 'playsound') == '1':					# play sound?
				soundcommand = ['aplay', '-q', cfg.get('notify', 'soundfile')]
				pid.append(subprocess.Popen(soundcommand))

#			if cfg.get('notify', 'notify') == '1':						# show bubble?
#			headline = cfg.get('indicate', 'headline')
			
#			notification = pynotify.Notification(headline, \
#				notify_text, "notification-message-email")
			self.notification.update(summary, body, "mail-unread")
			self.notification.show()

#			if cfg.get('notify', 'speak') == '1':						# speak?
#				self.speak(notify_text)

#		# Desktop Display ==============================================
#		if cfg.get('dd', 'on') == '1' and new_mails > 0:				# show Desktop Display
#			content = []
#			for mail in self.mail_list:
#				if not show_only_new or self.reminder.unseen(mail.id):
#					content.append([mail.sender + ' - ' + mail.datetime, mail.subject])
#			content.reverse()											# turn around
#			if self.desktop_display != None:
#				self.desktop_display.destroy()							# destroy old window
#			self.desktop_display = DesktopDisplay(content)
#			self.desktop_display.show()

		# Misc =========================================================
		user_scripts("on_email_arrival", new_mails)						# process user scripts

		self.reminder.save(self.mail_list)
		sys.stdout.flush()												# write stdout to log file
		return True


	def __notification_action_handler(self, n, action):
		if action == "open":
			emailclient = cfg.get('indicate', 'start_on_click').split(' ') # create list of command arguments				
			pid.append(subprocess.Popen(emailclient))
		elif action == "close":
			pass # notifications are closed automatically when an action is triggered	


#	def add_account_summaries(self):									# add entries per provider in indicator menu
#		if firstcheck:													# firstcheck = True -> add entries
#			for acc in accounts.account:								# loop all email accounts
#				self.messages.append(Message(Mail(4.0, acc.name, \
#					acc.name, None, 'id_4', 'acc_entry')))
#		else:															# firstcheck = False -> update count
#			show_only_new = bool(int(cfg.get('indicate', 'show_only_new')))	# get show_only_new flag
#			for message in self.messages:
#				if message.provider == 'acc_entry':
#					old_count = message.get_property("count")			# get last count
#					if show_only_new:
#						count = self.get_new_count(message.subject)		# get count of emails that are not in reminder
#					else:
#						count = accounts.get_count(message.subject)		# get number of mails per account
#					message.set_property("count", count)				# update count
#					if int(count) > int(old_count):						# new emails arrived
#						message.set_property("draw-attention", "true")	# green envelope in panel
#					elif int(count) == 0:
#						message.set_property("draw-attention", "false")	# white envelope in panel


#	def add_menu_entries(self, sort_order):								# add menu entries to messages
#		if sort_order == 'asc':
#			show_menu_1 = cfg.get('indicate', 'show_menu_1')
#			if show_menu_1 == '1' and 'id_1' not in \
#			[message.id for message in self.messages]:
#				name_menu_1 = cfg.get('indicate', 'name_menu_1')
#				cmd_menu_1 = cfg.get('indicate', 'cmd_menu_1')
#				if name_menu_1 != '' and cmd_menu_1 != '':
#					self.messages.append(Message(Mail(1.0, name_menu_1, \
#						cmd_menu_1, None, 'id_1', 'menu_entry')))
#
#			show_menu_2 = cfg.get('indicate', 'show_menu_2')
#			if show_menu_2 == '1' and 'id_2' not in \
#			[message.id for message in self.messages]:
#				name_menu_2 = cfg.get('indicate', 'name_menu_2')
#				cmd_menu_2 = cfg.get('indicate', 'cmd_menu_2')
#				if name_menu_2 != '' and cmd_menu_2 != '':
#					self.messages.append(Message(Mail(2.0, name_menu_2, \
#						cmd_menu_2, None, 'id_2', 'menu_entry')))
#
#			show_menu_3 = cfg.get('indicate', 'show_menu_3')
#			if show_menu_3 == '1' and 'id_3' not in \
#			[message.id for message in self.messages]:
#				name_menu_3 = cfg.get('indicate', 'name_menu_3')
#				cmd_menu_3 = cfg.get('indicate', 'cmd_menu_3')
#				if name_menu_3 != '' and cmd_menu_3 != '':
#					self.messages.append(Message(Mail(3.0, name_menu_3, \
#						cmd_menu_3, None, 'id_3', 'menu_entry')))
#		else:
#			show_menu_3 = cfg.get('indicate', 'show_menu_3')
#			if show_menu_3 == '1' and 'id_3' not in \
#			[message.id for message in self.messages]:
#				name_menu_3 = cfg.get('indicate', 'name_menu_3')
#				cmd_menu_3 = cfg.get('indicate', 'cmd_menu_3')
#				if name_menu_3 != '' and cmd_menu_3 != '':
#					self.messages.append(Message(Mail(3.0, name_menu_3, \
#						cmd_menu_3, None, 'id_3', 'menu_entry')))
#
#			show_menu_2 = cfg.get('indicate', 'show_menu_2')
#			if show_menu_2 == '1' and 'id_2' not in \
#			[message.id for message in self.messages]:
#				name_menu_2 = cfg.get('indicate', 'name_menu_2')
#				cmd_menu_2 = cfg.get('indicate', 'cmd_menu_2')
#				if name_menu_2 != '' and cmd_menu_2 != '':
#					self.messages.append(Message(Mail(2.0, name_menu_2, \
#						cmd_menu_2, None, 'id_2', 'menu_entry')))
#
#			show_menu_1 = cfg.get('indicate', 'show_menu_1')
#			if show_menu_1 == '1' and 'id_1' not in \
#			[message.id for message in self.messages]:
#				name_menu_1 = cfg.get('indicate', 'name_menu_1')
#				cmd_menu_1 = cfg.get('indicate', 'cmd_menu_1')
#				if name_menu_1 != '' and cmd_menu_1 != '':
#					self.messages.append(Message(Mail(1.0, name_menu_1, \
#						cmd_menu_1, None, 'id_1', 'menu_entry')))
#
#
#	def number_of_menu_entries(self):									# return number of active menu entries
#		count = 0
#		if cfg.get('indicate', 'show_menu_1') == '1':
#			count += 1
#		if cfg.get('indicate', 'show_menu_2') == '1':
#			count += 1
#		if cfg.get('indicate', 'show_menu_3') == '1':
#			count += 1
#		return count
#
#
#	def headline_clicked(self, server, dummy):							# click on headline
#		if self.desktop_display != None:
#			self.desktop_display.destroy()
#		clear_on_click = cfg.get('indicate', 'clear_on_click')
#		if clear_on_click == '1':
#			self.clear()												# clear messages list
#		emailclient = self.link.split(' ')								# create list of command arguments
#		pid.append(subprocess.Popen(emailclient))						# start link (Email Client)
#

	def clear(self):													# clear the messages list (not the menu entries)
		show_only_new = bool(int(cfg.get('indicate', 'show_only_new')))	# get show_only_new flag
#		remove_list = []
#		for message in self.messages:									# for all messages
#			message.set_property("draw-attention", "false")				# white envelope in panel
#			if message.provider not in ['menu_entry','acc_entry']:		# email entry
#				message.hide()											# remove from indicator menu
#				remove_list.append(message)								# add to removal list
#			elif message.provider == 'acc_entry':						# account entry
#				message.set_property("count", "0")						# reset count to account menu entry
#			if show_only_new:
#				for mail in self.mail_list:								# loop mails in mail list
#					self.reminder.set_to_seen(mail.id)					# set seen flag for this email to True
#		for message in remove_list:
#			self.messages.remove(message)								# remove all email entries from messages list
		
		
		if show_only_new:
			for mail in self.mail_list:
				self.reminder.set_to_seen(mail.id)

			self.reminder.save(self.mail_list)							# save to mailnag.dat
		else:															# keep 'list' filled
			self.mail_list = []											# clear mail list


#	def get_new_count(self, provider):									# get count of emails not in reminder for one provider
#		count = 0														# default counter
#		for mail in self.mail_list:										# loop all emails
#			if mail.provider == provider and self.reminder.unseen(mail.id):	# this provider and unflaged
#				count += 1
#		return str(count)


#	def speak(self, text):												# speak the text
#		lang = locale.getdefaultlocale()[0].lower()						# get language from operating system
#		if 'de' in lang:
#			lang = 'de'
#		else:
#			lang = 'en'
#		if cfg.get('notify', 'playsound') == '1':						# if sound should be played
#			time.sleep(1)												# wait until sound is played halfway
#		pid.append(subprocess.Popen(['espeak', '-s', '140','-v' + lang, text]))	# speak it


## Message ==============================================================
#class Message(indicate.Indicator):
#	def __init__(self, mail):
#		indicate.Indicator.__init__(self)
#
#		self.seconds = mail.seconds
#		self.subject = mail.subject
#		self.sender = mail.sender
#		self.datetime = mail.datetime
#		self.id = mail.id
#		self.provider = mail.provider
#
#		self.connect("user-display", self.clicked)
#
#		if self.provider not in ['menu_entry','acc_entry']:				# it is a normal message
#			self.set_property("draw-attention", "true")					# green envelope in panel
#			subject_short = self.get_short_subject(self.subject)		# cut subject text
#			self.set_property("subtype", "mail")
#			
#			show_sender = cfg.get('indicate', 'show_sender')
#			show_subject = cfg.get('indicate', 'show_subject')
#			
#			if show_sender == '0' and show_subject == '0':
#				message_text = self.datetime							# datetime
#			elif show_sender == '1' and show_subject == '0':
#				message_text = self.sender								# sender
#			elif show_sender == '0' and show_subject == '1':
#				message_text = subject_short							# subject
#			else:
#				message_format = cfg.get('indicate', 'message_format')
#				if message_format == '0':
#					message_text = "%s - %s" % (subject_short, self.sender)
#				else:
#					message_text = "%s - %s" % (self.sender, subject_short)
#
#			show_provider = cfg.get('indicate', 'show_provider')
#			if show_provider == '1':
#				message_text = "%s - %s" % (self.provider, message_text)	# provider
#				self.set_property("name", message_text)
#			else:
#				self.set_property("name", message_text)
#			self.set_property("count", self.get_time_delta())			# put age in counter spot
#			
#		else:															# it is a menue or account entry
#			show_only_new = bool(int(cfg.get('indicate', 'show_only_new')))	# get show_only_new flag
#			self.set_property("name", self.subject)
#			if self.provider == 'acc_entry':							# it is an account entry
#				if firstcheck:
#					old_count = '0'										# default last count
#				else: old_count = self.get_property("count")			# get last count
#				if show_only_new:
#					count = indicator.get_new_count(self.subject)		# get count of emails that are not in reminder
#				else:
#					count = accounts.get_count(self.subject)			# get number of mails per account
#				self.set_property("count", count)						# add count to provider menu entry
#				if int(count) > int(old_count):							# new emails arrived
#					self.set_property("draw-attention", "true")			# green envelope in panel
#		self.show()
#
#
#	def clicked(self, MessageObject, MessageNumber):					# click on message
#		if self.provider not in ['menu_entry','acc_entry']:				# it is a normal message
#			if cfg.get('indicate', 'remove_single_email') == '1':
#				self.hide()												# remove from indicator menu
#				show_only_new = bool(int(cfg.get('indicate', 'show_only_new')))
#				if show_only_new:
#					indicator.reminder.set_to_seen(self.id)				# don't show it again
#			else:														# show OSD
#				notify_text = self.sender + '\n' + self.datetime + \
#					'\n' + self.subject
#				notification = pynotify.Notification(self.provider, \
#					notify_text, "notification-message-email")
#				notification.show()										# show details of one message
#
#			user_scripts("on_email_clicked", \
#				[self.sender, self.datetime, self.subject])				# process user scripts
#		elif self.provider == 'menu_entry':								# it is a menu entry
#			command = self.sender
#			commandExecutor(command)
#		else:	# account entry
#			rows = []
#			for mail in indicator.mail_list:
#				if mail.provider == self.sender:						# self.sender holds the account name
#					rows.append([mail.provider, mail.sender, \
#						mail.subject, mail.datetime])
#			ProviderEmailList(rows, self.sender)						# show email list for this provider
#			user_scripts("on_account_clicked", [self.sender, len(rows)])# process user scripts (account, number_of_emails)
#
#
#	def get_short_subject(self, subject):								# shorten long mail subject text
#		subject_length = int(cfg.get('indicate', 'subject_length'))		# format subject
#		if len(subject) > subject_length:
#			dot_filler = '...'											# set dots if longer than n
#		else:
#			dot_filler = ''
#		subject_short = subject[:subject_length] + dot_filler			# shorten subject
#		return subject_short
#
#
#	def get_time_delta(self):											# return delta hours
#		delta = time.time() - self.seconds								# calculate delta seconds
#		if delta < 0:
#			return "?"													# negative age
#		else:
#			unit = " s"
#			if delta > 60:
#				delta /= 60												# convert to minutes
#				unit = " m"
#				if delta > 60:
#					delta /= 60											# convert to hours
#					unit = " h"
#					if delta > 24:
#						delta /= 24										# convert to days
#						unit = " d"
#						if delta > 7:
#							delta /= 7									# convert to weeks
#							unit = " w"
#							if delta > 30:
#								delta /= 30								# convert to months
#								unit = " M"
#								if delta > 12:
#									delta /= 12							# convert to years
#									unit = " Y"
#		delta_string = str(int(round(delta))) + unit					# make string
#		return delta_string
#

## Provider Email List Dialog ===========================================
#class ProviderEmailList:
#	def __init__(self, rows, title):
#		if len(rows) == 0:
#			return														# nothing to show
#		builder = gtk.Builder()											# build GUI from Glade file
#		builder.set_translation_domain('popper_list')
#		builder.add_from_file("popper_list.glade")
#		builder.connect_signals({ \
#		"gtk_main_quit" : self.exit, \
#		"on_button_close_clicked" : self.exit})
#		_ = gettext.gettext
#		colhead = [_('Provider'), _('From'), _('Subject'), _('Date')]	# column headings
#		self.window = builder.get_object("dialog_popper_list")
#		self.window.set_title('Popper')
#		width, hight = self.get_window_size(rows, colhead)				# calculate window size
#		self.window.set_default_size(width, hight)				  		# set the window size
#
#		treeview = builder.get_object("treeview")						# get the widgets
#		liststore = builder.get_object("liststore")
#		close_button = builder.get_object("button_close")
#		close_button.set_label(_('Close'))
#
#		renderer = gtk.CellRendererText()
#		column0 = gtk.TreeViewColumn(colhead[0], renderer, text=0)		# Provider
#		column0.set_sort_column_id(0)									# make column sortable
#		column0.set_resizable(True)										# column width resizable
#		treeview.append_column(column0)
#
#		column1 = gtk.TreeViewColumn(colhead[1], renderer, text=1)		# From
#		column1.set_sort_column_id(1)
#		column1.set_resizable(True)
#		treeview.append_column(column1)
#
#		column2 = gtk.TreeViewColumn(colhead[2], renderer, text=2)		# Subject
#		column2.set_sort_column_id(2)
#		column2.set_resizable(True)
#		treeview.append_column(column2)
#
#		column3 = gtk.TreeViewColumn(colhead[3], renderer, text=3)		# Date
#		column3.set_sort_column_id(3)
#		column3.set_resizable(True)
#		treeview.append_column(column3)
#
#		if not autostarted:
#			rows.reverse()												# not autostarted
#		elif indicator.sort_order == 'asc':
#			rows.reverse()												# autostarted and firstcheck
#
#		for row in rows:
#			liststore.append(row)										# add emails to summary window
#		self.window.show()
#
#
#	def get_window_size(self, rows, colhead):
#		max = 0															# default for widest row
#		fix = 50														# fix part of width (frame, lines, etc)
#		charlen = 7														# average width of one character
#		height = 480													# fixed set window height
#		min_width = 320													# lower limit for window width
#		max_width = 1024												# upper limit for window width
#		alist = self.transpose(rows)									# transpose list
#		for i in range(len(colhead)):
#			alist[i].append(colhead[i] + '  ')							# add column headings
#		colmax = []														# list with the widest string per column
#		for col in alist:												# loop all columns
#			temp_widest = 0												# reset temporary widest row value
#			for row in col:												# loop all row strings
#				if len(row) > temp_widest:
#					temp_widest = len(row)								# find the widest string in that column
#			colmax.append(temp_widest)									# save the widest string in that column
#		for row in colmax:
#			max += row													# add all widest strings
#		width = fix + max * charlen										# calculate window width
#		if width < min_width:
#			width = min_width											# avoid width underrun
#		if width > max_width:
#			width = max_width											# avoid width overrun
#		return width, height
#
#
#	def transpose(self, array):											# transpose list (switch cols with rows)
#		return map(lambda *row: list(row), *array)
#
#
#	def exit(self, widget):												# exit
#		self.window.destroy()


# Reminder =============================================================
class Reminder(dict):

	def load(self):														# load last known messages from mailnag.dat
		remember = cfg.get('indicate', 'remember')
		dat_file = user_path + 'mailnag.dat'
		we_have_a_file = os.path.exists(dat_file)						# check if file exists
		if remember == '1' and we_have_a_file:
			f = open(dat_file, 'r')										# open file again
			for line in f:
				stripedline = line.strip()								# remove CR at the end
				content = stripedline.split(',')						# get all items from one line in a list: ["mailid", show_only_new flag"]
				try:
					self[content[0]] = content[1]						# add to dict [id : flag]
				except IndexError:
					self[content[0]] = '0'								# no flags in mailnag.dat
			f.close()							   						# close file


	def save(self, mail_list):											# save mail ids to file
		dat_file = user_path + 'mailnag.dat'
		f = open(dat_file, 'w')											# open the file for overwrite
		for m in mail_list:
			try:
				seen_flag = self[m.id]
			except KeyError:
				seen_flag = '0'											# id of a new mail is not yet known to reminder
			line = m.id + ',' + seen_flag + '\n'						# construct line: email_id, seen_flag
			f.write(line)												# write line to file
			self[m.id] = seen_flag										# add to dict
		f.close()					   									# close the file


	def contains(self, id):												# check if mail id is in reminder list
		try:
			self[id]
			return True
		except KeyError:
			return False


	def set_to_seen(self, id):											# set seen flag for this email on True
		try:
			self[id] = '1'
		except KeyError:
			pass


	def unseen(self, id):												# return True if flag == '0'
		try:
			flag = self[id]
			if flag == '0':
				return True
			else:
				return False
		except KeyError:
			return True


# Pid ==================================================================
class Pid(list):														# List class to manage subprocess PIDs

	def kill(self):														# kill all zombies
		removals = []													# list of PIDs to remove from list
		for p in self:
			returncode = p.poll()										# get returncode of subprocess
			if returncode == 0:
				removals.append(p)										# zombie will be removed
		for p in removals:
			self.remove(p)												# remove non-zombies from list


## Desktop Display ======================================================
#class DesktopDisplay(gtk.Window):										# displays a transparent frameless window on the desktop
#	__gsignals__ = {
#		'expose-event': 'override'
#		}
#
#	def __init__(self, content):
#		super(DesktopDisplay, self).__init__()
#
#		self.content = content											# array of text lists
#
#		self.set_title('Popper Desktop Display')
#		self.set_app_paintable(True)									# no window border
#		self.set_decorated(False)
#		self.set_position(gtk.WIN_POS_CENTER)
#		pixbuf = gtk.gdk.pixbuf_new_from_file('popper.png')				# get icon from png
#		self.set_icon(pixbuf)											# set window icon
#		pos_x = int(cfg.get('dd', 'pos_x'))
#		pos_y = int(cfg.get('dd', 'pos_y'))
#		self.move(pos_x, pos_y)											# move window to position x,y
#
#		self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
#		self.connect("button-press-event", self.event_mouse_clicked)
#
#		screen = self.get_screen()										# see if we can do transparency
#		alphamap = screen.get_rgba_colormap()
#		rgbmap   = screen.get_rgb_colormap()
#		if alphamap is not None:
#			self.set_colormap(alphamap)
#		else:
#			self.set_colormap(rgbmap)
#			print _("Warning: transparency is not supported")
#
#		width = int(cfg.get('dd','width'))
#		height = int(cfg.get('dd','height'))
#		self.set_size_request(width, height)
#
#		font = cfg.get('dd','font_name').split(' ')						# make list ['ubuntu', 12]
#		self.font_name = ' '.join(font[:-1])							# everything except the last one
#		try:
#			self.font_size = int(font[-1])								# only the last one
#		except ValueError:												# if something wrong, use defaults
#			self.font_name = 'ubuntu'
#			self.font_size = '14'
#
#
#	def do_expose_event(self, event):
#		width, height = self.get_size()
#		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
#		ctx = cairo.Context(surface)
#
#		# Background
#		red, green, blue = self.get_rgb(str(cfg.get('dd','bg_color')))	# convert hex color to (r, g, b) / 100 values
#		alpha = (100 - int(cfg.get('dd','transparency'))) / 100.0
#		ctx.set_source_rgba(red, green, blue, alpha)					# background is red, green, blue, alpha
#		ctx.paint()
#
#		# Text
#		ctx.select_font_face(self.font_name, cairo.FONT_SLANT_NORMAL, \
#			cairo.FONT_WEIGHT_NORMAL)
#		ctx.set_font_size(self.font_size)
#		red, green, blue = self.get_rgb(str(cfg.get('dd','text_color')))
#		ctx.set_source_rgb(red, green, blue)
#		self.show_text(ctx, self.content)								# write text to surface
#
#		dest_ctx = self.window.cairo_create()							# now copy to our window surface
#		dest_ctx.rectangle(event.area.x, event.area.y, \
#			event.area.width, event.area.height)						# only update what needs to be drawn
#		dest_ctx.clip()
#
#		dest_ctx.set_operator(cairo.OPERATOR_SOURCE)					# source operator means replace, don't draw on top of
#		dest_ctx.set_source_surface(surface, 0, 0)
#		dest_ctx.paint()
#
#
#	def show_text(self, ctx, content):									# write text to surface
#		x = 10
#		y = 20
#		mail_offset = 10
#		line_offset = self.font_size
#		width = int(cfg.get('dd','width'))
#		x_cut = int(width / self.font_size * 1.7)						# end of line
#		height = int(cfg.get('dd','height'))
#		y_cut = int(height / (2 * line_offset + mail_offset)) - 2		# end of page
#		mail_count = 0
#
#		for mail in content:											# iterate all mails
#			mail_count += 1
#			for line in mail:											# iterate lines in mail
#				ctx.move_to(x, y)
#				if len(line) > x_cut: continuation = '...'
#				else: continuation = ''
#				ctx.show_text(line[:x_cut] + continuation)				# print stripped line
#				y += line_offset
#			y += mail_offset
#			if mail_count > y_cut:										# end of page
#				if len(content) > mail_count:
#					ctx.move_to(x, y)
#					ctx.show_text('...')
#				break
#
#
#	def get_rgb(self, hexcolor):										# convert hex color to (r, g, b) / 100 values
#		color = gtk.gdk.color_parse(hexcolor)
#		divisor = 65535.0
#		red = color.red / divisor
#		green = color.green / divisor
#		blue = color.blue / divisor
#		return red, green, blue											# exp.: 0.1, 0.5, 0.8
#
#
#	def event_mouse_clicked(self, widget, event):						# mouse button clicked
#		if event.button == 1:											# left button?
#			if bool(int(cfg.get('dd', 'click_launch'))):
#				indicator.headline_clicked(None, None)
#			if bool(int(cfg.get('dd', 'click_close'))):
#				self.destroy()
#		if event.button == 3:											# right button?
#			self.event_mouse_clicked_right(widget, event)
#
#
#	def event_mouse_clicked_right(self, widget, event):					# right mouse button clicked
#		contextMenu = gtk.Menu()
#		for str_i in ('1', '2', '3'):
#			if bool(int(cfg.get('indicate', 'show_menu_' + str_i))):	# if command is enabled append to context menu
#				menu_item = gtk.MenuItem(cfg.get('indicate', 'name_menu_' + str_i))
#				menu_item.connect('activate', commandExecutor,
#					cfg.get('indicate', 'cmd_menu_' + str_i))
#				contextMenu.append(menu_item)
#		if len(contextMenu) > 0:										# any entries at all?
#			contextMenu.show_all()
#			contextMenu.popup(None, None, None, event.button, event.time)
#

def cleanup():
	# clean up resources
	try:	
		mailchecker.notification.close()
	except NameError: pass
	delete_pid()

# Main =================================================================
def main():
	global cfg, user_path, accounts, mails, mailchecker, autostarted, firstcheck, pid

#	try:																# Internationalization
#		locale.setlocale(locale.LC_ALL, '')								# locale language, e.g.: de_CH.utf8
#	except locale.Error:
#		locale.setlocale(locale.LC_ALL, 'en_US.utf8')					# english for all unsupported locale languages
#	locale.bindtextdomain('popper', 'locale')
#	gettext.bindtextdomain('popper', 'locale')
#	gettext.textdomain('popper')

	signal.signal(signal.SIGTERM, cleanup)

	try:
		user_path = os.path.expanduser("~/.mailnag/")						# set path to: "/home/user/.mailnag/"
		autostarted = False													# default setting for command line argument
		cmdline = sys.argv													# get command line arguments
		if len(cmdline) > 1:												# do we have something in command line?
			if cmdline[1] == 'autostarted':
				autostarted = True
		write_pid()															# write Mailnag's process id to file
		cfg = read_config(user_path + 'mailnag.cfg')							# get configuration from file
		
		accounts = Accounts()												# create Accounts object
		if accounts.keyring_was_locked: firstcheck = False					# required for correct sortorder in indi menu
		else: firstcheck = True

		pid = Pid()															# create Pid object
		mailchecker = MailChecker()												# create MailChecker object
		mailchecker.timeout()													# immediate check, firstcheck=True
		firstcheck = False													# firstcheck is over
		
		if cfg.get('account', 'check_once') == '0':							# wanna do more than one email check?
			frequency = int(cfg.get('account', 'frequency'))				# get email check frequency
			gobject.timeout_add_seconds(60*frequency, mailchecker.timeout)			# repetitive check
			gtk.main()														# start Loop
		
		cleanup()		
		return 0
	except KeyboardInterrupt:
		cleanup()

if __name__ == '__main__': main()

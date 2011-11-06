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

PACKAGE_NAME = "mailnag"

import poplib
import imaplib
import urllib2
import os
import subprocess
import threading
from gi.repository import GObject, GLib, GdkPixbuf, Gtk, Notify
import time
import email
from email.header import decode_header
import sys
import gettext
from config import read_cfg, cfg_exists, cfg_folder
from keyring import Keyring
from utils import *
import signal

gettext.bindtextdomain(PACKAGE_NAME, './locale')
gettext.textdomain(PACKAGE_NAME)
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
					check_interval = cfg.get('general', 'check_interval')
					print "Error: Cannot connect to IMAP account: %s. " \
						"Next try in %s minutes." % (self.server, check_interval)
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
					check_interval = cfg.get('general', 'check_interval')
					print "Error: Cannot connect to POP account: %s. " \
						"Next try in %s minutes." % (self.server, check_interval)
					srv = False

		return srv														# server object


class Accounts:
	def __init__(self):
		self.account = []
		keyring = Keyring()
		self.keyring_was_locked = keyring.was_locked

		separator = '|'
		on_list = cfg.get('account', 'on').split(separator)
		name_list = cfg.get('account', 'name').split(separator)
		server_list = cfg.get('account', 'server').split(separator)
		user_list = cfg.get('account', 'user').split(separator)
		imap_list = cfg.get('account', 'imap').split(separator)
		folder_list = cfg.get('account', 'folder').split(separator)
		port_list = cfg.get('account', 'port').split(separator)

		# check if the account list is empty
		if len(name_list) == 1 and name_list[0] == '':
			return
		
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
									id = None                                               # prepare emergency 
								
								if id == None or id == '':
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
						uidl = None                                         # prepare emergency
					
					if uidl == None or uidl == '':	
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
		filter_list = filter_text.replace('\n', '').split(',')			# convert text to list
		for filter_item in filter_list:
			filter_stripped_item = filter_item.strip()					# remove CR and white space
			
			if len(filter_stripped_item) == 0:
				continue
			
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

			sender_format = cfg.get('general', 'sender_format')
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
def read_config():
	if not cfg_exists():
		return None
	else:
		return read_cfg()


def write_pid(): # write Mailnags's process id to file
	pid_file = os.path.join(cfg_folder, 'mailnag.pid')
	f = open(pid_file, 'w')
	f.write(str(os.getpid()))
	f.close()


def delete_pid(): # delete file mailnag.pid
	pid_file = os.path.join(cfg_folder, 'mailnag.pid')
	if os.path.exists(pid_file):
		os.popen("rm " + pid_file)


def user_scripts(event, data):
	if event == "on_mail_check":
		if cfg.get('script', 'script0_on') == '1':
			script_file = cfg.get('script', 'script0_file')
			if script_file != '' and os.path.exists(script_file):
				pid.append(subprocess.Popen("%s %s" % (script_file, data), shell = True))
			else:
				print 'Warning: cannot execute script:', script_file
		
		if (data != '0') and (cfg.get('script', 'script1_on') == '1'):
			script_file = cfg.get('script', 'script1_file')
			if script_file != '' and os.path.exists(script_file):
				pid.append(subprocess.Popen("%s %s" % (script_file, data), shell = True))
			else:
				print 'Warning: cannot execute script:', script_file


def commandExecutor(command, context_menu_command=None):
	if context_menu_command != None:									# check origin of command
		command = context_menu_command

	if command == 'clear':												# clear indicator list immediatelly
		mailchecker.clear()
	elif command == 'exit':												# exit mailnag immediatelly
		delete_pid()
		exit(0)
	elif command == 'check':											# check immediatelly for new emails
		mailchecker.timeout()
	else:
		command_list = command.split(' ')								# create list of arguments
		pid.append(subprocess.Popen(command_list))						# execute 'command'


# MailChecker ============================================================
class MailChecker:
	def __init__(self):
		self.MAIL_LIST_LIMIT = 10 # prevent flooding of the messaging tray
		self.mailcheck_lock = threading.Lock()
		self.mails = Mails()
		self.reminder = Reminder()
		# dict that tracks all notifications that need to be closed
		self.notifications = {}
		
		Notify.init(cfg.get('general', 'messagetray_label')) # initialize Notification		
		

	def timeout(self, firstcheck = False):
		with self.mailcheck_lock:
			print 'Checking email accounts at:', time.asctime()
			pid.kill() # kill all zombies
		
			if firstcheck: # Manual firststart
				self.reminder.load()	

			self.mail_list = self.mails.get_mail('desc') # get all mails from all inboxes
		
			unseen_mails = []
			new_mails = []
		
			script_data = ""
			script_data_mailcount = 0
			
			for mail in self.mail_list:
				if self.reminder.contains(mail.id): # mail was fetched before
					if self.reminder.unseen(mail.id): # mail was not marked as seen
						unseen_mails.append(mail)
						if firstcheck: # first check after startup
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
				if cfg.get('general', 'notification_mode') == '1':
					self.notify_summary(unseen_mails)
				else:
					self.notify_single(new_mails)

				if cfg.get('general', 'playsound') == '1': # play sound?
					soundcommand = ['aplay', '-q', get_data_file(cfg.get('general', 'soundfile'))]
					pid.append(subprocess.Popen(soundcommand))

			self.reminder.save(self.mail_list)

		user_scripts("on_mail_check", script_data) # process user scripts
		
		sys.stdout.flush() # write stdout to log file
		return True


	def notify_summary(self, unseen_mails):
		summary = ""		
		body = ""

		if len(self.notifications) == 0:
			self.notifications['0'] = self.get_notification(" ", None, None) # empty string will emit a gtk warning
		
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

	
	def notify_single(self, new_mails):
		for mail in new_mails:
			n = self.get_notification(mail.sender, mail.subject, "mail-unread")
			notification_id = str(id(n))
			n.add_action("mark-as-read", _("Mark as read"), self.__notification_action_handler, (mail, notification_id), None)			
			n.show()
			self.notifications[notification_id] = n


	def get_notification(self, summary, body, icon):
		n = Notify.Notification.new(summary, body, icon)		
		n.set_category("email")
		n.add_action("default", "default", self.__notification_action_handler, None, None)

		return n
	

	def __notification_action_handler(self, n, action, user_data):
		with self.mailcheck_lock:
			if action == "default":
				emailclient = cfg.get('general', 'mail_client').split(' ') # create list of command arguments				
				pid.append(subprocess.Popen(emailclient))
				
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
		

# Reminder =============================================================
class Reminder(dict):

	def load(self):														# load last known messages from mailnag.dat
		remember = cfg.get('general', 'remember')
		dat_file = os.path.join(cfg_folder, 'mailnag.dat')
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
		dat_file = os.path.join(cfg_folder, 'mailnag.dat')
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
		return (id in self)


	def set_to_seen(self, id):											# set seen flag for this email on True
		try:
			self[id] = '1'
		except KeyError:
			pass


	def unseen(self, id):												# return True if flag == '0'
		try:
			flag = self[id]
			return (flag == '0')
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


def cleanup():
	# clean up resources
	try:	
		for n in mailchecker.notifications.itervalues():
			n.close()
	except NameError: pass
	delete_pid()


def sig_handler(signum, frame):
	if mainloop != None:
		mainloop.quit()


# Main =================================================================
def main():
	global mainloop, cfg, accounts, mails, mailchecker, pid

	mainloop = None
	
	set_procname("mailnag")

	signal.signal(signal.SIGTERM, sig_handler)
	
	try:
		write_pid() # write Mailnag's process id to file
		cfg = read_config()
		
		if (cfg == None):
			print 'Error: Cannot find configuration file. Please run mailnag_config first.'
			exit(1)
		
		accounts = Accounts()												# create Accounts object
		pid = Pid()															# create Pid object
		mailchecker = MailChecker()											# create MailChecker object
		mailchecker.timeout(True)											# immediate check, firstcheck=True
		
		check_interval = int(cfg.get('general', 'check_interval'))
		GObject.timeout_add_seconds(60 * check_interval, mailchecker.timeout)
		mainloop = GObject.MainLoop()
		mainloop.run()
	except KeyboardInterrupt:
		pass # ctrl+c pressed
	finally:
		cleanup()


if __name__ == '__main__': main()

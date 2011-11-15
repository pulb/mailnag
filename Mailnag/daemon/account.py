#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# account.py
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

import time
import poplib
import daemon.imaplib2 as imaplib

class Account:
	def __init__(self, check_interval, name, server, user, password, imap, folder, port):
		self.check_interval = check_interval
		self.name = name
		self.server = server
		self.user = user
		self.password = password
		self.imap = imap # int
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
					print "Error: Cannot connect to IMAP account: %s. " \
						"Next try in %s minutes." % (self.server, self.check_interval)
					srv = None
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
					print "Error: Cannot connect to POP account: %s. " \
						"Next try in %s minutes." % (self.server, self.check_interval)
					srv = None

		return srv														# server object



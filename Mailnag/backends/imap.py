# Copyright 2011 - 2021 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2020 Andreas Angerer
# Copyright 2016 Timo Kankare <timo.kankare@iki.fi>
# Copyright 2016 Thomas Haider <t.haider@deprecate.de>
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

"""Implementation for IMAP mailbox connection."""

import email
import logging
import re

from Mailnag.backends.base import MailboxBackend
import Mailnag.common.imaplib2 as imaplib
from Mailnag.common.imaplib2 import AUTH
from Mailnag.common.exceptions import InvalidOperationException
from Mailnag.common.mutf7 import encode_mutf7, decode_mutf7


class IMAPMailboxBackend(MailboxBackend):
	"""Implementation of IMAP mail boxes."""

	def __init__(self, name = '', user = '', password = '', oauth2string = '',
				 server = '', port = '', ssl = True, folders = [], idle=True, **kw):
		self.name = name
		self.user = user
		self.password = password
		self.oauth2string = oauth2string
		self.server = server
		self.port = port
		self.ssl = ssl # bool
		self.folders = [encode_mutf7(folder) for folder in folders]
		self.idle = idle
		self._conn = None


	def open(self):
		if self._conn != None:
			raise InvalidOperationException("Account is aready open")
		
		self._conn = self._connect()

		
	def close(self):
		# if conn has already been closed, don't try to close it again
		if self._conn != None:
			conn = self._conn
			self._conn = None
			self._disconnect(conn)


	def is_open(self):
		return self._conn != None


	def list_messages(self):
		self._ensure_open()
		
		conn = self._conn
		
		if len(self.folders) == 0:
			folder_list = [ 'INBOX' ]
		else:
			folder_list = self.folders

		for folder in folder_list:
			# select IMAP folder
			conn.select(f'"{folder}"', readonly = True)
			try:
				status, data = conn.uid('SEARCH', None, '(UNSEEN)') # ALL or UNSEEN
			except:
				logging.warning('Folder %s does not exist.', folder)
				continue

			if status != 'OK' or None in [d for d in data]:
				logging.debug('Folder %s in status %s | Data: %s', (folder, status, data))
				continue # Bugfix LP-735071
			for num in data[0].split():
				typ, msg_data = conn.uid('FETCH', num, '(BODY.PEEK[HEADER])') # header only (without setting READ flag)
				for response_part in msg_data:
					if isinstance(response_part, tuple):
						try:
							msg = email.message_from_bytes(response_part[1])
						except:
							logging.debug("Couldn't get IMAP message.")
							continue
						yield (folder, msg, { 'uid' : num.decode("utf-8"), 'folder' : folder })


	def request_folders(self):
		lst = []
		
		# Always create a new connection as an existing one may
		# be used for IMAP IDLE.
		conn = self._connect()

		try:
			status, data = conn.list()
		finally:
			self._disconnect(conn)
		
		for d in data:
			match = re.match(r'.+\s+("."|"?NIL"?)\s+"?([^"]+)"?$', d.decode('utf-8'))

			if match == None:
				logging.warning("Folder format not supported.")
			else:
				folder = match.group(2)
				lst.append(decode_mutf7(folder))
		
		return lst


	def supports_mark_as_seen(self):
		return True


	def mark_as_seen(self, mails):
		# Always create a new connection as an existing one may
		# be used for IMAP IDLE.
		conn = self._connect()
		
		try:
			sorted_mails = sorted(mails, key = lambda m : m.flags['folder'] if 'folder' in m.flags else '')
			last_folder = ''
			
			for m in sorted_mails:
				if ('uid' in m.flags) and ('folder' in m.flags):
					try:
						folder = m.flags['folder']
						if folder != last_folder:
							conn.select(f'"{folder}"', readonly = False)
							last_folder = folder
						status, data = conn.uid("STORE", m.flags['uid'], "+FLAGS", r"(\Seen)")
					except:
						logging.warning("Failed to set mail with uid %s to seen on server (account: '%s').", m.flags['uid'], acc.name)

		finally:
			self._disconnect(conn)
	
	
	def supports_notifications(self):
		"""Returns True if mailbox supports notifications.
		IMAP mailbox supports notifications if idle parameter is True"""
		return self.idle


	def notify_next_change(self, callback=None, timeout=None):
		self._ensure_open()
		
		# register idle callback that is called whenever an idle event
		# arrives (new mail / mail deleted).
		# the callback is called after <idle_timeout> minutes at the latest.
		# gmail sends keepalive events every 5 minutes.

		# idle callback (runs on a further thread)
		def _idle_callback(args):
			# error = (error_type, error_val)
			response, callback_arg, error = args
			# call actual callback
			callback(error)
		
		self._conn.idle(callback = _idle_callback, timeout = timeout)


	def cancel_notifications(self):
		# NOTE: Don't throw if the connection is closed.
		# Analogous to close().
		# (Otherwise cleanup code like in Idler._idle() will fail)
		# self._ensure_open()
		
		try:
			if self._conn != None:
				# Exit possible active idle state.
				# (also calls idle_callback)
				self._conn.noop()
		except:
			pass
	
	
	def _connect(self):
		conn = None
		
		try:
			if self.ssl:
				if self.port == '':
					conn = imaplib.IMAP4_SSL(self.server)
				else:
					conn = imaplib.IMAP4_SSL(self.server, int(self.port))
			else:
				if self.port == '':
					conn = imaplib.IMAP4(self.server)
				else:
					conn = imaplib.IMAP4(self.server, int(self.port))
				
				if 'STARTTLS' in conn.capabilities:
					conn.starttls()
				else:
					logging.warning("Using unencrypted connection for account '%s'" % self.name)
				
			if self.oauth2string != '':
				conn.authenticate('XOAUTH2', lambda x: self.oauth2string)
			elif 'AUTH=CRAM-MD5' in conn.capabilities:
				# use CRAM-MD5 auth if available
				conn.login_cram_md5(self.user, self.password)
			else:
				conn.login(self.user, self.password)
		except:
			try:
				if conn != None:
					# conn.close() # allowed in SELECTED state only
					conn.logout()
			except:	pass
			raise # re-throw exception
		
		# notify_next_change() (IMAP IDLE) requires a selected folder
		if conn.state == AUTH:
			self._select_single_folder(conn)
		
		return conn


	def _disconnect(self, conn):
		try:
			conn.close()
		finally:		
			# Closing the connection may fail (e.g. wrong state), 
			# but resources need to be freed anyway.
			conn.logout()
	
	
	def _select_single_folder(self, conn):
		if len(self.folders) == 1:
			folder = self.folders[0]
		else:
			folder = "INBOX"
		conn.select(f'"{folder}"', readonly = True)
	
	def _ensure_open(self):
		if not self.is_open():
			raise InvalidOperationException("Account is not open")


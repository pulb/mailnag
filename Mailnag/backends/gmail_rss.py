# Copyright 2021 Daniel Colascione <dancol@dancol.org>
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

"""Implemention for GMail RSS parsing

Store the cookies for GMail fetching in a cookie jar file encrypted
with the "password" we store in the account information.  This way, we
don't have to constantly rewrite configuration or the secret store as
cookies change.
"""

import concurrent.futures
from http.cookiejar import Cookie, CookieJar
import http.cookies
import pickle
import logging
import os.path
import urllib.parse
import urllib.request
from datetime import datetime
import dateutil.parser
import tempfile
from email.message import EmailMessage
from email.utils import format_datetime

from cryptography.fernet import Fernet, InvalidToken

from Mailnag.backends.base import MailboxBackend
from Mailnag.common.config import cfg_folder

GMAIL_URL = "https://mail.google.com/"
GMAIL_RSS_URL = "https://mail.google.com/mail/u/0/feed/atom"

def generate_gmail_cookies_key():
	# The generated key is base64 encoded, so we can treat it as
	# an ASCII string.
	return Fernet.generate_key().decode("ASCII")

def get_gmail_cookie_file_name(account_name):
	return os.path.join(cfg_folder, f"{account_name}.cookies")

def load_gmail_cookies(account_name, cookies_key):
	"""Load GMail cookies for account

	Result is a CookieJar object.
	"""
	file_name = get_gmail_cookie_file_name(account_name)
	try:
		with open(file_name, "rb") as f:
			ciphertext = f.read()
	except IOError:
		return []
	try:
		cookies = pickle.loads(
			Fernet(cookies_key.encode("ASCII")).decrypt(ciphertext))
	except InvalidToken:
		return []
	cookie_jar = CookieJar()
	for cookie in cookies:
		if not isinstance(cookie, http.cookiejar.Cookie):
			return []
		cookie_jar.set_cookie(cookie)
	return cookie_jar

def _serialize_gmail_cookies(cookie_jar):
	# The CookieJar object can't be pickled, but individual
	# cookies inside it can be.
	assert isinstance(cookie_jar, http.cookiejar.CookieJar)
	return pickle.dumps(list(cookie_jar))

def save_gmail_cookies(account_name, cookies_key, cookie_jar):
	"""Save GMail cookies for account."""
	fn = get_gmail_cookie_file_name(account_name)
	ciphertext = (Fernet(cookies_key.encode("ASCII"))
		      .encrypt(_serialize_gmail_cookies(cookie_jar)))
	with tempfile.NamedTemporaryFile(
			dir=os.path.dirname(fn),
			prefix="gmail_rss",
			suffix=".mailnag",
			delete=False) as f:
		try:
			f.write(ciphertext)
			f.flush()
			os.rename(f.name, fn)
		except:
			os.unlink(f.name)

def _feed_entry_to_message(entry):
	message = EmailMessage()
	ad = entry.get("author_detail", {})
	from_name = ad.get("name")
	from_email = ad.get("email")
	title = entry.get("title")
	date = entry.get("published")
	msg_id = entry.get("id")
	if from_name and from_email:
		message.add_header("From", f"{from_name} <{from_email}>")
	elif from_name:
		message.add_header("From", from_name)
	else:
		message.add_header("From", from_email)
	if title is not None:
		message.add_header("Subject", title)
	if date is not None:
		message.add_header("Date", format_datetime(dateutil.parser.parse(date)))
	if msg_id is not None:
		message.add_header("Message-Id", msg_id)
	return message

class GMailRssBackend(MailboxBackend):
	"""Implementation of GMail RSS parsing"""
	def __init__(self, name, password, gmail_labels=(), **kw):
		super().__init__(**kw)
		self._name = name
		self._gmail_labels = gmail_labels
		self._gmail_cookies_key = password or ''
		self._cookie_jar = None
		self._opened = False

	def open(self):
		self._cookie_jar = load_gmail_cookies(self._name, self._gmail_cookies_key)
		if not self._cookie_jar:
			raise ValueError("no cookies")
		self._opened = True

	def close(self):
		self._opened = False
		self._cookie_jar = None

	def is_open(self):
		return self._opened

	def _get_feed_for_label(self, data):
		label = data["label"]
		url = f"{GMAIL_RSS_URL}/{urllib.parse.quote(label)}"
		import feedparser
		return label, data["mode"], feedparser.parse(url, handlers=[
			urllib.request.HTTPCookieProcessor(self._cookie_jar)
		])

	def _get_all_feeds(self):
		labels = self._gmail_labels
		have_included = False
		for label in labels:
			if label.get("mode", "").lower() != "exclude":
				have_included = True
				break
		if not have_included:
			lables = list(labels)
			labels.append({"label": "inbox", "mode": "include"})
		try:
			with concurrent.futures.ThreadPoolExecutor() as pool:
				return pool.map(self._get_feed_for_label,
						self._gmail_labels)
		finally:
			save_gmail_cookies(self._name,
					   self._gmail_cookies_key,
					   self._cookie_jar)

	def list_messages(self):
		excluded_msg_ids = set()
		all_feeds = list(self._get_all_feeds())
		for label, mode, feed in all_feeds:
			if mode.lower() != "exclude":
				continue
			for entry in feed.get("entries"):
				msg = _feed_entry_to_message(entry)
				msg_id = msg.get("Message-Id")
				if msg_id is not None:
					excluded_msg_ids.add(msg_id)
		for label, mode, feed in all_feeds:
			if mode.lower() != "include":
				continue
			for entry in feed.get("entries", ()):
				msg = _feed_entry_to_message(entry)
				msg_id = msg.get("Message-Id")
				if msg_id not in excluded_msg_ids:
					yield label, msg, {}

	def request_folders(self):
		raise NotImplementedError

	def supports_mark_as_seen(self):
		return False

	def mark_as_seen(self, mails):
		raise NotImplementedError

	def supports_notifications(self):
		return False

	def notify_next_change(self, callback=None, timeout=None):
		raise NotImplementedError

	def cancel_notifications(self):
		raise NotImplementedError

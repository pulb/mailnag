# Copyright 2011 - 2020 Patrick Ulbrich <zulu99@gmx.net>
# Copyright 2016 Thomas Haider <t.haider@deprecate.de>
# Copyright 2016, 2018 Timo Kankare <timo.kankare@iki.fi>
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

import logging
import hashlib
from Mailnag.backends import create_backend, get_mailbox_parameter_specs
from Mailnag.common.secretstore import SecretStore
from Mailnag.common.dist_cfg import PACKAGE_NAME

account_defaults = {
	'enabled'			: '0',
	'type'				: 'imap',
	'name'				: '',	
	'user'				: '',
	'password'			: '',
	'server'			: '',
	'port'				: '',
	'ssl'				: '1',
	'imap'				: '1',	
	'idle'				: '1',
	'folder'			: '[]'
}

#
# Account class
#
class Account:
	def __init__(self, mailbox_type = None, enabled = False, name = '', **kw):
		self._backend = None
		self.set_config(
			mailbox_type=mailbox_type,
			name=name,
			enabled=enabled,
			config=kw)


	def set_config(self, mailbox_type, enabled, name, config):
		"""Set accounts configuration."""
		self.enabled = enabled
		if mailbox_type:
			self.mailbox_type = mailbox_type
		elif 'imap' in config:
			self.mailbox_type = 'imap' if config.get('imap', True) else 'pop3'
		else:
		    self.mailbox_type = ''
		self.name = name
		self.user = config.get('user', '')
		self.password = config.get('password', '')
		self.oauth2string = config.get('oauth2string', '')
		self.server = config.get('server', '')
		self.port = config.get('port', '')
		self.ssl = config.get('ssl', True)
		self.imap = config.get('imap', True)
		self.idle = config.get('idle', False)
		self.folders = config.get('folders', [])
		self._rest_of_config = config
		if self._backend and self._backend.is_open():
			self._backend.close()
		self._backend = None

		if mailbox_type == "gmail_rss":
			self.user = name
			self.server = "gmail_rss"

	def get_config(self):
		"""Return account's configuration as a dict."""
		config = {
			'enabled': self.enabled,
			'mailbox_type': self.mailbox_type,
			'name': self.name,
		}
		config.update(self._get_backend_config())
		return config


	def open(self):
		"""Open mailbox for the account."""
		self._get_backend().open()


	def close(self):
		"""Close mailbox for this account."""
		self._get_backend().close()


	# Indicates whether the account 
	# holds an active existing connection.
	def is_open(self):
		"""Returns true if the mailbox is opened."""
		return self._get_backend().is_open()


	def list_messages(self):
		"""Lists unseen messages from the mailbox for this account.
		Yields a set of tuples (folder, message).
		"""
		return self._get_backend().list_messages()


	def supports_notifications(self):
		"""Returns True if account supports notifications."""
		return self._get_backend().supports_notifications()


	def notify_next_change(self, callback=None, timeout=None):
		"""Asks mailbox to notify next change.
		Callback is called when new mail arrives or removed.
		This may raise an exception if mailbox does not support
		notifications.
		"""
		self._get_backend().notify_next_change(callback, timeout)


	def cancel_notifications(self):
		"""Cancels notifications.
		This may raise an exception if mailbox does not support
		notifications.
		"""
		self._get_backend().cancel_notifications()


	def request_server_folders(self):
		"""Requests folder names (list) from a server.
		Returns an empty list if mailbox does not support folders.
		"""
		return self._get_backend().request_folders()


	def supports_mark_as_seen(self):
		return self._get_backend().supports_mark_as_seen()


	def mark_as_seen(self, mails):
		self._get_backend().mark_as_seen(mails)
		
			
	def get_id(self):
		"""Returns unique id for the account."""
		# Assumption: The name of the account is unique.
		return str(hash(self.name))


	def _get_backend(self):
		if not self._backend:
			backend_config = self._get_backend_config()
			self._backend = create_backend(self.mailbox_type,
										   name=self.name,
										   **backend_config)
		return self._backend


	def _get_backend_config(self):
		config = {}
		imap_pop_config = {
			'user': self.user,
			'password': self.password,
			'oauth2string': self.oauth2string,
			'server': self.server,
			'port': self.port,
			'ssl': self.ssl,
			'imap': self.imap,
			'idle': self.idle,
			'folders': self.folders,
		}
		config.update(imap_pop_config)
		config.update(self._rest_of_config)
		return config


#
# AccountManager class
#
class AccountManager:
	def __init__(self):
		self._accounts = []
		self._removed = []
		self._secretstore = SecretStore.get_default()
		
		if self._secretstore == None:
			logging.warning("Failed to create secretstore - account passwords will be stored in plaintext config file.")

	
	def __len__(self):
		return len(self._accounts)
	
	
	def __iter__(self):
		for acc in self._accounts:
			yield acc

		
	def __contains__(self, item):
		return (item in self._accounts)
	
	
	def add(self, account):
		self._accounts.append(account)
	
	
	def remove(self, account):
		self._accounts.remove(account)
		self._removed.append(account)
	
	
	def clear(self):
		for acc in self._accounts:
			self._removed.append(acc)
		del self._accounts[:]
	
	
	def to_list(self):
		# Don't pass a ref to the internal accounts list.
		# (Accounts must be removed via the remove() method only.)
		return self._accounts[:]
	
	
	def load_from_cfg(self, cfg, enabled_only = False):
		del self._accounts[:]
		del self._removed[:]
		
		i = 1
		section_name = "account" + str(i)
		
		while cfg.has_section(section_name):
			enabled		= bool(int(	self._get_account_cfg(cfg, section_name, 'enabled')	))
			
			if (not enabled_only) or (enabled_only and enabled):
				if cfg.has_option(section_name, 'type'):
					mailbox_type = self._get_account_cfg(cfg, section_name, 'type')
					imap = (mailbox_type == 'imap')
				else:
					imap = bool(int(self._get_account_cfg(cfg, section_name, 'imap')))
					mailbox_type = 'imap' if imap else 'pop3'
				name = self._get_account_cfg(cfg, section_name, 'name')

				option_spec = get_mailbox_parameter_specs(mailbox_type)
				options = self._get_cfg_options(cfg, section_name, option_spec)

				# TODO: Getting a password from the secretstore is mailbox specific.
				#       Not every backend requires a password.
				user = options.get('user')
				server = options.get('server')
				# TODO: get rid of the fake server and user names
				if mailbox_type == "gmail_rss":
					user = name
					server = "gmail_rss"
					imap = True
				if self._secretstore != None and user and server:
					password = self._secretstore.get(self._get_account_id(user, server, imap))
					if not password: password = ''
					options['password'] = password

				acc = Account(enabled=enabled,
							  name=name,
							  mailbox_type=mailbox_type,
							  **options)
				self._accounts.append(acc)

			i = i + 1
			section_name = "account" + str(i)
			

	def save_to_cfg(self, cfg):		
		# Remove all accounts from cfg
		i = 1
		section_name = "account" + str(i)
		while cfg.has_section(section_name):
			cfg.remove_section(section_name)
			i = i + 1
			section_name = "account" + str(i)
		
		# Delete secrets of removed accounts from the secretstore
		# (it's important to do this before adding accounts, 
		# in case multiple accounts with the same id exist).
		if self._secretstore != None:
			for acc in self._removed:
				self._secretstore.remove(self._get_account_id(acc.user, acc.server, acc.imap))
			
		del self._removed[:]
		
		# Add accounts
		i = 1
		for acc in self._accounts:
			if acc.oauth2string != '':
				logging.warning("Saving of OAuth2 based accounts is not supported. Account '%s' skipped." % acc.name)
				continue
				
			section_name = "account" + str(i)
			
			cfg.add_section(section_name)
			
			cfg.set(section_name, 'enabled', int(acc.enabled))
			cfg.set(section_name, 'type', acc.mailbox_type)
			cfg.set(section_name, 'name', acc.name)

			config = acc.get_config()
			option_spec = get_mailbox_parameter_specs(acc.mailbox_type)

			# TODO: Storing a password is mailbox specific.
			#       Not every backend requires a password.
			if self._secretstore != None:
				self._secretstore.set(self._get_account_id(acc.user, acc.server, acc.imap), acc.password,
				        f'{PACKAGE_NAME.capitalize()} password for account {acc.user}@{acc.server}')
				config['password'] = ''
                        
			self._set_cfg_options(cfg, section_name, config, option_spec)

			i = i + 1
	
		
	def _get_account_id(self, user, server, is_imap):
                # TODO : Introduce account.uuid when rewriting account and backend code
                return hashlib.md5((user + server + str(is_imap)).encode('utf-8')).hexdigest()
	
	
	def _get_account_cfg(self, cfg, section_name, option_name):
		if cfg.has_option(section_name, option_name):
			return cfg.get(section_name, option_name)
		else:
			return account_defaults[option_name]


	def _get_cfg_options(self, cfg, section_name, option_spec):
		options = {}
		for s in option_spec:
			options[s.param_name] = self._get_cfg_option(cfg,
														 section_name,
														 s.option_name,
														 s.from_str,
														 s.default_value)
		return options


	def _get_cfg_option(self, cfg, section_name, option_name, convert, default_value):
		if convert and cfg.has_option(section_name, option_name):
			value = convert(cfg.get(section_name, option_name))
		else:
			value = default_value
		return value


	def _set_cfg_options(self, cfg, section_name, options, option_spec):
		for s in option_spec:
			if s.to_str and s.param_name in options:
				value = s.to_str(options[s.param_name])
			else:
				value = s.default_value
			cfg.set(section_name, s.option_name, value)


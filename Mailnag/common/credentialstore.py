# Copyright 2015, 2016 Patrick Ulbrich <zulu99@gmx.net>
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

import hashlib


# TODO: Make this class an enum 
# when Mailnag is ported to python 3
class CredentialStoreType:
	NONE	= 'none'
	GNOME	= 'gnome'
	# KDE	= 'kde'


_credentialstoretype = CredentialStoreType.NONE

try:
	import gi
	gi.require_version('GnomeKeyring', '1.0')
	from gi.repository import GnomeKeyring
	_credentialstoretype = CredentialStoreType.GNOME
except: pass


#
# CredentialStore base class
#
class CredentialStore:
	_instance = None
	
	def set(self, key, secret):
		pass
	
	
	def get(self, key):
		pass
	
	
	def remove(self, key):
		pass
	
	
	@staticmethod
	def get_default():
		if (CredentialStore._instance == None) and (_credentialstoretype != CredentialStoreType.NONE):
			CredentialStore._instance = SupportedCredentialStores[_credentialstoretype]()
		
		return CredentialStore._instance
	
	
	@staticmethod
	def from_string(strn):
		cs = None
		if strn == 'auto':
			cs = CredentialStore.get_default()
		elif strn in SupportedCredentialStores:
			cs = SupportedCredentialStores[strn]()
		
		return cs


#
# GNOME CredentialStore
#
class GnomeCredentialStore(CredentialStore):
	def __init__(self):
		(result, kr_name) = GnomeKeyring.get_default_keyring_sync()
		self._defaultKeyring = kr_name
		
		if self._defaultKeyring == None:
			self._defaultKeyring = 'login'

		result = GnomeKeyring.unlock_sync(self._defaultKeyring, None)
		
		if result != GnomeKeyring.Result.OK:
			raise KeyringUnlockException('Failed to unlock default keyring')

		self._migrate_keyring()


	def get(self, key):
		attrs = self._get_attrs(key)
		result, items = GnomeKeyring.find_items_sync(GnomeKeyring.ItemType.GENERIC_SECRET, attrs)
		
		if result == GnomeKeyring.Result.OK:
			return items[0].secret
		else:
			return ''


	def set(self, key, secret):
		if secret == '':
			return
		
		attrs = self._get_attrs(key)
		
		existing_secret = ''
		result, items = GnomeKeyring.find_items_sync(GnomeKeyring.ItemType.GENERIC_SECRET, attrs)
		
		if result == GnomeKeyring.Result.OK:
			existing_secret = items[0].secret
		
		if existing_secret != secret:
			GnomeKeyring.item_create_sync(self._defaultKeyring, \
					GnomeKeyring.ItemType.GENERIC_SECRET, key, \
					attrs, secret, True)


	def remove(self, key):
		attrs = self._get_attrs(key)
		result, items = GnomeKeyring.find_items_sync(GnomeKeyring.ItemType.GENERIC_SECRET, attrs)
		
		if result == GnomeKeyring.Result.OK:
			GnomeKeyring.item_delete_sync(self._defaultKeyring, items[0].item_id)
	
	
	def _get_attrs(self, key):
		attrs = GnomeKeyring.Attribute.list_new()
		keyid = hashlib.md5(key.encode('utf-8')).hexdigest()
		GnomeKeyring.Attribute.list_append_string(attrs, 'source', 'Mailnag')
		GnomeKeyring.Attribute.list_append_string(attrs, 'api-version', '1.1')
		GnomeKeyring.Attribute.list_append_string(attrs, 'keyid', keyid)
		
		return attrs
	
	
	# Migrates pre Mailnag 1.1 keyring items into the new format
	def _migrate_keyring(self):
		attrs = GnomeKeyring.Attribute.list_new()
		GnomeKeyring.Attribute.list_append_string(attrs, 'application', 'Mailnag')
		result, items = GnomeKeyring.find_items_sync(GnomeKeyring.ItemType.GENERIC_SECRET, attrs)
		
		if result == GnomeKeyring.Result.OK:
			for i in items:
				result, info = GnomeKeyring.item_get_info_sync(self._defaultKeyring, i.item_id)
				self.set(info.get_display_name(), i.secret)
				GnomeKeyring.item_delete_sync(self._defaultKeyring, i.item_id)


#
# Exception thrown if the GNOME keyring can't be unlocked
#
class KeyringUnlockException(Exception):
	def __init__(self, message):
		Exception.__init__(self, message)


#
# All supported credential stores
#
SupportedCredentialStores = {
	CredentialStoreType.GNOME : GnomeCredentialStore
	#CredentialStoreType.KDE : KDECredentialStore
}

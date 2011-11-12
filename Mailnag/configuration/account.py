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

class Account:
	def __init__(self, on, name, server, user, password, imap, folder, port):
		self.id = str(id(self))	# unique identifier
		self.on = on # int
		self.name = name
		self.server = server
		self.user = user
		self.password = password
		self.imap = imap # int
		self.folder = folder
		self.port = port


	def get_row(self):
		return [self.id, self.on, self.name]


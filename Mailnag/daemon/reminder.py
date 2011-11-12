#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# reminder.py
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

import os
from common.config import cfg_folder

class Reminder(dict):

	def load(self):														# load last known messages from mailnag.dat
		dat_file = os.path.join(cfg_folder, 'mailnag.dat')
		
		if os.path.exists(dat_file):
			f = open(dat_file, 'r')										# reopen file
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

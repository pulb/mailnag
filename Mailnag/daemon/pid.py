#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# pid.py
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

class Pid(list):														# List class to manage subprocess PIDs

	def kill(self):														# kill all zombies
		removals = []													# list of PIDs to remove from list
		for p in self:
			returncode = p.poll()										# get returncode of subprocess
			if returncode == 0:
				removals.append(p)										# zombie will be removed
		for p in removals:
			self.remove(p)												# remove non-zombies from list



# Copyright 2014 - 2021 Patrick Ulbrich <zulu99@gmx.net>
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
from enum import Enum
from gi.repository import Gio

TEST_HOST = 'www.google.com'


class TestModes(Enum):
	NETWORKMONITOR	= 0
	PING			= 1


class ConnectivityTest:
	def __init__(self, testmode):
		self._testmode = testmode
		self._monitor = None
		
		
	def is_offline(self):
		if self._testmode == TestModes.NETWORKMONITOR:
			if self._monitor == None:
				# The monitor instance is based on NetworkManager if available, 
				# otherwise on the kernels netlink interface.
				self._monitor = Gio.NetworkMonitor.get_default()
			
			if self._monitor.get_connectivity() == Gio.NetworkConnectivity.FULL:
				return False
			else:
				try:
					return (not self._monitor.can_reach(Gio.NetworkAddress.new(TEST_HOST, 8080)))
				except:
					return False
		else:
			return (os.system('ping -c1 -W2 %s > /dev/null 2>&1' % TEST_HOST) != 0)


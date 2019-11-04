# Copyright 2014 - 2019 Patrick Ulbrich <zulu99@gmx.net>
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
import dbus
from enum import Enum

PING_TEST_HOST				= 'www.google.com'

NM_STATE_CONNECTED_GLOBAL	= 70

NM_PATH						= '/org/freedesktop/NetworkManager'
NM_NAME						= 'org.freedesktop.NetworkManager'
DBUS_PROPS_NAME				= 'org.freedesktop.DBus.Properties'


# TODO: Add GLib connection mode if GLib > 2.42 is available 
# (wrap GNetworkmonitor.get_connectivity() into a try/except block)


class TestModes(Enum):
	AUTO			= 0
	NETWORKMANAGER	= 1
	PING			= 2


class ConnectivityTest:
	def __init__(self, testmode):
		self._testmode = testmode
		self._nm_is_offline = True
		
		bus = dbus.SystemBus()
		
		if self._testmode == TestModes.AUTO:
			if bus.name_has_owner(NM_NAME):
				self._testmode = TestModes.NETWORKMANAGER
			else:
				self._testmode = TestModes.PING
		
		if self._testmode == TestModes.NETWORKMANAGER:
			def state_changed_handler(state):
				self._nm_is_offline = (state != NM_STATE_CONNECTED_GLOBAL)
			
			proxy = bus.get_object(NM_NAME, NM_PATH)
			# Note: connect requires DBusGMainLoop(set_as_default = True) 
			# and a running main loop.
			proxy.connect_to_signal('StateChanged', state_changed_handler)
			iface = dbus.Interface(proxy, DBUS_PROPS_NAME)
			state = iface.Get(NM_NAME, 'State')
			self._nm_is_offline = (state != NM_STATE_CONNECTED_GLOBAL)

		
	def is_offline(self):
		if self._testmode == TestModes.NETWORKMANAGER:
			return self._nm_is_offline
		else:
			return (os.system('ping -c1 -W2 %s > /dev/null 2>&1' % PING_TEST_HOST) != 0)


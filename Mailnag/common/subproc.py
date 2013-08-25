#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# subproc.py
#
# Copyright 2013 Patrick Ulbrich <zulu99@gmx.net>
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

import subprocess
import threading
import logging
import time

_plock = threading.Lock()
_tlock = threading.Lock()
_procs = []
_threads = []

def start_subprocess(args, shell = False, callback = None):
	def thread():
		p = subprocess.Popen(args, shell = shell)
		with _plock: _procs.append(p)
		retcode = p.wait()
		with _plock: _procs.remove(p)
		if callback != None:
			callback(retcode)
	
	t = threading.Thread(target = thread)
	with _tlock:
		_threads.append(t)
		t.start()


def terminate_subprocesses():
	with _tlock:
		if len(_threads) == 0:
			return
	
	with _plock:
		for p in _procs:
			# Ask all runnig processes to terminate.
			# This will also terminate threads waiting for p.wait().
			# Note : terminate() does not block.
			try: p.terminate()
			except: logging.debug('p.terminate() failed')

	# Start a watchdaog thread that will kill 
	# all processes that didn't terminate within 3 seconds.
	wd = _Watchdog(3.0)
	wd.start()
	
	with _tlock:
		# Wait for all threads to terminate
		for t in _threads:
			t.join()
		del _threads[0 : len(_threads)]
	
	wd.stop()
	
	if (not wd.triggered):
		logging.info('All subprocesses exited normally.')


class _Watchdog(threading.Thread):
	def __init__(self, timeout):
		threading.Thread.__init__(self)
		self.triggered = False
		self._timeout = timeout
		self._event = threading.Event()


	def run(self):
		# Note : keep in mind that cleanup() in mailnag.py 
		# has a timeout as well, so don't wait too long.
		self._event.wait(self._timeout)
		if not self._event.is_set():
			logging.warning('Process termination took too long - watchdog starts killing...')
			self.triggered = True
			with _plock:
				for p in _procs:
					try:
						# Kill process p and quit the thread 
						# waiting for p to terminate (p.wait()).
						p.kill()
						logging.info('Watchdog killed process %s' % p.pid)
					except: logging.debug('p.kill() failed')


	def stop(self):
		# Abort watchdog thread (may have been triggered already)
		self._event.set()
		# Wait for watchdog thread (may be inactive already)
		self.join()

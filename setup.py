#!/usr/bin/env python

# To install Mailnag run this script as root:
# ./setup.py install

from distutils.core import setup
from distutils.cmd import Command
from distutils.log import warn, info, error
from distutils.command.install_data import install_data
from distutils.command.build import build
from distutils.sysconfig import get_python_lib

import sys
import os
import subprocess
import glob

from Mailnag.common.dist_cfg import PACKAGE_NAME, APP_VERSION


# TODO : This hack won't work with --user and --home options
PREFIX = '/usr'
for arg in sys.argv:
	if arg.startswith('--prefix='):
		PREFIX = arg[9:]

BUILD_DIR = 'build'
for arg in sys.argv:
	if arg.startswith('--build-base='):
		BUILD_DIR = arg[13:]

BUILD_LOCALE_DIR = os.path.join(BUILD_DIR, 'locale')
INSTALL_LIB_DIR =  os.path.join(get_python_lib(prefix=PREFIX), 'Mailnag')


class BuildData(build):
	def run (self):
		# generate translations
		try:
			rc = subprocess.call('./gen_locales ' + BUILD_LOCALE_DIR, shell = True)
			if (rc != 0):
				if (rc == 1): err = "MKDIR_ERR"
				elif (rc == 2): err = "MSGFMT_ERR"
				else: err = "UNKNOWN_ERR"
				raise Warning, "gen_locales returned %d (%s)" % (rc, err)
		except Exception, e:
			error("Building locales failed.")
			error("Error: %s" % str(e))
			sys.exit(1)
		
		# patch paths
		self._patch_file('./mailnag', os.path.join(BUILD_DIR, 'mailnag'), './Mailnag', INSTALL_LIB_DIR)
		self._patch_file('./mailnag_config', os.path.join(BUILD_DIR, 'mailnag_config'), './Mailnag', INSTALL_LIB_DIR)
		self._patch_file('./data/mailnag_config.desktop', os.path.join(BUILD_DIR, 'mailnag_config.desktop'), '/usr', PREFIX)
		
		build.run (self)


	def _patch_file(self, infile, outfile, orig, replaced):
		with open(infile, 'r') as f:
			strn = f.read()
			strn = strn.replace(orig, replaced)
		with open(outfile, 'w') as f:
			f.write(strn)


class InstallData(install_data):
	def run (self):
		self._add_locale_data()
		install_data.run (self)
	
	
	def _add_locale_data(self):
		for root, dirs, files in os.walk(BUILD_LOCALE_DIR):
			for file in files:
				src_path = os.path.join(root, file)
				dst_path = os.path.join('share/locale', os.path.dirname(src_path[len(BUILD_LOCALE_DIR)+1:]))
				self.data_files.append((dst_path, [src_path]))


class Uninstall(Command):
	def run (self):
		# TODO
		pass


setup(name=PACKAGE_NAME,
	version=APP_VERSION,
	description='Mail notification daemon for GNOME 3',
	author='Patrick Ulbrich',
	author_email='zulu99@gmx.net',
	url='https://github.com/pulb/mailnag',
	license='GNU GPL3',
	packages=['Mailnag', 'Mailnag.common', 'Mailnag.configuration', 'Mailnag.daemon'],
	scripts=[os.path.join(BUILD_DIR, 'mailnag'), os.path.join(BUILD_DIR, 'mailnag_config')],
	data_files=[('share/mailnag', glob.glob('data/*.ui')),
		('share/mailnag', ['data/mailnag.ogg']),
		('share/mailnag', ['data/mailnag.svg']),
		('share/applications', [os.path.join(BUILD_DIR, 'mailnag_config.desktop')])],
	cmdclass={'build': BuildData, 
                'install_data': InstallData,
                'uninstall': Uninstall}
	)

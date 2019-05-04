#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# dist_cfg.py
#
# Copyright 2012 - 2019 Patrick Ulbrich <zulu99@gmx.net>
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

#
# This file contains constants that need to be adjusted for propper distro integration.
#

# Application version displayed in the 
# about dialog of the config window.
APP_VERSION = '1.3.1'

# The PACKAGE_NAME constant is used to configure
# 1) the path where all app data (glade files, images) is loaded from
#    (usually /usr/share/<PACKAGE_NAME>) via get_data_file() (see utils.py). 
# 2) paths for localization files generated with gen_locales
#    (usually /usr/share/locale/<LANG>/LC_MESSAGES/<PACKAGE_NAME>.mo).
# Typically, there's no need to touch this constant.
PACKAGE_NAME = 'mailnag'

# The LOCALE_DIR constant specifies the root path for localization files
# (usually you have to make it point to '/usr/share/locale').
LOCALE_DIR = './locale'

# The DESKTOP_FILE_DIR constant specifies the root path for .desktop files
# (usually you have to make it point to '/usr/share/applications').
DESKTOP_FILE_DIR = './data'

# The LIB_DIR constant specifies the root path for the Mailnag python files
# (usually you have to make it point to <PYTHON_LIB_DIR>/Mailnag).
LIB_DIR = './Mailnag'

# The BIN_DIR constant specifies the path for the mailnag start scripts
# (usually you have to make it point to '/usr/bin').
BIN_DIR = '.'

# DBUS service configuration
DBUS_BUS_NAME = 'mailnag.MailnagService'
DBUS_OBJ_PATH = '/mailnag/MailnagService'

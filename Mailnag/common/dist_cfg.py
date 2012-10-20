#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dist_cfg.py
#
# Copyright 2012 Patrick Ulbrich <zulu99@gmx.net>
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

# This file contains variables that need to be adjusted for propper distro integration.
# Additionally to those variables, packagers have to adjust the following paths:
# * LOCALE_DIR in file gen_locales
# * LIB_DIR in bash scripts mailnag and mailnag_cfg
# * Exec and Icon paths in data/mailnag_config.desktop

# Application version displayed in the 
# about dialog of the config window.
APP_VERSION = "0.4.4"

# The PACKAGE_NAME variable is used to configure
# 1) the path where all app data (glade files, images) is loaded from
#    (usually /usr/share/<PACKAGE_NAME>) via get_data_file() (see utils.py). 
# 2) paths for localization files generated with gen_locales
#    (usually /usr/share/locale/<LANG>/LC_MESSAGES/<PACKAGE_NAME>.mo).
# Typically, there's no need to touch this variable.
PACKAGE_NAME = "mailnag"

# The LOCALE_DIR variable specifies the root path for localization files
# (usually you have to make it point to '/usr/share/locale').
LOCALE_DIR = './locale'

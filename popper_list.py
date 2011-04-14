#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# popper_list.py
#
# Copyright 2010 Ralf Hersel <ralf.hersel@gmx.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
#
#=======================================================================
# POPPER : A new email indicator and notifier for POP3 accounts
#		   popper_settings.py is the GUI for configuration settings
# Author : Ralf Hersel, ralf.hersel@gmx.net
# Version: 0.23
# Date   : Nov 18, 2010
# Licence: GPL
#
# Libraries ============================================================

import gtk


# Settings =============================================================

class Dialog:
	def __init__(self, rows):
		builder = gtk.Builder()											# build GUI from Glade file
		builder.add_from_file("popper_list.glade")
		builder.connect_signals({ \
		"gtk_main_quit" : self.exit, \
		"on_button_close_clicked" : self.exit})

		self.window = builder.get_object("dialog_popper_list")
		width, hight = self.get_window_size(rows)						# calculate window size
		self.window.set_default_size(width, hight)				  		# set the window size

		self.treeview = builder.get_object("treeview")					# get the widgets
		self.liststore = builder.get_object("liststore")

		renderer = gtk.CellRendererText()
		column0 = gtk.TreeViewColumn("Provider", renderer, text=0)
		column0.set_sort_column_id(0)									# make column sortable
		self.treeview.append_column(column0)

		column1 = gtk.TreeViewColumn("From", renderer, text=1)
		column1.set_sort_column_id(1)
		self.treeview.append_column(column1)

		column2 = gtk.TreeViewColumn("Subject", renderer, text=2)
		column2.set_sort_column_id(2)
		self.treeview.append_column(column2)

		column3 = gtk.TreeViewColumn("Date", renderer, text=3)
		column3.set_sort_column_id(3)
		self.treeview.append_column(column3)

		for row in rows: self.liststore.append(row)
		self.window.show()


	def get_window_size(self, rows):
		max = 0															# default for widest row
		fix = 50														# fix part of width (frame, lines, etc)
		charlen = 7														# average width of one character
		height = 480													# fixed set window height
		min_width = 320													# lower limit for window width
		max_width = 1024												# upper limit for window width
		alist = self.transpose(rows)									# transpose list
		alist[0].append('Provider  ')									# add column headings
		alist[1].append('From  ')
		alist[2].append('Subject  ')
		alist[3].append('Date  ')
		print alist
		colmax = []														# list with the widest string per column
		for col in alist:												# loop all columns
			temp_widest = 0												# reset temporary widest row value
			for row in col:												# loop all row strings
				if len(row) > temp_widest: temp_widest = len(row)		# find the widest string in that column
			colmax.append(temp_widest)									# save the widest string in that column
		for row in colmax: max += row									# add all widest strings
		width = fix + max * charlen										# calculate window width
		print width, colmax, max
		if width < min_width: width = min_width							# avoid width underrun
		if width > max_width: width = max_width							# avoid width overrun
		print width, height
		return width, height


	def transpose(self, lists):											# transpose list (switch cols with rows)
		return map(lambda *row: list(row), *lists)


	def exit(self, widget):												# exit
		gtk.main_quit()


# Main =================================================================

def main():
	dialog = Dialog([['G','R','D','24.08.2010'], \
	['Gmail','Martina','Heute schon','25.08.2010'], \
	['Gmail','Martina Gerisch','Igel','25.08.2010'], \
	['Gmail','M','Heute schon gefrühstückst? fragte der Hase den Igel. Natürlich habe ich schon gegessen.','25.08.2010'], \
	['G','Mart','He.','1.1.10'], \
	['G','D','M','26.08.2010']])													# start Dialog
	gtk.main()															# start main loop


if __name__ == "__main__":  main()

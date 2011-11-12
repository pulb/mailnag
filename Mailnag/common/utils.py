import xdg.BaseDirectory as base
import os

PACKAGE_NAME = "mailnag"

def get_data_file(filename):
	"""
	Return path to @filename if it exists
	anywhere in the data paths, else return None
	"""
	# Add "./data" in workdir for running from builddir
	data_paths = []
	data_paths.append("./data")
	data_paths.extend(base.load_data_paths(PACKAGE_NAME))

	for direc in data_paths:
		file_path = os.path.join(direc, filename)
		if os.path.exists(file_path):
			return file_path
	return None


def set_procname(newname):
	from ctypes import cdll, byref, create_string_buffer
	libc = cdll.LoadLibrary('libc.so.6')
	buff = create_string_buffer(len(newname)+1)
	buff.value = newname
	libc.prctl(15, byref(buff), 0, 0, 0)

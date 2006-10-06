# pydvi2svg
# -*- coding: iso-8859-2 -*-
#
# File searching functions
# $Id: findfile.py,v 1.1 2006-10-06 17:55:41 wojtek Exp $
# 
# license: BSD
#
# author: Wojciech Muła
# e-mail: wojciech_mula@poczta.onet.pl

__change__ = '''
5.10.2006
	- find_all
4.10.2006
	- locate, findfile (+ignorecase)
3.10.2006
	- kpsewhich, findfile
'''

import os
import types

def find_all(search_paths, extension):
	def aux(path, extension, list=[]):
		dir = os.listdir(path)
		list.extend( [os.path.join(path, name) for name in dir if name.endswith(extension) ] )

		for file in dir:
			newpath = os.path.join(path, file)
			if os.path.isdir(newpath):
				aux(newpath, extension, list)

		return list
	#fed

	if type(search_paths) in types.StringTypes:
		return aux(search_paths, extension, [])
	
	else:
		list = []
		for path in search_paths:
			aux(path, extension, list)
		return list
	

def findfile(filename, search_paths, ignorecase=False):
	def aux(filename, path):
		dir = os.listdir(path)
		if ignorecase:
			try:
				dir_lower = [name.lower() for name in dir]
				filename  = dir[dir_lower.index(filename.lower())]
				return os.path.join(path, filename)
			except ValueError:
				pass
		else:
			if filename in dir:
				return os.path.join(path, filename)

		# not found, go deeper	
		for file in dir:
			newpath = os.path.join(path, file)
			if os.path.isdir(newpath):
				result = aux(filename, newpath)
				if result:
					return result
		return None
	#fed

	if type(search_paths) in types.StringTypes:
		result = aux(filename, search_paths)
		if result != None: return result
	
	else:
		for path in search_paths:
			result = aux(path)
			if result != None: return result

	return None

kpsewhich_available = True
def kpsewhich(filename):
	global kpsewhich_available

	assert filename != ''

	if kpsewhich_available:
		stdout     = os.popen('kpsewhich %s' % filename, 'r')
		path       = stdout.read().rstrip()
		exitstatus = stdout.close()
		if exitstatus:
			if exitstatus >> 8 == 127: kpsewhich_available = False
			return None
		else:
			return path
	else:
		return None
	
def locate(filename, search_paths=[]):
	return kpsewhich(filename) or findfile(filename, search_paths)
	
# vim: ts=4 sw=4

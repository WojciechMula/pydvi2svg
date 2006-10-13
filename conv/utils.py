# pydvi2svg
# -*- coding: iso-8859-2 -*-
#
# Some utils
# $Id: utils.py,v 1.1 2006-10-13 18:38:44 wojtek Exp $
# 
# license: BSD
#
# author: Wojciech Muła
# e-mail: wojciech_mula@poczta.onet.pl

__changelog__ = '''
13.10.2006
	- added group_elements
'''

def group_elements(seq, value=lambda x: x):
	"""
	Groups adjecent elements that has some value.
	Groups is a pair: common value, list of elements.
	"""
	if not seq:
		return []

	result = []
	prev   = value(seq[0])
	curr   = prev
	group  = [seq[0]]

	for i in xrange(1, len(seq)):
		curr = value(seq[i])
		if curr == prev:
			group.append(seq[i])
		else:
			result.append( (prev, group) )
			group = [seq[i]]
			prev  = curr
	
	if group:
		result.append( (curr, group) )
	
	return result

# vim: ts=4 sw=4

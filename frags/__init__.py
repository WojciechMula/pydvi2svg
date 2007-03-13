#!/usr/bin/python
# -*- coding: iso-8859-2 -*-
# $Id: __init__.py,v 1.4 2007-03-13 00:06:52 wojtek Exp $
#
# SVGfrags - auxilary functions & classes
#
# license: BSD
#
# author: Wojciech Muła
# e-mail: wojciech_mula@poczta.onet.pl
# WWW   : http://wmula.republika.pl/

# changelog
"""
10.03.2007
	+ remove_file
	+ Dict
	+ CSS_value
 9.03.2007
	+ safe_float
	+ get_bbox/get_width/get_height
	+ collect_Id
"""

import os

def safe_float(string, default=0.0):
	try:
		return float(string)
	except ValueError:
		return default
	

def remove_file(filename):
	try:
		os.remove(filename)
	except OSError, error:
		if error.errno != 2: # 2 is file not found (we pass it silently)
			raise error
		

def get_bbox(object):
	"Returns BBox of given object (rect/circle/ellipse are supported)"

	tag = object.tagName

	def safe_get(object, attribute):
		return safe_float(object.getAttribute(attribute))
	if tag == 'rect':
		Xmin = safe_get(object, 'x')
		Ymin = safe_get(object, 'y')
		Xmax = Xmin + safe_get(object, 'width')
		Ymax = Ymin + safe_get(object, 'height')
	elif tag == 'circle':
		cx = safe_get(object, 'cx')
		cy = safe_get(object, 'cy')
		rx = ry = safe_get(object, 'r')

		Xmin = cx - rx
		Ymin = cy - ry
		Xmax = cx + rx
		Ymax = cy + ry

	elif tag == 'ellipse':
		cx = safe_get(object, 'cx')
		cy = safe_get(object, 'cy')
		rx = safe_get(object, 'rx')
		ry = safe_get(object, 'ry')

		Xmin = cx - rx
		Ymin = cy - ry
		Xmax = cx + rx
		Ymax = cy + ry
	else:
		raise ValueError("Can't deal with tag <%s>" % tag)

	return (Xmin, Ymin, Xmax, Ymax)


def get_width(object):
	"Returns width of object"
	xmin, ymin, xmax, ymax = get_bbox(object)
	return xmax-xmin


def get_height(object):
	"Returns width of object"
	xmin, ymin, xmax, ymax = get_bbox(object)
	return ymax-ymin


def collect_Id(XML, d={}):
	# hack
	for object in XML.childNodes:
		try:
			v = object.getAttribute('id')
			if v: d.update([(v, object)])
		except AttributeError: # no hasAttr
			pass
		collect_Id(object, d)


def CSS_value(object, property):
	css_string = object.getAttribute('style')
	for pair in css_string.split(';'):
		prop, value = pair.split(':', 2)
		if prop.strip() == property:
			return value.strip()


class Dict(dict):
	"Ocaml-like dict"
	def __setitem__(self, key, value):
		try:
			L = super(Dict, self).__getitem__(key)
		except KeyError:
			L = []
			super(Dict, self).__setitem__(key, L)

		L.append(value)

# vim: ts=4 sw=4 noexpandtab nowrap

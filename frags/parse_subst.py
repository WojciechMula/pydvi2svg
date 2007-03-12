#!/usr/bin/python
# -*- coding: iso-8859-2 -*-
# $Id: parse_subst.py,v 1.8 2007-03-12 22:22:36 wojtek Exp $
#
# part of SVGfrags -- subst list parser 
#
# license: BSD
#
# author: Wojciech Muła
# e-mail: wojciech_mula@poczta.onet.pl
# WWW   : http://wmula.republika.pl/

# changelog
"""
12.03.2007
	+ rewritten (use parser.py)
10.03.2007
	+ margins property
 9.03.2007
	- class approach:
	  + Tokenizer (base class)
	  + FragsTokenizer (specialized class)
	  + parser
 8.03.2007
	- first version
"""

import re
from parser import token, seq, alt, optional, infty, glued, eat

space 	= re.compile(r'\s+')
comment	= re.compile('\s*%.*\n')

# by default eat spaces and comments
seq.ws = infty(space, comment)

# numbers (converted to float)
def number_cb(l, s, r):
	return [float(r[0])]
number = token(number_cb, re.compile(r'([+-]?\d*\.\d+|[+-]?\d+\.\d*|[-+]?\d+)'))

# number or percents
def numorperc_cb(l, s, r):
	if len(r) == 2:
		# perc
		return [('%', r[0])]
	else:
		return r
numorperc = glued(numorperc_cb, number, optional("(%)"))

def quoted_string_cb(l, s, r):
	return [r[0].replace('\\"', '"')]
quoted_string = token(quoted_string_cb, re.compile(r'"((?:\\"|[^"])*)"'))

def xml_id_cb(l, s, r):
	return [('id', r[0])]
xml_id = token(xml_id_cb, re.compile(r'(#[a-zA-Z0-9._:-]+)'))

def rect_cb(l, s, r):
	return [('rect', tuple(r))]
rect = seq(rect_cb, "rect", "(", number, ",", number, ",", number, ",", number, ")")

def point_cb(l, s, r):
	return [('point', tuple(r))]
point = seq(point_cb, "point", "(", number, ",", number, ")")

def margin_cb(l, s, r):
	if len(r) == 1:
		m = r[0]
		return [('margin', m, m, m, m)]
	elif len(r) == 2:
		mx, my = r
		return [('margin', mx, mx, my, my)]
	else: # 4 elements
		return [('margin',) + tuple(r)]

margin = seq(margin_cb,
	"margin", ":", numorperc,
	 optional(",", numorperc, optional(",", numorperc, ",", numorperc))
)

# number|perc|width(id)|height(id)
def wh_cb(l, s, r):
	return [tuple(r)]
def length_cb(l, s, r):
	return [tuple(r)]

scaledim = alt(
	numorperc,
	number,
	seq(wh_cb, alt("(width)", "(height)"), "(", alt(xml_id, "(this)"), ")"),
	"(uniform)",
	seq(length_cb, "(length)", number),
)

# scale: fit | (scaledim [, scaledim])
def scale_cb(l, s, r):
	if len(r) == 1: # fit/one scaledim
		sx = r[0]
		if sx == 'uniform': return [] # no scale

		if type(sx) is tuple and sx[0] == '%':
			sx = sx[1] * 0.01

		if type(sx) is float:
			return [('scale', sx, sx)]
		elif sx == 'fit':
			return [('scale', 'fit')]
		else:
			return [('scale', sx, "uniform")]
	else: # two scaledim
		sx, sy = r

		if sx == sy == 'uniform':	# no scale
			return []

		if type(sx) is tuple and sx[0] == '%':
			sx = sx[1] * 0.01
		
		if type(sy) is tuple and sy[0] == '%':
			sy = sy[1] * 0.01

		if sy == 'uniform' and type(sx) is float:
			return [('scale', sx, sx)] # uniform
		else:
			return [('scale', sx, sy)]

scale = seq(scale_cb,
	"scale", ":", alt("(fit)", seq(scaledim, optional(",", scaledim)))
)

def position_cb(l, s, r):
	x_const = {
		'center': 0.5, 'c':0.5,
		'left'  : 0.0, 'l':0.0,
		'right' : 1.0, 'r':1.0
	}

	y_const = {
		'center' : 0.5, 'c':0.5,
		'top'    : 0.0, 't':0.0,
		'bottom' : 1.0, 'b':1.0
	}
	
	if len(r) == 1: # single argument
		py = 1.0
		px = r[0]
		if type(px) is str:
			px = x_const[px]
		elif type(px) is tuple: # ('%', float)
			px = px[1] * 0.01

		return [('position', px, py)]
	else: # two args
		px = r[0]
		if type(px) is str:
			px = x_const[px]
		elif type(px) is tuple: # ('%', float)
			px = px[1] * 0.01
		
		py = r[1]
		if type(py) is str:
			py = y_const[py]
		elif type(py) is tuple: # ('%', float)
			py = py[1] * 0.01

		return [('position', px, py)]
		

position = seq(position_cb, 
	"position", ":",
	
	alt(numorperc, number, "(center)", "(c)", "(left)", "(l)", "(right)", "(r)"),
	optional(
		",", alt(numorperc, number, "(center)", "(c)", "(top)", "(t)", "(bottom)", "(b)")
	)
)

class record:
	def __init__(self):
		self.scale    = (1.0, 1.0)
		self.margin   = (0.0, 0.0, 0.0, 0.0)
		self.position = (0.0, 1.0) # left, bottom
	def __str__(self):
		return "{%s}" % ", ".join(self.__dict__.keys())
	
	__repr__ = __str__


def subst_cb(l, s, r):
	# target, tex, (...other data...)
	h = r[0]
	if type(h) is str:
		r[0] = ('string', h)
	
	data = record()
	for item in r[2:]:
		value = item[1:]
		if len(value) == 1:
			setattr(data, item[0], value[0])
		else:
			setattr(data, item[0], value)
	
	return [r[0], r[1], data]

subst = seq(subst_cb,
	alt(quoted_string, xml_id, rect, point),
	eat(token(re.compile(r'(?:->|=>|=)'))),
	quoted_string,
	
	optional(position),
	optional(alt(
		optional(seq(optional(margin), optional(scale))),
		optional(seq(optional(scale), optional(margin))),
	))
)


class SyntaxError(Exception): pass
	

def parse(string):
	while string:
		try:
			l, _ = seq.ws.match(string)
			string = string[l:]
		except TypeError:
			pass

		if not string:
			break
		
		try:
			l, r = subst.match(string)
			yield r
			string = string[l:]
		except TypeError:
			raise SyntaxError("'%s'" % string[:30])

# vim: ts=4 sw=4 nowrap

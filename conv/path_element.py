#!/usr/bin/python
# -*- coding: iso-8859-2 -*-
#
# pydvi2svg
#
# SVG path data parser & bbox calculate
# $Id: path_element.py,v 1.2 2007-03-06 20:50:27 wojtek Exp $
# 
# license: BSD
#
# author: Wojciech Muła
# e-mail: wojciech_mula@poczta.onet.pl

import re
import math

number  = "([+-]?(?:\d+(?:\.\d*)?|\d*\.\d+))"
r_number  = re.compile(number)
r_pair    = re.compile("%s\s*%s\s*" % (number, number))
r_flag    = re.compile("([01])\s*")
r_command = re.compile("\s*([MmZzLlHhVvCcSsQqTtAa])\s*")

def tokens(d_attribute, tofloat=float):
	d = d_attribute.replace('\n', ' ')
	d = d.replace(',', ' ')

	class Tokenizer:
		def __init__(self, d):
			self.d = d
			self.start = 0

		def command(self):
			match = r_command.match(self.d, self.start)
			if match:
				self.start = match.end()
				return match.group(1)
			else:
				return None

		def number(self):
			match = r_number.match(self.d, self.start)
			if match:
				self.start = match.end()
				x = tofloat(match.group(1))
				return x
			else:
				raise ValueError("number expeced - got '%s...'" % self.d[self.start:self.start+20])

		def pair(self):
			match = r_pair.match(self.d, self.start)
			if match:
				self.start = match.end()
				x = tofloat(match.group(1))
				y = tofloat(match.group(2))
				return (x, y)
			else:
				raise ValueError("point expeced - got '%s...'" % self.d[self.start:self.start+40])

		def flag(self):
			match = r_flag.match(self.d, self.start)
			if match:
				self.start = match.end()
				f = int(match.group(1))
				return f

		def __nonzero__(self):
			return self.start < len(self.d)

	tokenizer = Tokenizer(d)
	command = "none"
	while tokenizer:
		tmp = tokenizer.command()
		if tmp:
			command = tmp

		if command in ['z', 'Z']:
			yield (command, None)
			continue

		if command in ['v', 'V', 'h', 'H']:
			yield (command, tokenizer.number())
			continue
		
		if command in ['m', 'M', 'l', 'L', 't', 'T']:
			yield (command, tokenizer.pair())
			continue
		
		if command in ['s', 'S', 'q', 'Q']:
			yield (command, (tokenizer.pair(), tokenizer.pair()))
			continue
		
		if command in ['c', 'C']:
			yield (command, (tokenizer.pair(), tokenizer.pair(), tokenizer.pair()))
			continue
		
		if command in ['a', 'A']:
			yield (command, (tokenizer.pair(), tokenizer.number(), tokenizer.flag(), tokenizer(flag), tokenizer.pair(), tokenizer.pair()))
			continue

		raise ValueError("No command set.")


def translate(path, dx=0.0, dy=0.0):
	path2 = []
	for item in path:
		command, params = item
		if command in ['M', 'L', 'T']:
			x,y = params
			path2.append( (command, (x+dx, y+dy)) )	
		elif command in ['V']:
			y = params
			path2.append( (command, y+dy) )
		elif command in ['H']:
			x = params
			path2.append( (command, x+dx) )
		elif command in ['S', 'Q']:
			(x1,y1), (x2,y2) = params
			path2.append( (command, (x1+dx,y1+dy, x2+dx,y2+dy)) )
		elif command in ['C']:
			(x1,y1), (x2,y2), (x3,y3) = params
			path2.append( (command, ((x1+dx,y1+dy), (x2+dx,y2+dy), (x3+dx,y3+dy))) )
		elif command in ['A']:
			rx,ry, x_axis_rot, large_arc_flag, sweep_flag, x,y = params
			path2.append( (command, (rx+dx,ry+dy, x_axis_rot, large_arc_flag, sweep_flag, x+dx,y+dy)) )
		else:
			path2.append(item)

	return path2


def scale(path, sx=1.0, sy=None):
	if sy == None:
		sy = sx

	path2 = []
	for item in path:
		try:
			command, params = item
		except:
			raise ValueError(str(item))
		if command in ['m', 'M', 'l', 'L', 't', 'T']:
			x,y = params
			path2.append( (command, (x*sx, y*sy)) )
		elif command in ['v', 'V']:
			y = params
			path2.append( (command, y*sy) )
		elif command in ['h', 'H']:
			x = params
			path2.append( (command, x*sx) )
		elif command in ['s', 'S', 'q', 'Q']:
			(x1,y1), (x2,y2) = params
			path2.append( (command, ((x1*sx,y1*sy), (x2*sx,y2*sy))) )
		elif command in ['c', 'C']:
			(x1,y1), (x2,y2), (x3,y3) = params
			path2.append( (command, ((x1*sx,y1*sy), (x2*sx,y2*sy), (x3*sx,y3*sy))) )
		elif command in ['a', 'A']:
			(rx,ry), x_axis_rot, large_arc_flag, sweep_flag, (x,y) = param
			path2.append( (command, ((rx*sx,ry*sy), x_axis_rot, large_arc_flag, sweep_flag, (x*sx,y*sy))) )
		else:
			path2.append(item)
	return path2


def to_path_string(L):
	s = []
	for command, param in L:
		if command in ['m', 'M', 'l', 'L', 't', 'T']:
			s.append('%s%f,%f' % ((command,) + param))
		elif command in ['h', 'H', 'v', 'V']:
			s.append('%s%f' % (command, param))
		elif command in ['c', 'C']:
			P0, P1, P2 = param
			s.append('%s%f,%f %f,%f %f,%f' % ((command,) + P0 + P1 + P2))
		elif command in ['s', 'S', 'q', 'Q']:
			P0, P1 = param
			s.append('%s%f,%f %f,%f' % ((command,) + P0 + P1))
		elif command in ['a', 'A']:
			(rx,ry), x_axis_rot, large_arc_flag, sweep_flag, (x,y) = param
			s.append('%s%f,%f %f %d %d %f,%f' % (rx,ry, x_axis_rot, large_arc_flag, sweep_flag, x, y))
		elif command in ['z', 'Z']:
			s.append('%s' % command)
		else:
			raise NotImplementedError("Command '%s'." % command)
	
	return ' '.join(s)

def nop(*arg):
	pass

def iter(L, init_x=0.0, init_y=0.0, line_fn=nop, ccurve_fn=nop, qcurve_fn=nop):

	cur_x = init_x		# current point
	cur_y = init_y

	clast_x2 = None		# last control point for 's'/'S' 
	clast_y2 = None

	qlast_x1 = None		# last control point for 't'/'T'
	qlast_y1 = None

	mlast_x1 = None		# last moveto coord (for 'z' -- closepath)
	mlast_y1 = None

	prevcomm = 'none'
	for command, param in L:

		# move commands
		# ---------------------------------------------------

		# relative move
		if command == 'm':
			(x,y) = param

			# first 'm' is replaced to 'M'
			if prevcomm == 'none':
				cur_x = x
				cur_y = y
				mlast_x, mlast_y = cur_x, cur_y

			# sequence of m's are converted to rmoveto-lineto
			elif prevcomm == 'm':
				line_fn( (cur_x,cur_y), (cur_x + x, cur_y + y) )
				cur_x += x
				cur_y += y

			# relmove to
			else:
				cur_x += x
				cur_y += y
				mlast_x, mlast_y = cur_x, cur_y

		# absolute move (begin new subpath)
		elif command == 'M':
			(x,y) = param

			# sequence of M's are converted to moveto-lineto
			if prevcomm == 'M':
				line_fn( (cur_x, cur_y),  (x, y) )
				cur_x = x
				cur_y = y

			# move to
			else:
				cur_x = x
				cur_y = y
				mlast_x, mlast_y = cur_x, cur_y

		# line drawing commands
		# ---------------------------------------------------

		# relative lineto
		elif command == 'l':
			(x,y) = param
			line_fn( (cur_x, cur_y), (cur_x + x, cur_y + y) )
			cur_x += x
			cur_y += y

		# absolute lineto
		elif command == 'L':
			(x,y) = param
			line_fn( (cur_x, cur_y), (x, y) )
			cur_x = x
			cur_y = y

		# relative horizontal-lineto
		elif command == 'h':
			x = param
			line_fn( (cur_x, cur_y), (cur_x + x, cur_y) )
			cur_x += x
		
		# absolute horizontal-lineto
		elif command == 'H':
			x = param
			line_fn( (cur_x, cur_y), (x, cur_y) )
			cur_x = x

		# realive veritical-lineto
		elif command == 'v':
			y = param
			line_fn( (cur_x, cur_y), (cur_x, cur_y + y) )
			cur_y += y
		
		# absolute veritical-lineto
		elif command == 'V':
			y = param
			line_fn( (cur_x, cur_y), (cur_x, y) )
			cur_y = y

		# cubic curves
		# ---------------------------------------------------

		# relative curveto
		elif command == 'c':
			x1, y1 = param[0]
			x2, y2 = param[1]
			x, y   = param[2]

			ccurve_fn( (cur_x, cur_y),
			           (cur_x + x1, cur_y + y1),
			           (cur_x + x2, cur_y + y2),
			           (cur_x + x, cur_y + y))

			clast_x2 = cur_x + x2
			clast_y2 = cur_y + y2
			cur_x += x
			cur_y += y
		
		# absolute curveto
		elif command == 'C':
			x1, y1 = param[0]
			x2, y2 = param[1]
			x, y   = param[2]

			ccurve_fn( (cur_x, cur_y), (x1, y1), (x2, y2), (x, y) )

			clast_x2 = x2
			clast_y2 = y2
			cur_x = x
			cur_y = y

		# relative smooth curveto
		elif command == 's':
			from sys import stderr
			x2, y2 = param[0]
			x, y   = param[1]

			if prevcomm in ['c','C','s','S']:
				x1 = cur_x - clast_x2
				y1 = cur_y - clast_y2
			else:
				x1 = cur_x
				y1 = cur_y

			ccurve_fn( (cur_x, cur_y), (cur_x + x1, cur_y + y1), (cur_x + x2, cur_y + y2), (cur_x + x, cur_y + y))

			clast_x2 = cur_x + x2
			clast_y2 = cur_y + y2
			cur_x += x
			cur_y += y
				
		# absolute smooth curveto
		elif command == 'S':
			x2, y2 = param[0]
			x, y   = param[1]

			if prevcomm in ['c','C','s','S']:
				x1 = cur_x - last_x2
				y1 = cur_y - last_y2
			else:
				x1, y1 = cur_x, cur_y

			ccurve_fn( (cur_x, cur_y), (x1, y1), (x2, y2), (x, y))

			clast_x2 = x2
			clast_y2 = y2
			cur_x = x
			cur_y = y


		# quadratic curves
		# ---------------------------------------------------
		
		# relative curveto
		elif command == 'q':
			x1, y1 = param[0]
			x, y   = param[1]

			qcurve_fn( (cur_x, cur_y), (cur_x + x1, cur_y + y1), (cur_x + x, cur_y + y) )

			qlast_x1 = cur_x + x1
			qlast_y1 = cur_y + y1
			cur_x += x
			cur_y += y
		
		# absolute curveto
		elif command == 'Q':
			x1, y1 = param[0]
			x, y   = param[1]

			qcurve_fn( (cur_x, cur_y), (x1, y1), (x, y) )

			qlast_x1 = x1
			qlast_y1 = y1
			cur_x = x
			cur_y = y
		
		# relative smooth curveto
		elif command == 't':
			(x,y) = param
			if prevcomm in ['q','Q','t','T']:
				x1 = cur_x - qlast_x1
				y1 = cur_y - qlast_y1
			else:
				x1 = cur_x
				y1 = cur_y
			
			qcurve_fn( (cur_x, cur_y), (x1, y1), (cur_x + x, cur_y + y) )

			qlast_x1 = x1
			qlast_y1 = y1
			cur_x += x
			cur_y += y
			
		# absolute smooth curveto
		elif command == 'T':
			(x,y) = param
			if prevcomm in ['q','Q','t','T']:
				x1 = cur_x - qlast_x1
				y1 = cur_y - qlast_y1
			else:
				x1 = cur_x
				y1 = cur_y
			
			qcurve_fn( (cur_x, cur_y), (x1, y1), (x, y) )

			qlast_x1 = x1
			qlast_y1 = y1
			cur_x = x
			cur_y = y
		
		elif command in ['z', 'Z']:
			# close current subpath
			line_fn( (cur_x, cur_y), (mlast_x, mlast_y) )

		# elliptical arc (not implemented)
		elif command == 'a':
			raise NotImplementedError
		elif command == 'A':
			raise NotImplementedError
		
		else:
			ValueError("unknown command '%s'" % command)

		prevcomm = command
	#rof
#fed

def bounding_box(L):
	class Dummy:
		pass
	
	cur = Dummy()
	cur.x = []
	cur.y = []

	
	def line((x1,y1), (x2,y2)):
		cur.x.append(x1); cur.x.append(x2)
		cur.y.append(y1); cur.y.append(y2)
	#fed
	
	def qbezier((x0,y0), (x1,y1), (x2,y2)):
		"""Calculate BB of quadric Bezier curve"""

		# bezier curve represented in polynomial base:
		# A t^2 + B t^1 + C 
		Ax =    x0 - 2*y1 + y2
		Bx = -2*x0 + 2*y1
		Cx =    x0
		
		Ay =    y0 - 2*y1 + y2
		By = -2*y0 + 2*y1
		Cy =    y0

		# find extremas
		x = [x0,x2]
		if abs(Ax) > 1e-10:
			x.append(-Bx/(2*Ax))

		y = [y0,y2]
		if abs(Ay) > 1e-10:
			y.append(-By/(2*Ay))

		# update global table
		cur.x.extend(x)
		cur.y.extend(y)

		#return (min(x), min(y)), (max(x), max(y))
	#fed

	def cbezier((x0,y0), (x1,y1), (x2,y2), (x3,y3)):
		"""Calculate BB of cubic Bezier curve"""

		def solve(a,b,c):
			"""Solve quadratic equation"""
			if abs(a) < 1e-10:
				if abs(b) < 1e-10:
					return []
				else:
					return [-c/b]
			else:
				delta = b*b - 4*a*c
				if delta < 0.0:
					return []
				elif delta > 0.0:
					dsq = math.sqrt(delta)
					return [(-b-dsq)/(2*a), (-b+dsq)/(2*a)]
				else:
					return [-b/(2*a)]
		#fed

		# bezier curve represented in polynomial base:
		# A t^3 + B t^2 + C t + D
		Ax =   -x0 + 3*x1 - 3*x2 + x3	# t^3
		Bx =  3*x0 - 6*x1 + 3*x2		# t^2
		Cx = -3*x0 + 3*x1				# t^1
		Dx =    x0						# t^0
		
		Ay =   -y0 + 3*y1 - 3*y2 + y3	# t^3
		By =  3*y0 - 6*y1 + 3*y2		# t^2
		Cy = -3*y0 + 3*y1				# t^1
		Dy =    y0						# t^0

		# find extremas
		x = [x0, x3]
		for t in solve(3*Ax, 2*Bx, Cx):
			if 1.0 > t > 0.0:
				t2 = t*t
				t3 = t*t2
				x.append(t3*Ax + t2*Bx + t*Cx + Dx)
		
		y = [y0, y3]
		for t in solve(3*Ay, 2*By, Cy):
			if 1.0 > t > 0.0:
				t2 = t*t
				t3 = t*t2
				y.append(t3*Ay + t2*By + t*Cy + Dy)

		# update global table
		cur.x.extend(x)
		cur.y.extend(y)
		
		#return (min(x), min(y)), (max(x), max(y))
	#fed

	
	iter(L, line_fn=line, qcurve_fn=qbezier, ccurve_fn=cbezier)
	return (min(cur.x), min(cur.y)), (max(cur.x), max(cur.y))

# vim: ts=4 sw=4

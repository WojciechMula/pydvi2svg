#!/usr/bin/python
# -*- coding: iso-8859-2 -*-
#
# pydvi2svg
#
# Main program
# $Id: dvi2svg.py,v 1.23 2007-03-07 22:46:51 wojtek Exp $
# 
# license: BSD
#
# author: Wojciech Muła
# e-mail: wojciech_mula@poczta.onet.pl

# changelog
"""
 7.03.2007
	- better command line parsing, now user can set name of
	  output file or set output directory
	- new switch --always-number
	- extended "bbox" keyword, now four number are accepted
	  (left/right & top/bottom margin)
	- two bugs fixed
 6.03.2007
	- calculate page bbox
	- --paper-size accepts keyword "bbox"
	- new switch --verbose
 3.03.2007
	- options are global (moved to setup.py)
	- new switches:
	  * --no-fontforge
	  * --no-fnt2meta
	- -paper-size accepts argument "query"
	- a bit shorter output (id string became shorter):
	  before:
	  * sample10001.svg = 123483
	  * sample10002.svg = 72777
	  * sample20001.svg = 90202
	  after:
	  * sample10001.svg = 113055 (-10kB)
	  * sample10002.svg = 66062  (-6.5kB)
	  * sample20001.svg = 83599  (-6.5kB)
 1.03.2007
    - fixed bug
16.10.2006
	- moved get_basename to utils.py
	- implementation of SVGTextDocument finished
15.10.2006
	- added --enc-methods switch
	- moved parse_enc_repl & parse_pagedef to utils.py
	- replaced function open_dvi with findfile.find_file call
14.10.2006
	- small fixes
13.10.2006
	- renamed class SVGDocument to SVGGfxDocument
	- both SVGGfxDocument & SVGTextDocument utilize utils.group_element
	  (code is much simplier)
12.10.2006
	- SVGTextDocument (started)
 6.10.2006
	- removed class fontDB, fontsel now provide these functions (*)
	- use logging module
	- added override encoding (--enc switch)
	- removed --update-cache switch
	- replaced --separate-files switch with --single-file
	- implemented --page-size switch

 4.10.2006
	- much smaller SVG output; characters with same scale factor
	  and y coordinate are grouped;

	  For example:
	  	
		<use x="0" y="10" transform="scale(0.5)" .../>
		<use x="1" y="10" transform="scale(0.5)" .../>
		<use x="2" y="10" transform="scale(0.5)" .../>
		<use x="3" y="11" transform="scale(0.5)" .../>
		<use x="4" y="11" transform="scale(0.5)" .../>
		<use x="5" y="11" transform="scale(0.5)" .../>
	
	  become

		<g transform="scale(0.5)">
			<g transform="translate(0,10)">
				<use x="0" .../>
				<use x="1" .../>
				<use x="2" .../>
			</g>
			<g transform="translate(0,11)">
				<use x="3" .../>
				<use x="4" .../>
				<use x="5" .../>
			</g>
		</g>

  2.10.2006
	- convert single pages
	- some fixes in rendering routines
	- fonts managed by external object, not render itself
	- added command line support
	- fixed font scale calculation
	- added separate class that produce SVG documents

 30.09.2006
 	- version 0.1 (based on previous experiments)
"""

import sys
import os
import xml.dom
import logging

import dviparser
import fontsel
import findfile
import utils
import setup

from binfile import binfile
from colors  import is_colorspecial, execute

class SVGGfxDocument:
	"Outputs glyphs"
	def __init__(self, mag, scale, unit_mm, page_size):
		self.mag		= mag		# maginication
		self.scale		= scale		# additional scale
		self.oneinch	= 25.4/unit_mm

		self.id			= set()
		self.bbox_cache = {}
		self.scale2str	= lambda x: "%0.5f" % x
		self.coord2str	= lambda x: "%0.3f" % x
		
		implementation = xml.dom.getDOMImplementation()
		doctype = implementation.createDocumentType(
			"svg",
			"-//W3C//DTD SVG 1.1//EN",
			"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd")
		self.document = implementation.createDocument(None, "svg", doctype)

		# set SVG implementation
		self.svg      = self.document.documentElement
		self.svg.setAttribute  ('xmlns', 'http://www.w3.org/2000/svg')
		self.svg.setAttributeNS('xmlns', 'xmlns:xlink', "http://www.w3.org/1999/xlink")

		self.svg.setAttribute('width',  '%smm' % str(page_size[0]))
		self.svg.setAttribute('height', '%smm' % str(page_size[1]))
	
	def new_page(self):
		self.chars = []
		self.rules = []
		pass
	
	def put_char(self, h, v, fntnum, dvicode, color=None, next=False):
		try:
			glyph, glyphscale, hadv = fontsel.get_char(fntnum, dvicode)
			assert glyph is not None, (fntnum, dvicode)
		except KeyError:
			return 0.0

		self.id.add( (fntnum, dvicode) )

		H  = self.scale * (h + self.oneinch)
		V  = self.scale * (v + self.oneinch)

		self.chars.append( (fntnum, dvicode, next, H, V, glyphscale, color) )
		return hadv
	
	def put_rule(self, h, v, a, b, color=None):
		self.rules.append( (h, v, a, b, color) )
	
	def eop(self):
		new  = self.document.createElement
		scale2str = self.scale2str
		coord2str = self.coord2str

		page = new('g')
		page.setAttribute('transform', 'scale(%s)' % str(self.mag))
		self.svg.appendChild(page)
		
		# 0. get bounding box (if needed)
		if setup.options.use_bbox:
			xmin, ymin, xmax, ymax = self.__get_page_bbox(page)
			
			xmin -= setup.options.bbox_margin_L
			ymin -= setup.options.bbox_margin_T
			xmax += setup.options.bbox_margin_R
			ymax += setup.options.bbox_margin_B
			
			dx = (xmax - xmin)*self.mag
			dy = (ymax - ymin)*self.mag
			self.svg.setAttribute("width",  coord2str(dx))
			self.svg.setAttribute("height", coord2str(dy))
			self.svg.setAttribute("viewBox", "%s %s %s %s" % 
				(coord2str(xmin*self.mag), coord2str(ymin*self.mag),
				coord2str(dx), coord2str(dy))
			)
		
		# 1. make rules (i.e. filled rectangles)
		for (h,v, a, b, color) in self.rules:
			rect = new('rect')
			rect.setAttribute('x',      coord2str(self.scale * (h + self.oneinch)))
			rect.setAttribute('y',      coord2str(self.scale * (v - a + self.oneinch)))
			rect.setAttribute('width',  coord2str(self.scale * b))
			rect.setAttribute('height', coord2str(self.scale * a))
			if color:
				rect.setAttribute('fill', color)

			page.appendChild(rect)

		# 2. process chars
		from utils import group_elements as group
		

		# (fntnum, dvicode, next, H, V, glyphscale, color)

		# group chars with same glyphscale
		byglyphscale = group(self.chars, value=lambda x: x[5])
		for (glyphscale, chars2) in byglyphscale:
			g = new('g')
			g.setAttribute('transform', 'scale(%s,%s)' % (scale2str(glyphscale), scale2str(-glyphscale) ))
			page.appendChild(g)

			# then group by V
			byV = group(chars2, value=lambda x: x[4])
			for (V, chars3) in byV:
				g1 = new('g')
				g1.setAttribute('transform', 'translate(0,%s)' % coord2str(-V/glyphscale))
				g.appendChild(g1)

				for char in chars3:
					c = new('use')
					g1.appendChild(c)

					H        = char[3]
					fntnum   = char[0]
					dvicode  = char[1]
					color    = char[6]
					idstring = "%02x%d" % (dvicode, fntnum)

					c.setAttributeNS('xlink', 'xlink:href', '#'+idstring)
					c.setAttribute('x', coord2str(H/glyphscale))
					if color:
						c.setAttribute('style', 'fill:%s' % color)

		#rof
	
	def __get_page_bbox(self, page):
		"Returns bbox of chars (self.chars) and rules (self.reules)."

		import path_element
		new  = self.document.createElement
		X = []
		Y = []

		# bbox of chars
		for (fntnum, dvicode, next, H, V, glyphscale, color) in self.chars:
			try:
				bbox = self.bbox_cache[fntnum, dvicode]
			except KeyError:
				path   = fontsel.get_char(fntnum, dvicode)[0]
				tokens = path_element.tokens(path)
				bbox   = path_element.bounding_box(tokens)
				self.bbox_cache[fntnum, dvicode] = bbox

			(xmin, ymin), (xmax, ymax) = bbox
			X.append(H+xmax*glyphscale)
			X.append(H+xmin*glyphscale)
			Y.append(V-ymax*glyphscale)
			Y.append(V-ymin*glyphscale)

			"""
			# blue background for char's bbox (TESTING)
			tmp = new('rect')
			tmp.setAttribute('fill',  '#aaf')
			tmp.setAttribute('x', str(H+xmax*glyphscale))
			tmp.setAttribute('y', str(V-ymax*glyphscale))
			tmp.setAttribute('width',  str(glyphscale * (xmin-xmax)))
			tmp.setAttribute('height', str(glyphscale * (ymax-ymin)))
			page.appendChild(tmp)
			"""
	
		# bbox of rules
		for (h,v, a, b, color) in self.rules:
			X.append(self.scale * (h + self.oneinch))
			X.append(self.scale * (h + self.oneinch + b))
			
			Y.append(self.scale * (v - a + self.oneinch))
			Y.append(self.scale * (v + self.oneinch))

		# get bbox
		xmin = min(X)
		xmax = max(X)

		ymin = min(Y)
		ymax = max(Y)

		"""
		# red frame around bbox (TESTING)
		tmp = new('rect')
		tmp.setAttribute("x", str(xmin))
		tmp.setAttribute("y", str(ymin))
		tmp.setAttribute("width",  str(xmax - xmin))
		tmp.setAttribute("height", str(ymax - ymin))
		tmp.setAttribute('fill',  'none')
		tmp.setAttribute('stroke','red')
		tmp.setAttribute('stroke-width', '2')
		page.appendChild(tmp)
		"""
		
		return xmin, ymin, xmax, ymax

	
	def save(self, filename):
		# create defs
		defs = self.document.createElement('defs')
		for fntnum, dvicode in self.id:
			try:
				glyph, _, _ = fontsel.get_char(fntnum, dvicode)
			except KeyError:
				continue

			path = self.document.createElement('path')
			path.setAttribute("id", "%02x%d" % (dvicode, fntnum))
			path.setAttribute("d",  glyph)
			defs.appendChild(path)

		self.svg.insertBefore(defs, self.svg.firstChild)

		# save
		f = open(filename, 'wb')
		if setup.options.prettyXML:
			f.write(self.document.toprettyxml())
		else:
			f.write(self.document.toxml())
		f.close()


from unic import name_lookup
class SVGTextDocument(SVGGfxDocument):
	"""
	Outputs text
	"""
	def put_char(self, h, v, fntnum, dvicode, color=None, next=False):
		try:
			glyph, glyphscale, hadv = fontsel.get_char(fntnum, dvicode)
			glyphname = fontsel.get_char_name(fntnum, dvicode)
		except KeyError:
			return 0.0

		H  = self.scale * (h + self.oneinch)
		V  = self.scale * (v + self.oneinch)

		self.chars.append( (H, V, fntnum, glyphname, next, color) )

		# return horizontal advance
		return hadv
	
	def eop(self):
		new  = self.document.createElement
		scale2str = self.scale2str
		coord2str = self.coord2str

		page = new('g')
		page.setAttribute('transform', 'scale(%s)' % str(self.mag))
		self.svg.appendChild(page)
		
		# 1. make rules (i.e. filled rectangles)
		for (h,v, a, b, color) in self.rules:
			rect = new('rect')
			rect.setAttribute('x',      coord2str(self.scale * (h + self.oneinch)))
			rect.setAttribute('y',      coord2str(self.scale * (v - a + self.oneinch)))
			rect.setAttribute('width',  coord2str(self.scale * b))
			rect.setAttribute('height', coord2str(self.scale * a))
			if color:
				rect.setAttribute('fill', color)

			page.appendChild(rect)

		# 2. process chars
		from utils import group_elements as group

		# (H, V, fntnum, glyphname, next, color)
	

		# group chars typeseted with the same font
		byfntnum = group(self.chars, value=lambda x: x[2])
		for (fntnum, char_list) in byfntnum:
			g = new('tspan')
			page.appendChild(g)

			font  = fontsel.get_font(fntnum)
			style = "font-family:%s; font-size:%0.1fpt" % (font.fontfamily, font.designsize)
			s,d   = font.sd
			if s != d:	# scaled font
				style += "; font-scale: %0.1f%%" % ((100.0*s)/d)

			g.setAttribute('style', style)
				
			def isglyphknown(glyphname):
				try:
					return bool(name_lookup[glyphname])
				except KeyError:
					return False

			def output_char_string(list):
				H     = list[0][0]
				V     = list[0][1]
				color = list[0][5]
				text  = ''.join([name_lookup[item[3]] for item in list])
				
				node = new('text')
				if color:
					node.setAttribute('style', 'fill:%s' % color)

				node.setAttribute('x', coord2str(H))
				node.setAttribute('y', coord2str(V))
				node.appendChild(self.document.createTextNode(text))
				return node
			
			def output_char(char):
				H     = char[0]
				V     = char[1]
				color = char[5]
				text  = name_lookup[char[3]]
				
				node = new('text')
				if color:
					node.setAttribute('style', 'fill:%s' % color)

				node.setAttribute('x', coord2str(H))
				node.setAttribute('y', coord2str(V))
				node.appendChild(self.document.createTextNode(text))
				return node

			# find unknown chars
			for (known, char_list2) in group(char_list, lambda x: isglyphknown(x[3])):
				if not known:
					for char in char_list2:
						H    = item[0]
						V    = item[1]

						node = new('text')
						node.setAttribute('x', coord2str(H))
						node.setAttribute('y', coord2str(V))
						node.setAttribute('style', 'fill:red')
						node.appendChild(self.document.createTextNode('?'))
						g.appendChild(node)
				else:
					# group set_char commands
					for (set_char, char_list3) in group(char_list2, lambda x: x[4]):
						if set_char:
							for (color, char_list4) in group(char_list3, lambda x: x[5]):
								g.appendChild(output_char_string(char_list4))
						else:
							for char in char_list3:
								g.appendChild(output_char(char))
					#rof


		#rof
	
	def save(self, filename):
		if setup.options.prettyXML:
			log.warning("Pretty XML is disabled in text mode")
		
		# save
		f = open(filename, 'wb')
		f.write(self.document.toxml(encoding="utf-8"))
		f.close()
	

def convert_page(dvi, document):

	h, v, w, x, y, z = 0,0,0,0,0,0	# DVI variables
	fntnum = None					# DVI current font number
	stack  = []						# DVI stack

	color  = None					# current color

	command     = None
	prevcommand = None

	while dvi:
		prevcommand  = command
		command, arg = dviparser.get_token(dvi)

		if command == 'put_char':
			document.put_char(h, v, fntnum, arg, color)

		if command == 'set_char':
			h += document.put_char(h, v, fntnum, arg, color, prevcommand==command)

		elif command == 'nop':
			pass
		elif command == 'bop':
			h, v, w, x, y, z = 0,0,0,0,0,0
			fntnum  = None
		elif command == 'eop':
			document.eop() # ok, we finished this page
			break
		elif command == 'push':
			stack.insert(0, (h, v, w, x, y, z))
		elif command == 'pop':
			(h, v, w, x, y, z) = stack.pop(0)
		elif command == 'right':
			h += arg
		elif command == 'w0':
			h += w
		elif command == 'w':
			b = arg
			w  = b
			h += b
		elif command == 'x0':
			h += x
		elif command == 'x':
			x  = arg
			h += arg
		elif command == 'down':
			v += arg
		elif command == 'y0':
			v += y
		elif command == 'y':
			y  = arg
			v += arg
		elif command == 'z0':
			v += z
		elif command == 'z':
			z  = arg
			v += arg
		elif command == 'fnt_num':
			fntnum = arg
		elif command == 'fnt_def':
			pass		# fonts are already loaded
		elif command == "pre":
			raise ValueError("'pre' command is not allowed inside page - DVI corrupted")
		elif command == "post":
			raise ValueError("'post' command is not allowed inside page - DVI corrupted")
		elif command == "put_rule":
			a, b = arg
			document.put_rule(h, v, a, b, color)

		elif command == "set_rule":
			a, b = arg
			document.put_rule(h, v, a, b, color)
			h += b

		elif command == "xxx":	# special
			if is_colorspecial(arg):
				color, background = execute(arg)
		else:
			raise NotImplementedError("Command '%s' not implemented." % command)


if __name__ == '__main__':
	import optparse
	
	parser = optparse.OptionParser()
	
	parser.add_option("--enc",
					  dest="enc_repl",
					  default={})
	
	parser.add_option("--pretty-xml",
	                  action="store_true",
					  dest="prettyXML",
					  default=False)

	parser.add_option("--single-file",
	                  action="store_true",
					  dest="single_file",
					  default=False)

	parser.add_option("--pages",
	                  dest="pages")
	
	parser.add_option("--scale",
	                  dest="scale",
					  default=1.0)

	parser.add_option("--paper-size",
	                  dest="paper_size",
					  default="A4")
	
	parser.add_option("--generate-text",
	                  action="store_true",
	                  dest="generate_text",
					  default=False)
	
	parser.add_option("--enc-methods",
	                  dest="enc_methods",
					  default="c,t,a")

	parser.add_option("--no-fontforge",
					  action="store_false",
	                  dest="use_fontforge",
					  default=True)
	
	parser.add_option("--no-fnt2meta",
					  action="store_false",
	                  dest="use_fnt2meta",
					  default=True)
	
	parser.add_option("--verbose",
					  action="store_true",
	                  dest="verbose",
					  default=False)
	
	parser.add_option("--always-number",
					  action="store_true",
	                  dest="always_number",
					  default=False)

	(setup.options, args) = parser.parse_args()

	# set logging level
	if setup.options.verbose:
		logging.basicConfig(level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.INFO)
	log = logging.getLogger('dvi2svg')

	# read paper size/print all known paper-size names
	from paper_size import paper_size
	ps = setup.options.paper_size.upper()
	try:
		(pw, ph) = paper_size[ps]
		setup.options.use_bbox = False
		log.debug("Paper size set to %s (%dmm x %dmm)",
		          setup.options.paper_size.upper(), pw, ph)
	except KeyError:
		if ps == "QUERY":
			for name in sorted(paper_size.keys()):
				(pw, ph) = paper_size[name]
				print "%-4s: %dmm x %dmm" % (name, pw, ph)
			del name
			sys.exit()
		elif ps.startswith("BBOX"): # Bounding box
			(pw, ph) = (0, 0)
			
			# variants:
			#  1. BBOX
			#  2. BBOX:number
			#  3. BBOX:number,number
			setup.options.use_bbox = True
		
			mT = mB = mL = mR = 0.0
			if ps.startswith("BBOX:"): # 2. & 3.
				tmp = ps[5:].split(",", 4)
				if len(tmp) == 1: # BBOX:number
					mT = mB = mL = mR = abs(utils.safe_float(tmp[0]))
				elif len(tmp) == 2: # BBOX:number,number
					mL = mR = abs(utils.safe_float(tmp[0]))
					mT = mB = abs(utils.safe_float(tmp[1]))
				elif len(tmp) == 4: # BBOX:number,number,number,number
					mL = abs(utils.safe_float(tmp[0]))
					mR = abs(utils.safe_float(tmp[1]))
					mT = abs(utils.safe_float(tmp[2]))
					mB = abs(utils.safe_float(tmp[3]))

			setup.options.bbox_margin_L = mL
			setup.options.bbox_margin_R = mR
			setup.options.bbox_margin_T = mT
			setup.options.bbox_margin_B = mB
			log.debug("BBox margins: left=%0.2f, right=%0.2f, top=%0.2f, bottom=%02f",
				setup.options.bbox_margin_L,
				setup.options.bbox_margin_R,
				setup.options.bbox_margin_T,
				setup.options.bbox_margin_B,
			)
				
		else:
			log.warning("Know nothing about paper size %s, defaults to A4" % ps)
			(pw, ph) = paper_size['A4']
	del ps
	
	if not args:
		log.info("Nothing to do.")
		sys.exit()

	# load & process information about encoding
	setup.options.enc_methods = utils.parse_enc_methods(setup.options.enc_methods)

	if setup.options.enc_repl:
		fontsel.preload(utils.parse_enc_repl(setup.options.enc_repl))
	else:
		fontsel.preload()

	
	# process command line
	def preprocess(filename):
		# directory? (output)
		if os.path.isdir(filename):
			return ('dir', filename)

		# DVI file? (input)
		dir, fname = os.path.split(filename)
		if dir == '': dir = '.'
		def dvipred(p, f):
			return f==fname or \
			       f==fname + '.dvi' or \
			       f==fname + '.DVI' or \
			       f==fname + '.Dvi'
		dvi = findfile.find_file(dir, dvipred, enterdir=lambda p, l: False)
		if dvi is not None:
			return ('dvi', dvi)
		
		# SVG file? (output)
		if filename.lower().endswith('.svg'):
			return ('svg', filename[:-4])

		# none, skipping
		log.info("File '%s' not found, skipping" % filename)
		return None
		
	tmp  = filter(bool, map(preprocess, args))
	args = []
	
	prev = tmp[0]
	for curr in tmp[1:] + [('dvi', None)]:
		t2, f2 = curr
		t1, f1 = prev
		prev   = curr

		if t1 == 'dvi':
			if t2 == 'svg':
				args.append( (f1, f2) )
			elif t2 == 'dir':
				basename = os.path.split(utils.get_basename(f1))[1]
				args.append( (f1, os.path.join(f2, basename)) )
			else:
				basename = os.path.split(utils.get_basename(f1))[1]
				args.append( (f1, basename) )

	
	for filename, basename in args:
	
		#
		# 1. Open file
		#
		dvi = binfile(filename, 'rb')
		log.info("Processing '%s' file -> '%s'", filename, basename)

		#
		# 2. Read DVI info	
		#
		comment, (num, den, mag, u, l), page_offset, fonts = dviparser.dviinfo(dvi)
		n       = len(page_offset)
		unit_mm = num/(den*10000.0)

		if mag == 1000: # not scaled
			log.debug("%s ('%s') has %d page(s)", dvi.name, comment, len(page_offset))
		else:           # scaled
			log.debug("%s ('%s') has %d page(s); magnification is %0.2f", dvi.name, comment, len(page_offset), mag/1000.0)

		#
		# 3. Preload fonts
		#

		missing = []
		for k in fonts:
			_, s, d, fontname = fonts[k]
			log.debug("Font %s=%s" % (k, fontname))
			#print "Font %s=%s" % (k, fontname)
			try:
				fontsel.create_DVI_font(fontname, k, s, d, setup.options.enc_methods)
			except fontsel.FontError, e:
				log.error("Can't find font '%s': %s" % (fontname, str(e)))
				missing.append((k, fontname))

		if missing:
			log.info("There were some unavailable fonts, skipping file '%s'; list of missing fonts: %s" % (dvi.name, ", ".join("%d=%s" % kf for kf in missing)))
			continue

		#
		# 4. process pages
		#
		if setup.options.pages == None:	# processing all pages
			pages = range(0, n)
		else: # processing selected pages
			try:
				tmp   = utils.parse_pagedef(setup.options.pages, 1, n)
				pages = [p-1 for p in tmp]
			except ValueError, e:
				log.warning("Argument of --pages switch has invalid syntax ('%s'), processing first page", setup.options.pages)
				pages = [0]

		# ok, write the file
			
		scale = unit_mm * 72.27/25.4
		mag   = mag/1000.0
		try:
			mag *= float(setup.options.scale)
		except ValueError:
			pass

		if setup.options.generate_text:
			SVGDocument = SVGTextDocument
		else:
			SVGDocument = SVGGfxDocument

		if setup.options.single_file:
			svg = SVGDocument(1.25 * mag, scale, unit_mm, (pw,ph))
			for i, pageno in enumerate(pages):
				log.info("Procesing page %d (%d of %d)", pageno+1, i+1, len(pages))
				dvi.seek(page_offset[pageno])
				svg.new_page()
				convert_page(dvi, svg)

			svg.save(basename + ".svg")
		else:
			n = len(pages)
			for i, pageno in enumerate(pages):
				log.info("Procesing page %d (%d of %d)", pageno+1, i+1, n)
				dvi.seek(page_offset[pageno])
				svg = SVGDocument(1.25 * mag, scale, unit_mm, (pw,ph))
				svg.new_page()
				convert_page(dvi, svg)
				if n == 1 and not setup.options.always_number:
					svg.save(basename + ".svg")
				else:
					svg.save("%s%04d.svg" % (basename, pageno+1))

	sys.exit()

# vim: ts=4 sw=4 nowrap

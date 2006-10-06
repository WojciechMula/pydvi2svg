# pydvi2svg
# -*- coding: iso-8859-2 -*-
#
# Main program
# $Id: dvi2svg.py,v 1.5 2006-10-06 17:54:45 wojtek Exp $
# 
# license: BSD
#
# author: Wojciech Muła
# e-mail: wojciech_mula@poczta.onet.pl

'''
 6.10.2006
	- removed class fontDB, fontsel now provide these functions (*)
	- use logging module
	- added override encoding (--enc switch)
	- removed --update-cache switch
	- replaced --separate-files switch with --single-file
	- implemented --page-size switch

 4.10.2006
	- much smaller SVG output; characters with some scale factor
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
	- added command line supprt
	- fixed font scale calculation
	- added separate class that produce SVG documents

 30.09.2006
 	- version 0.1 (based on previous experiments)
'''

import sys
import os
import xml.dom
import logging

from sys  import stderr
from sets import Set

import dviparser
import fontsel
import setup

from binfile import binfile
from colors  import is_colorspecial, execute

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('dvi2svg')

class SVGDocument:
	def __init__(self, mag, scale, unit_mm, page_size):
		self.mag		= mag		# maginication
		self.scale		= scale		# additional scale
		self.oneinch	= 25.4/unit_mm

		self.id		= Set()
		self.pageno	= 0
		
		self.prevscale	= None
		self.prevy    	= None
		self.curblock	= None
		self.cury    	= None
		
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
		self.pageno += 1
		self.page = self.document.createElement('g')
		self.page.setAttribute('transform', 'scale(%f)' % self.mag)
		self.page.setAttribute('id', 'page%04d' % self.pageno)

		self.svg.appendChild(self.page)
		return self.page
	
	def put_char(self, h, v, fntnum, dvicode, color=None):
		self.id.add( (fntnum, dvicode) )
		idstring = "c%d-%02x" % (fntnum, dvicode)

		try:
			glyph, glyphscale, hadv = fontsel.get_char(fntnum, dvicode)
		except KeyError:
			return 0.0

		H  = self.scale * (h + self.oneinch)
		V  = self.scale * (v + self.oneinch)

		use = self.document.createElement('use')
		use.setAttributeNS('xlink', 'xlink:href', '#'+idstring)

		use.setAttribute('x', str( H/glyphscale))
		if color:
			use.setAttribute('style', 'fill:%s' % color)

		newscale = self.prevscale != glyphscale
		newy     = self.prevy != -V/glyphscale or newscale
			
		if newy and self.cury and len(self.cury.childNodes) == 1:
			tmp = self.cury.firstChild
			tmp.setAttribute('y', str(self.cury.ytransform))

			self.cury.removeChild(tmp)
			self.cury.parentNode.replaceChild(tmp, self.cury)
		
		if newscale and self.curblock and len(self.curblock.childNodes) == 1:

			tmp = self.curblock.firstChild
			if tmp.nodeName == 'use':
				scale = str(self.curblock.scale)
				tmp.setAttribute('transform', 'scale(%s,-%s)' % (scale, scale))
			
				self.curblock.removeChild(tmp)
				self.curblock.parentNode.replaceChild(tmp, self.curblock)

		if newscale:
			self.curblock = self.document.createElement('g')
			self.curblock.setAttribute('transform', 'scale(%s,%s)' % (str(glyphscale), str(-glyphscale)))
			self.curblock.scale = glyphscale
			self.page.appendChild(self.curblock)
			self.prevscale = glyphscale

		if newy:
			self.cury = self.document.createElement('g')
			self.cury.setAttribute('transform', 'translate(0,%s)' % str(-V/glyphscale))
			self.cury.ytransform = -V/glyphscale
			self.curblock.appendChild(self.cury)
			self.prevy = -V/glyphscale

		self.cury.appendChild(use)
		return hadv
	
	def put_rule(self, h, v, a, b, color=None):
		rect = self.document.createElement('rect')
		rect.setAttribute('x',      str(self.scale * (h + self.oneinch)))
		rect.setAttribute('y',      str(self.scale * (v - a + self.oneinch)))
		rect.setAttribute('width',  str(self.scale * b))
		rect.setAttribute('height', str(self.scale * a))
		if color:
			rect.setAttribute('fill', color)

		self.page.appendChild(rect)
	
	def save(self, filename, prettyXML=False):
		# create defs
		defs = self.document.createElement('defs')
		for fntnum, dvicode in self.id:
			try:
				glyph, scale, _ = fontsel.get_char(fntnum, dvicode)
			except KeyError:
				continue

			path = self.document.createElement('path')
			path.setAttribute("id", "c%d-%02x" % (fntnum, dvicode))
			path.setAttribute("d",  glyph)
			defs.appendChild(path)

		self.svg.insertBefore(defs, self.svg.firstChild)

		# save
		f = open(filename, 'wb')
		if prettyXML:
			f.write(self.document.toprettyxml())
		else:
			f.write(self.document.toxml())
		f.close()

def convert_page(dvi, document):

	h, v, w, x, y, z = 0,0,0,0,0,0	# DVI variables
	fntnum = None			# DVI current font number
	stack  = []			# DVI stack

	color  = None			# current color

	while dvi:
		command, arg = dviparser.get_token(dvi)
		if command == 'put_char':
			document.put_char(h, v, fntnum, arg, color)

		if command == 'set_char':
			h += document.put_char(h, v, fntnum, arg, color)

		elif command == 'nop':
			pass
		elif command == 'bop':
			h, v, w, x, y, z = 0,0,0,0,0,0
			fntnum  = None
		elif command == 'eop':
			break	# ok, we finished this page
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


def open_dvi(filename, mode, default_extension=None):
	try:
		dvi = binfile(filename, mode)
	except IOError, e:
		if default_extension:
			dvi = binfile(filename + default_extension, mode)
		else:
			raise e
	
	return dvi

def get_basename(filename):
	dotpos = filename.rfind('.')
	if dotpos > -1:
		return filename[:dotpos]
	else:
		return filename


def parse_pagedef(string, min, max):
	"""
	Parse page numbers. Examples:
		1,2,5,10	- selected single pages
		2-5		- range (2,5)
		-10		- range (min,10)
		15-		- range (15,max)

	>>> parse_pagedef("1,2,3,4,5", 1, 10)
	[1, 2, 3, 4, 5]
	>>> parse_pagedef("1,-5,2-7",  1, 10)
	[1, 2, 3, 4, 5, 6, 7]
	>>> parse_pagedef("1,5-,3-,2", 1, 10)
	[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
	"""
	assert min <= max
	def touint(string):
		try:
			x = int(string)
		except ValueError:
			raise ValueError("Number expeced, got %s" % string)

		if   x < min:
			raise ValueError("Number %d less then %d" % (x, min))
		elif x > max:
			raise ValueError("Number %d greater then %d" % (x, max))
		else:
			return x

	result = []
	for item in string.split(','):
		tmp = item.split('-')
		if   len(tmp) == 1:	# single page (number)
			result.append(touint(tmp[0]))
		elif len(tmp) == 2:	
			# open range (number-)
			if   tmp[0] == '':
				a = min
				b = touint(tmp[1])

			# open range (number-)
			elif tmp[1] == '':
				a = touint(tmp[0])
				b = max

			# range (number-number)
			else:              
				a = touint(tmp[0])
				b = touint(tmp[1])

			result.extend( range(a,b+1) )
		else:
			raise ValueError("Wrong syntax: %s" % item)
	#rof
	return list(Set(result))


def parse_enc_repl(string):
	# format:
	#  fontname:enc,fontname:enc,fontname=enc

	string = string.replace(':', '=')
	dict   = {}
	for item in string.split(','):
		try:
			fontname, enc = item.split('=')
			dict[fontname] = enc
		except ValueError:
			pass
	
	return dict
	

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
					  default=None)

	(options, args) = parser.parse_args()
	if not args:
		log.info("Nothing to do.")
		sys.exit()

	if options.enc_repl:
		fontsel.preload(parse_enc_repl(options.enc_repl))
	else:
		fontsel.preload()

	
	from paper_size import paper_size
	try:
		(pw, ph) = paper_size[options.paper_size.upper()]
		log.debug("Paper size set to %s (%dmm x %dmm)",
		          options.paper_size.upper(), pw, ph)
	except (KeyError, AttributeError):
		(pw, ph) = paper_size['A4']

	for filename in args:
	
		#
		# 1. Open file
		#
		dvi = open_dvi(filename, 'rb', '.dvi')
		log.info("Processing '%s' file", dvi.name) 

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

		# check if we support all fonts
		missing = fontsel.unavailable_fonts( (val[3] for val in fonts.itervalues()) )
		if missing:	# there are some unknown
			log.error("Following fonts aren't available:")
			log.error('\n'.join(missing))
			log.info("Skipping file '%s'" % dvi.name)
			continue

		else:		# ok, preload
			for k in fonts:
				_, s, d, fontname = fonts[k]
				fontsel.create_DVI_font(fontname, k, s, d)

		#
		# 4. process pages
		#
		if options.pages == None:	# processing all pages
			pages = range(0, n)
		else:				# processing selected pages
			try:
				tmp   = parse_pagedef(options.pages, 1, n)
				pages = [p-1 for p in tmp]
			except ValueError, e:
				log.warning("Argument of --pages switch has invalid syntax ('%s'), processing first page", options.pages)
				pages = [0]

		# ok, write the file
		basename = os.path.split(get_basename(dvi.name))[1]

			
		scale = unit_mm * 72.27/25.4
		mag   = mag/1000.0
		try:
			mag *= float(options.scale)
		except ValueError:
			pass

		if options.single_file:
			svg = SVGDocument(fontDB, mag, scale, unit_mm, (pw,ph))
			for i, pageno in enumerate(pages):
				log.info("Procesing page %d (%d of %d)", pageno+1, i+1, len(pages))
				dvi.seek(page_offset[pageno])
				svg.new_page()
				convert_page(dvi, svg)

			svg.save(basename + ".svg", options.prettyXML)
		else:
			for i, pageno in enumerate(pages):
				log.info("Procesing page %d (%d of %d)", pageno+1, i+1, len(pages))
				dvi.seek(page_offset[pageno])
				svg = SVGDocument(1.25 * mag, scale, unit_mm, (pw,ph))
				svg.new_page()
				convert_page(dvi, svg)
				svg.save("%s%04d.svg" % (basename, pageno+1), options.prettyXML)

	sys.exit(0)

# vim: ts=4 sw=4

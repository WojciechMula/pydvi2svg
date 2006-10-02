import sys
import os
import xml.dom

from sys  import stderr
from sets import Set

import dviparser
import fontsel

from color import is_colorspecial, execute

verbose_level = 1
def echo(s, verbose=0, halt=0):
	if verbose <= verbose_level:
		print >>stderr, s
	if halt:
		sys.exit(halt)

class FontDB:
	def __init__(self):
		self.fonts = {}

	def fnt_def(self, k, s, d, fnt):
		class Struct: pass
		font_info, glyphs = fontsel.get_font(fnt)

		info = Struct()
		info.name		= font_info[0]
		info.designsize		= font_info[1]
		info.max_height		= font_info[2]
		info.hadvscale		= float(s)/1000
		info.glyphscale		= float(s)/d * info.designsize/1000.0
		info.glyphs		= glyphs

		self.fonts[k] = info
		
	def get_char(self, k, dvicode):
		font  = self.fonts[k]
		glyph = font.glyphs[dvicode]

		path  = glyph[4]
		hadv  = glyph[3] * font.hadvscale
		return path, font.glyphscale, hadv

fontDB = FontDB()

class SVGDocument:
	def __init__(self, fontDB, mag, scale, unit_mm, page_size):
		self.fontDB	= fontDB
		self.mag	= mag		# maginication
		self.scale	= scale		# additional scale
		#self.oneinch	= 25.4/unit_mm
		self.oneinch	= 0.0

		self.id		= Set()
		
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
		self.page = self.document.createElement('g')
		self.svg.appendChild(self.page)
		return self.page
	
	def put_char(self, h, v, fntnum, dvicode, color=None):
		if not hasattr(self, 'page'):
			self.new_page()

		self.id.add( (fntnum, dvicode) )
		idstring = "c%d-%02x" % (fntnum, dvicode)

		path, glyphscale, hadv = self.fontDB.get_char(fntnum, dvicode)
		glyphscale = self.mag * glyphscale

		H  = self.mag * self.scale * (h + self.oneinch)
		V  = self.mag * self.scale * (v + self.oneinch)

		use = self.document.createElement('use')
		use.setAttributeNS('xlink', 'xlink:href', '#'+idstring)
		use.setAttribute('transform', 'scale(%f,%f) translate(%f,%f)' % (glyphscale, -glyphscale, H/glyphscale, -V/glyphscale))
		if color:
			use.setAttribute('style', 'fill:%s' % color)

		self.page.appendChild(use)
		return hadv
	
	def put_rule(self, h, v, a, b, color=None):
		if not hasattr(self, 'page'):
			self.new_page()

		rect = self.document.createElement('rect')
		rect.setAttribute('x',      str(self.mag * self.scale * (h + self.oneinch)))
		rect.setAttribute('y',      str(self.mag * self.scale * (v - a + self.oneinch)))
		rect.setAttribute('width',  str(self.mag * self.scale * b))
		rect.setAttribute('height', str(self.mag * self.scale * a))
		if color:
			rect.setAttribute('fill', color)

		self.page.appendChild(rect)
	
	def save(self, filename, prettyXML=False):
		# create defs
		defs = self.document.createElement('defs')
		for fntnum, dvicode in self.id:
			path = self.document.createElement('path')
			path.setAttribute("id", "c%d-%02x" % (fntnum, dvicode))
			path.setAttribute("d",  self.fontDB.get_char(fntnum, dvicode)[0])
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


def open_file(filename, mode, default_extension=None):
	try:
		file = open(filename, mode)
	except IOError, e:
		if default_extension:
			file = open(filename + default_extension, mode)
		else:
			raise e
	
	return file

def get_basename(filename):
	dotpos = filename.rfind('.')
	if dotpos > -1:
		return filename[:dotpos]
	else:
		return filename

from sets import Set

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

if __name__ == '__main__':
	import optparse
	
	parser = optparse.OptionParser()
	parser.add_option("--pretty-xml",
	                  action="store_true",
			  dest="prettyXML",
			  default=False)

	parser.add_option("--separate-files",
	                  action="store_true",
			  dest="separate_files",
			  default=False)

	parser.add_option("--pages",
	                  dest="pages")
	
	parser.add_option("--scale",
	                  dest="scale",
			  default=1.0)

	parser.add_option("--pages-sze",
	                  dest="page_size",
			  default="A4")

	(options, args) = parser.parse_args()
	for filename in args:
	
		#
		# 1. Open file
		#
		file = open_file(filename, 'rb', '.dvi')
		dvi  = dviparser.binfile(file)
		echo("Processing '%s' file" % file.name) 

		#
		# 2. Read DVI info	
		#
		comment, (num, den, mag, u, l), page_offset, fonts = dviparser.dviinfo(dvi)
		n       = len(page_offset)
		unit_mm = num/(den*10000.0)

		if mag == 1000: # not scaled
			echo("%s ('%s') has %d page(s)" % (file.name, comment, len(page_offset)), 2)
		else:           # not scaled
			echo("%s ('%s') has %d page(s); magnification %f times" % (file.name, comment, len(page_offset), mag/1000.0), 2)

		#
		# 3. Preload fonts
		#

		# check if we support all fonts
		missing = fontsel.unknown_fonts( (val[3] for val in fonts.itervalues()) )
		if missing:	# there are some unknown
			echo("Following fonts are unavailable:", 0)
			echo('\n'.join(missing), 0)
			echo("Skipping '%s'" % file.name, 0)
			continue

		else:		# ok, preload
			for k in fonts:
				_, s, d, fontname = fonts[k]
				fontDB.fnt_def(k,s,d,fontname)


		#
		# 4. process pages
		#
		if options.pages == None:	# processing all pages
			pages = range(0, n)
		else:				# processing selected pages
			tmp   = parse_pagedef(options.pages, 1, n)
			pages = [p-1 for p in tmp]

		# ok, write the file
		basename = os.path.split(get_basename(file.name))[1]

			
		scale = unit_mm * 72.27/25.4
		mag   = mag/1000.0 * 1.25
		try:
			mag *= float(options.scale)
		except ValueError:
			pass

		if options.separate_files:
			for i, pageno in enumerate(pages):
				echo("Procesing page %d (%d of %d)" % (pageno+1, i+1, len(pages)))
				dvi.seek(page_offset[pageno])
				svg = SVGDocument(fontDB, 1.25 * mag, scale, unit_mm, (210, 297))
				convert_page(dvi, svg)
				svg.save("%s%04d.svg" % (basename, pageno+1), options.prettyXML)
		else:
			svg = SVGDocument(fontDB, 1.25 * mag, scale, unit_mm, (210, 297))
			for i, pageno in enumerate(pages):
				echo("Procesing page %d (%d of %d)" % (pageno+1, i+1, len(pages)))
				dvi.seek(page_offset[pageno])
				convert_page(dvi, svg)

			svg.save(basename + ".svg", options.prettyXML)

	sys.exit(0)

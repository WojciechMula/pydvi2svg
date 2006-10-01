import sys
import xml.dom as DOM

import dviparser
import path_element
import fontsel

from color import is_colorspecial, execute

from sys import stderr

verbose_level = 0
def echo(s, verbose=0, halt=0):
	if verbose <= verbose_level:
		print >>stderr, s
	if halt:
		sys.exit(halt)

class FontDB:
	def __init__(self):
		self.ids   = {}
		self.fonts = {}

	def fnt_def(self, k, s, d, fnt):
		class Struct: pass
		font_info, glyphs = fontsel.get_font(fnt)

		info = Struct()
		info.name		= font_info[0]
		info.designsize		= font_info[1]
		info.max_height		= font_info[2]
		info.hadvscale		= float(s)/info.max_height
		info.glyphscale		= float(s)/d * info.designsize/1000.0
		info.glyphs		= glyphs

		self.fonts[k] = info
		
	def get_char(self, k, dvicode):
		self.ids[k,dvicode] = True

		id    = "c%d-%02x" % (k, dvicode)
		font  = self.fonts[k]
		glyph = font.glyphs[dvicode]

		path  = glyph[4]
		hadv  = glyph[3] * font.hadvscale
		return id, path, font.glyphscale, hadv
	
	def get_used_glyphs(self):
		result = []
		for k, dvicode in self.ids:
			font = self.fonts[k]
			path = font.glyphs[dvicode][4]
			result.append( ("c%d-%02x" % (k,dvicode), path) )
		return result

fontDB = FontDB()

def convert_page(dvi, document, page, fonts, mag, scale, hoff, voff):
	global def_id

	h, v, w, x, y, z = 0,0,0,0,0,0	# DVI varaibles
	fntnum = None			# DVI current font number
	stack  = []

	color  = None

	while True:
		command, arg = dviparser.get_token(dvi)
		if command == 'set_char':
			id, path, glyphscale, hadv = fontDB.get_char(fntnum, arg)

			glyphscale = mag * glyphscale

			H  = mag * scale * (h + hoff)
			V  = mag * scale * (v + voff)
			h += hadv

			use = document.createElement('use')
			use.setAttributeNS('xlink', 'xlink:href', '#'+id)
			use.setAttribute('transform', 'scale(%f,%f) translate(%f,%f)' % (glyphscale, -glyphscale, H/glyphscale, -V/glyphscale))
			if color:
				use.setAttribute('style', 'fill:%s' % color)
			page.appendChild(use)

		elif command == 'nop':
			pass
		elif command == 'bop':
			h, v, w, x, y, z = 0,0,0,0,0,0
			fntnum  = None
		elif command == 'eop':
			return page
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
			pass		# 'fonts' dictionary already contains this information
		elif command == "pre":
			raise ValueError("'pre' command is not allowed inside page - DVI corrupted")
		elif command == "post":
			raise ValueError("'post' command is not allowed inside page - DVI corrupted")
		elif command == "put_rule":
			a, b = arg
			rect = document.createElement('rect')
			rect.setAttribute('x',      str(mag * scale * (h + hoff)))
			rect.setAttribute('y',      str(mag * scale * (v-a + voff)))
			rect.setAttribute('width',  str(mag * scale * b))
			rect.setAttribute('height', str(mag * scale * a))
			page.appendChild(rect)
		elif command == "set_rule":
			a, b = arg
			rect = document.createElement('rect')
			rect.setAttribute('x',      str(mag * scale * (h + hoff)))
			rect.setAttribute('y',      str(mag * scale * (v-a + voff)))
			rect.setAttribute('width',  str(mag * scale * b))
			rect.setAttribute('height', str(mag * scale * a))
			page.appendChild(rect)

			h += b
		elif command == "xxx":	# special
			#print >>stderr, "'%s'" % arg
			if is_colorspecial(arg):
				color, background = execute(arg)
		else:
			raise NotImplementedError("Command '%s' not implemented." % command)


def convert(filename, pages, globalscale=1.0):
	global defs
	
	# prepare XML document
	implementation = DOM.getDOMImplementation()
	doctype = implementation.createDocumentType(
		"svg",
		"-//W3C//DTD SVG 1.1//EN",
		"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd")
	document = implementation.createDocument(None, "svg", doctype)

	# set SVG implementation
	svg      = document.documentElement
	svg.setAttribute  ('xmlns', 'http://www.w3.org/2000/svg')
	svg.setAttributeNS('xmlns', 'xmlns:xlink', "http://www.w3.org/1999/xlink")


	# load DVI file
	dvi = dviparser.binfile(open(filename, 'r'))

	comment, (num, den, mag, u, l), page_offset, fonts = dviparser.dviinfo(dvi)
	
	unsupported = fontsel.unknown_fonts( (val[3] for val in fonts.itervalues()) )
	if unsupported:
		print "Following SVG fonts dosn't exists: "
		print '\n'.join(unsupported)
		sys.exit()
	
	for k in fonts:
		_, s, d, fontname = fonts[k]
		fontDB.fnt_def(k,s,d,fontname)

	mm = num/(den*10000.0)
	for i, pagenum in enumerate(pages):
		scale = 72.27/25.4
		
		dvi.seek(page_offset[pagenum-1])
		page = document.createElement('g')
		page.setAttribute('transform', "translate(0, %f)" % (i*1.25*297) )
		page.setAttribute('id', 'page%03d' % pagenum)
		svg.appendChild(page)


		off   = 25.4/mm
		convert_page(dvi, document, page, fonts, 1.25*mag/1000.0, scale*mm, off, off)
	
	#svg.setAttribute('width',  "%fmm" % (u*mm))
	#svg.setAttribute('height', "%fmm" % (len(pages)*l*mm))
	#viewBox="0 0 1500 1000" preserveAspectRatio="none"
	#210x297 mm
	
	svg.setAttribute('width',  "210mm")
	#svg.setAttribute('height', "297mm")
	svg.setAttribute('height', "891mm")
	
	# create <defs> tag, to store glyphs
	defs = document.createElement('defs')
	svg.insertBefore(defs, svg.firstChild)

	for idstring, pathdef in fontDB.get_used_glyphs():
		path = document.createElement('path')
		path.setAttribute('id', idstring)
		path.setAttribute('d',  pathdef)
		defs.appendChild(path)

	dvi.close()
	return document

print convert(sys.argv[1], [1,2,3]).toprettyxml()

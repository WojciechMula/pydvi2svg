import dviparser
import path_element
import fontsel as fontDB
import xml.dom as DOM

import sys

from sys import stderr

def convert(filename, globalscale=5.0):
	
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
	svg.setAttribute('width', "500px")
	svg.setAttribute('height', "1000px")

	# create <defs> tag, to store glyphs
	defs = document.createElement('defs')
	def_id = {}
	
	svg.appendChild(defs)

	# load DVI file
	f = open(filename, 'r')
	r = dviparser.binfile(f.read())
	f.close()

	class FontInfo: pass

	font  = {} # info about loaded fonts
	stack = []

	h, v, w, x, y, z = 0,0,0,0,0,0	# DVI varaibles
	fntnum = None			# DVI current font number
	pageno = 0			# current page

	for (command, arg) in dviparser.tokenize(r):
		if command == 'set_char':
			fnt = font[fntnum]
			hadv, path = fontDB.get_glyph (fnt.name, arg)
			
			scale = globalscale * fnt.scale * fnt.pt_size/1000.0

			H  = globalscale * in_pt * h
			V  = globalscale * in_pt * v
			h += hadv * fnt.hadvscale

			'''
			id = "c%d-%d" % (fntnum, arg)
			if (fntnum,arg) not in def_id:
				element = document.createElement('path')
				element.setAttribute('d',  path)
				element.setAttribute('id', id)
				defs.appendChild(element)
				def_id[(fntnum,arg)] = id
			
			use = document.createElement('use')
			use.setAttribute('transform', 'scale(%f,%f) translate(%f,%f)' % (scale, -scale, H/scale, -V/scale))
			use.setAttributeNS('xlink', 'xlink:href', '#'+id)
			page.appendChild(use)
			'''

			tmp = path_element.tokens(path)
			tmp = path_element.scale(tmp, scale, -scale)
			tmp = path_element.translate(tmp, H, V)

			element = document.createElement('path')
			element.setAttribute('d',  path_element.to_path_string(tmp))
			page.appendChild(element)


		elif command == 'nop':
			pass
		elif command == 'bop':
			h, v, w, x, y, z = 0,0,0,0,0,0
			fntnum  = None
			pageno += 1

			page = document.createElement('g')
			page.setAttribute("id", "page%03d" % pageno)
			svg.appendChild(page)
		elif command == 'eop':
			break
			pass
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
			k, c, s, d, dir, fnt = arg
			
			info = FontInfo()

			info.name       = fnt
			info.scale      = (mag * s)/d
			info.pt_size    = 1
			info.hadvscale  = float(s)/fontDB.get_height(fnt)

			tmp = fnt
			while len(tmp):
				try:
					info.pt_size = float(tmp)
					break
				except ValueError:
					tmp = tmp[1:]
			
			font[k] = info
		elif command == "pre":
			(i, num, den, mag, comment) = arg
			in_mm = num/(den*10000.0)
			in_pt = (72.27*num)/(25.4*den*10000)
			mag   = mag/1000.0
		elif command == "post":
			break
		elif command == "put_rule":
			a, b = arg
			rect = document.createElement('rect')
			rect.setAttribute('x',      str(globalscale * in_pt*h))
			rect.setAttribute('y',      str(globalscale * in_pt*(v-a)))
			rect.setAttribute('width',  str(globalscale * in_pt*b))
			rect.setAttribute('height', str(globalscale * in_pt*a))
			page.appendChild(rect)
		elif command == "xxx":	# special
			pass
		else:
			raise NotImplementedError("Command '%s' not implemented." % command)

	return document


print convert(sys.argv[1]).toprettyxml()

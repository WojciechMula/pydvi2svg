# SVGfrags
#
# TODO: options parse, add option to hack, safe remove
# id based on file timestamp (to reasume purposes)

"""
 9.03.2007
	- parser
	- clean up
 8.03.2007
	- early tests
"""

import setup
import utils
import dvi2svg
import fontsel
from binfile import binfile
import dviparser
import frags

import xml.dom.minidom

import logging
import sys
import os


logging.basicConfig(level=logging.INFO)
log = logging.getLogger('SVGfrags')

class EquationsManager(dvi2svg.SVGGfxDocument):
	def __init__(self, doc, mag, scale, unit_mm):
		super(EquationsManager, self).__init__(mag, scale, unit_mm, (0,0))

		self.document = doc
		self.svg = self.document.documentElement

	def new_page(self):
		self.chars = []
		self.rules = []
		self.equation = None
		pass

	def eop(self):
		new = self.document.createElement
		scale2str = self.scale2str
		coord2str = self.coord2str

		element = new('g')
		xmin, ymin, xmax, ymax = self._get_page_bbox()
		self.equation = (element, xmin, ymin, xmax, ymax)

		# (TESTING)
		"""
		r = new('rect')
		r.setAttribute('x', str(xmin))
		r.setAttribute('y', str(ymin))
		r.setAttribute('width', str(xmax - xmin))
		r.setAttribute('height', str(ymax - ymin))
		r.setAttribute('fill', 'none')
		r.setAttribute('stroke', 'red')
		element.appendChild(r)
		"""

		# 1. make rules (i.e. filled rectangles)
		for (h,v, a, b, color) in self.rules:
			rect = new('rect')
			rect.setAttribute('x',      coord2str(self.scale * (h + self.oneinch)))
			rect.setAttribute('y',      coord2str(self.scale * (v - a + self.oneinch)))
			rect.setAttribute('width',  coord2str(self.scale * b))
			rect.setAttribute('height', coord2str(self.scale * a))
			if color:
				rect.setAttribute('fill', color)

			element.appendChild(rect)

		# 2. process chars
		from utils import group_elements as group

		# (fntnum, dvicode, next, H, V, glyphscale, color)

		# group chars with same glyphscale
		byglyphscale = group(self.chars, value=lambda x: x[5])
		for (glyphscale, chars2) in byglyphscale:
			g = new('g')
			g.setAttribute('transform', 'scale(%s,%s)' % (scale2str(glyphscale), scale2str(-glyphscale) ))
			element.appendChild(g)

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
		#for


setup.options.use_bbox = True
setup.options.prettyXML = True
setup.options.enc_methods = utils.parse_enc_methods("c,t")

# SVGfrags options
setup.options.frags_strip	= True
setup.options.frags_keeptex	= True
setup.options.frags_removetext = True
setup.options.frags_hideobject = True

if __name__ == '__main__':
#	input_txt = sys.argv[1]
#	input_svg = sys.argv[2]
	input_txt = 'test.txt'
	input_svg = 'b.svg'

	# 1. Load SVG file
	XML = xml.dom.minidom.parse(input_svg)

	# 1.1. Create 'defs' tag (if doesn't exists), and add xlink namespace
	if not XML.getElementsByTagName('defs'):
		XML.documentElement.insertBefore(
			XML.createElement('defs'),
			XML.documentElement.firstChild
		)

	if not XML.documentElement.getAttribute('xmlns:xlink'):
		XML.documentElement.setAttribute('xmlns:xlink', "http://www.w3.org/1999/xlink")

	if True:
		# XXX: hack; for unknown reason expat do not read id attribute
		# and getElementById always fails
		ID = {}
		frags.collect_Id(XML, ID)

		def my_getElementById(id):
			try:
				return ID[id]
			except KeyError:
				return None
		XML.getElementById = my_getElementById


	# 1.2. find all text objects
	text_objects = {}
	for item in XML.getElementsByTagName('text'):
		# use only raw text
		if len(item.childNodes) != 1:
			continue

		# one tspan is allowed
		if item.firstChild.nodeType == item.ELEMENT_NODE and \
		   item.firstChild.tagName == 'tspan':
		   	textitem = item.firstChild
		else:
			textitem = item

		# text node needed
		if textitem.firstChild.nodeType != item.TEXT_NODE:
			continue

		# strip whitespaces (if enabled)
		if setup.options.frags_strip:
			text = textitem.firstChild.wholeText.strip()
		else:
			text = textitem.firstChild.wholeText

		# add to list
		if text in text_objects:
			text_objects[text].append(item)
		else:
			text_objects[text] = [item]
	#for

	# 2. Load & parse replace pairs
	from frags.parser import parse
	repl_defs = [] # valid defs
	for item in parse(open(input_txt, 'r').read()):
		# (target, tex, px, py, scale, stw, sth, fit) = item
		kind, value = item[0] # target

		if kind == 'string':
			if setup.options.frags_strip:
				value = value.strip()
				item  = ((kind, value), ) + item[1:]

			if value in text_objects:
				repl_defs.append(item)
			else:
				log.warning("String '%s' doesn't found in SVG, skipping repl", value)

		elif kind == 'id':
			object = XML.getElementById(value[1:])
			if object:
				if object.nodeName in ['text', 'rect', 'ellipse', 'circle']:
					# "forget" id, save object
					item = ((kind, object), ) + item[1:]
					repl_defs.append(item)
				else:
					log.warning("Object with id=%s is not text, rect, ellipse nor circle - skipping repl", value)
			else:
				log.warning("Object with id=%s doesn't found in SVG, skipping repl", value)

		else: # point, rect -- no checks needed
			repl_defs.append(item)


	if True:
		# 3. prepare LaTeX source
		tmp_lines = [
			'\\documentclass{article}',
			'\\pagestyle{empty}'
			'\\begin{document}',
		]
		for item in repl_defs:
			tmp_lines.append(item[1])	# each TeX expression at new page
			tmp_lines.append("\\newpage")

		# 4. write & compile TeX source
		tmp_filename = "%08x-tmp" % os.getpid()
		tmp_lines.append("\end{document}")

		tmp = open(tmp_filename + '.tex', 'w')
		for line in tmp_lines:
			tmp.write(line + "\n")
		tmp.close()

		os.system("latex %s.tex > /dev/null" % tmp_filename)

		# 5. clean -- remove tmp.tex, tmp.aux, tmp.log
		if setup.options.frags_keeptex:
			for ext in ['aux', 'log']:
				os.remove('%s.%s' % (tmp_filename, ext))
		else:
			for ext in ['aux', 'log', 'tex']:
				os.remove('%s.%s' % (tmp_filename, ext))


	# 6. Load DVI
	dvi = binfile(tmp_filename + ".dvi", 'rb')
	comment, (num, den, mag, u, l), page_offset, fonts = dviparser.dviinfo(dvi)
	unit_mm = num/(den*10000.0)
	scale = unit_mm * 72.27/25.4
	mag   = mag/1000.0


	# 7. Preload fonts used in DVI & other stuff
	fontsel.preload()
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
		log.error("There were some unavailable fonts, skipping file '%s'; list of missing fonts: %s" % (dvi.name, ", ".join("%d=%s" % kf for kf in missing)))
		sys.exit(1)

	# 8. Substitute
	eq_id_n = 0

	SVG = EquationsManager(XML, 1.25 * mag, scale, unit_mm)
	for pageno, item in enumerate(repl_defs):
		dvi.seek(page_offset[pageno])
		SVG.new_page()
		dvi2svg.convert_page(dvi, SVG)
		assert SVG.equation is not None, "Fatal error!"

		(equation, xmin, ymin, xmax, ymax) = SVG.equation
		((kind, value), tex, px, py, scale, settowidth, settoheight, fit) = item

		def put_equation(x, y, sx, sy=None):

			# calculate desired point in equation BBox
			xo = xmin + (xmax - xmin)*px
			yo = ymin + (ymax - ymin)*py

			# move (xo,yo) to (x,y)
			if sy is None: # sx == sy
				equation.setAttribute(
					'transform',
					('translate(%s,%s)' % (SVG.c2s(x), SVG.c2s(y))) + \
					('scale(%s)'        %  SVG.s2s(sx)) + \
					('translate(%s,%s)' % (SVG.c2s(-xo), SVG.c2s(-yo)))
				)
			else:
				equation.setAttribute(
					'transform',
					('translate(%s,%s)' % (SVG.c2s(x), SVG.c2s(y))) + \
					('scale(%s,%s)'     % (SVG.s2s(sx), SVG.s2s(sy))) + \
					('translate(%s,%s)' % (SVG.c2s(-xo), SVG.c2s(-yo)))
				)
			return equation


		# string
		if kind == 'string':
			log.info("String '%s' is processing", value)


			# there is more then one text object, so
			# we have to **define** TeX object, and
			# reference to it, by <use>
			if len(text_objects[value]) > 1:
				eq_id    = 'svgfrags-%x' % eq_id_n
				eq_id_n += 1
				object = equation
				object.setAttribute('id', eq_id)
				XML.getElementsByTagName('defs')[0].appendChild(object)

			for object in text_objects[value]:

				# more then one reference, create new <use>
				if len(text_objects[value]) > 0:
					equation = XML.createElement('use')
					equation.setAttributeNS('xlink', 'xlink:href', '#'+eq_id)

				# get <text> object coords
				x = frags.safe_float(object.getAttribute('x'))
				y = frags.safe_float(object.getAttribute('y'))

				put_equation(x, y, scale)

				# insert equation into XML tree
				object.parentNode.insertBefore(equation, object)

				# modify existing object according to options
				if setup.options.frags_removetext:
					object.parentNode.removeChild(object)
				elif setup.options.frags_hideobject:
					object.setAttribute('display', 'none')


		# explicity given point
		elif kind == 'point':
			# insert equation into XML tree
			x, y = value
			XML.documentElement.appendChild(
				put_equation(x, y, scale)
			)

		# text object
		elif kind == 'id' and value.nodeName == 'text':
			object = value
			if settowidth or settoheight or fit:
				log.warning("%s is a text object, can't set width/height nor fit", value)

			# get <text> object coords
			x = frags.safe_float(object.getAttribute('x'))
			y = frags.safe_float(object.getAttribute('y'))

			put_equation(x, y, scale)

			# insert equation into DOM tree
			object.parentNode.insertBefore(equation, object)

			# modify existing object according to options
			if setup.options.frags_removetext:
				object.parentNode.removeChild(object)
			elif setup.options.frags_hideobject:
				object.setAttribute('display', 'none')

		# rectangle or object with known bbox
		elif kind == 'id' or kind == 'rect':
			# get bounding box
			if kind == 'rect':
				Xmin, Ymin, Xmax, Ymax = value # rect
			else:
				Xmin, Ymin, Xmax, Ymax = frags.get_bbox(value) # object

			DX = Xmax - Xmin
			DY = Ymax - Ymin

			# reference point
			x  = Xmin + (Xmax - Xmin)*px
			y  = Ymin + (Ymax - Ymin)*py

			# and set default scale
			sx = scale * SVG.mag
			sy = scale * SVG.mag

				
			# if set to width/height is set:
			if settowidth is not None or settoheight is not None:

				# value given by user
				if type(settowidth) is float:
					DX = abs(settowidth)

				# width of other object
				elif type(settowidth) is str and settowidth.startswith('#'):
					ref = XML.getElementById(settowidth[1:])
					if ref:
						try:
							Xmin, Xmax = frags.get_xbounds(ref)
							DX = Xmax - Xmin
						except ValueError, e:
							log.warning("Set to width ignored, bacause: '%s'", str(e))
					else:
						log.warning("Can't locate object %s", settowidth)

			
				# value given by user
				if type(settoheight) is float:
					DY = abs(settoheight)

				# height of other object
				elif type(settoheight) is str and settoheight.startswith('#'):
					ref = XML.getElementById(settoheight[1:])
					if ref:
						try:
							Ymin, Ymax = frags.get_ybounds(ref)
							DY = Ymax - Ymin
						except ValueError, e:
							log.warning("Set to height ignored, bacause: '%s'", str(e))
					else:
						log.warning("Can't locate object %s", settoheight)

				if settowidth is not None:
					sx = DX/(xmax - xmin)
				if settoheight is not None:
					sy = DY/(ymax - ymin)

			# Fit in rectangle
			elif fit:
				tmp_x = DX/(xmax - xmin)
				tmp_y = DY/(ymax - ymin)

				if tmp_x < tmp_y:
					sx = sy = tmp_x
				else:
					sx = sy = tmp_y
			#endif

			# move&scale equation
			put_equation(x, y, sx, sy)

			# and append to XML tree
			if kind == 'rect':
				XML.documentElement.appendChild(equation)
			else:
				# in case of existing objects, place them
				# just "above" them
				pn = value.parentNode
				if value == pn.lastChild:
					pn.appendChild(equation)
				else:
					pn.insertBefore(equation, value.nextSibling)
	#for


	SVG.save('xxx.svg')

	for ext in ['tex', 'dvi']:
		os.remove('%s.%s' % (tmp_filename, ext))

# vim: ts=4 sw=4 nowrap

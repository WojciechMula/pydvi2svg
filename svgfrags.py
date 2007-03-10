# SVGfrags
#
# TODO:
# * options parse, add option to hack,
# * colors inherit

"""
10.03.2007
	- group by TeX expression
	- id based on file timestamp & string hash (to reasume purposes)
	- keep old DVI & TeX fles
	- EquationsManager updated (SVGGfxDocument was changed)
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
		self.lastpage = None
		self.lastbbox = None
		pass

	def eop(self):
		scale2str = self.scale2str
		coord2str = self.coord2str

		g = self.document.createElement('g')
		self.lastpage = g
		self.lastbbox = self.get_page_bbox()

		for element in self.flush_rules() + self.flush_chars():
			g.appendChild(element)


		# (TESTING)
		"""
		r = self.document.createElement('rect')
		r.setAttribute('x', str(xmin))
		r.setAttribute('y', str(ymin))
		r.setAttribute('width', str(xmax - xmin))
		r.setAttribute('height', str(ymax - ymin))
		r.setAttribute('fill', 'none')
		r.setAttribute('stroke', 'red')
		element.appendChild(r)
		"""
		#for
	
	def save(self, filename):
		defs = self.document.getElementsByTagName('defs')[0]
		for element in self.flush_glyphs():
			defs.appendChild(element)

		# save file
		f = open(filename, 'wb')
		if setup.options.prettyXML:
			f.write(self.document.toprettyxml())
		else:
			f.write(self.document.toxml())
		f.close()


setup.options.use_bbox = True
setup.options.prettyXML = True
setup.options.enc_methods = utils.parse_enc_methods("c,t")

# SVGfrags options
setup.options.frags_strip	= True
setup.options.frags_keeptex	= False
setup.options.frags_keepdvi	= True
setup.options.frags_keepolderfiles = False
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
	input = open(input_txt, 'r').read()

	from frags.parser import parse
	repl_defs  = frags.Dict() # valid defs
	text_nodes = set()        # text nodes to remove/hide
	for item in parse(input):
		(target, tex, px, py, scale, stw, sth, fit) = item
		kind, value = target

		if kind == 'string':
			if setup.options.frags_strip:
				value = value.strip()
				item  = ((kind, value), ) + item[1:]

			try:
				for node in text_objects[value]:
					text_nodes.add(node)
					repl_defs[tex] = ((kind, node), ) + item[1:]
			except KeyError:
				log.warning("String '%s' doesn't found in SVG, skipping repl", value)

		elif kind == 'id':
			object = XML.getElementById(value[1:])
			if object:
				if object.nodeName in ['text', 'rect', 'ellipse', 'circle']:
					# "forget" id, save object
					repl_defs[tex] = ((kind, object), ) + item[1:]
				else:
					log.warning("Object with id=%s is not text, rect, ellipse nor circle - skipping repl", value)
			else:
				log.warning("Object with id=%s doesn't found in SVG, skipping repl", value)

		else: # point, rect -- no checks needed
			repl_defs[tex] = item


	# make tmp name based on hash input & timestamp of input_txt file
	tmp_filename = "svgfrags-%08x-%08x" % (input.__hash__(), os.path.getmtime(input_txt))
	if not os.path.exists(tmp_filename + ".dvi"):

		# 3. prepare LaTeX source
		tmp_lines = [
			'\\documentclass{article}',
			'\\pagestyle{empty}'
			'\\begin{document}',
		]
		for tex in repl_defs:
			tmp_lines.append(tex)	# each TeX expression at new page
			tmp_lines.append("\\newpage")

		# 4. write & compile TeX source
		tmp_lines.append("\end{document}")

		tmp = open(tmp_filename + '.tex', 'w')
		for line in tmp_lines:
			tmp.write(line + "\n")
		tmp.close()

		os.system("latex %s.tex > /dev/null" % tmp_filename)
	else:
		log.info("File not changed, used existing DVI file (%s)", tmp_filename)


	# 5. Load DVI
	dvi = binfile(tmp_filename + ".dvi", 'rb')
	comment, (num, den, mag, u, l), page_offset, fonts = dviparser.dviinfo(dvi)
	unit_mm = num/(den*10000.0)
	scale = unit_mm * 72.27/25.4
	mag   = mag/1000.0


	# 6. Preload fonts used in DVI & other stuff
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

	# 7. Substitute
	eq_id_n = 0

	SVG = EquationsManager(XML, 1.25 * mag, scale, unit_mm)
	for pageno, items in enumerate(repl_defs.values()):
		dvi.seek(page_offset[pageno])
		SVG.new_page()
		dvi2svg.convert_page(dvi, SVG)
		assert SVG.lastpage is not None, "Fatal error!"
		assert SVG.lastbbox is not None, "Fatal error!"
		(xmin, ymin, xmax, ymax) = SVG.lastbbox

		# there are more then one text object, so
		# we have to **define** TeX object, and
		# reference to it, by <use>
		if len(items) > 1:
			eq_id    = 'svgfrags-%x' % eq_id_n
			eq_id_n += 1
			SVG.lastpage.setAttribute('id', eq_id)
			XML.getElementsByTagName('defs')[0].appendChild(SVG.lastpage)
		else:
			equation = SVG.lastpage
			eq_id = None

		for item in items:
			((kind, value), tex, px, py, scale, settowidth, settoheight, fit) = item

			if eq_id is not None:
				# more then one reference, create new <use>
				equation = XML.createElement('use')
				equation.setAttributeNS('xlink', 'xlink:href', '#'+eq_id)

			
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
				object = value

				# get <text> object coords
				x = frags.safe_float(object.getAttribute('x'))
				y = frags.safe_float(object.getAttribute('y'))

				put_equation(x, y, scale)

				# insert equation into XML tree
				object.parentNode.insertBefore(equation, object)


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

	
	# modify existing object according to options
	if setup.options.frags_removetext:
		for node in text_nodes:
			node.parentNode.removeChild(node)
	elif setup.options.frags_hideobject:
		for node in text_nodes:
			node.setAttribute('display', 'none')

	
	SVG.save('xxx.svg')
	
	# 5. clean -- remove tmp.tex, tmp.aux, tmp.log
	extensions = ['aux', 'log']
	if not setup.options.frags_keeptex:
		extensions.append('tex')
	if not setup.options.frags_keepdvi:
		extensions.append('dvi')
	for ext in extensions:
		frags.remove_file('%s.%s' % (tmp_filename, ext))
	
	# 5a. remove outdated DVI & TeX files
	if not setup.options.frags_keepolderfiles:
		import glob
		for file in glob.glob(tmp_filename[:-8] + "????????.dvi"):
			if file != tmp_filename + ".dvi":
				frags.remove_file(file)
		for file in glob.glob(tmp_filename[:-8] + "????????.tex"):
			if file != tmp_filename + ".tex":
				frags.remove_file(file)


# vim: ts=4 sw=4 nowrap

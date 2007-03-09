# SVGfrags
#
# keep temporary file
# remove/hide

"""
w³±cznie parsera
wyszukiwanie po ID
wyrównywanie
rozci±ganie
"""

import setup
import utils
import dvi2svg
import fontsel
from binfile import binfile
import dviparser

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
	
	def new_page(self, object):
		self.chars = []
		self.rules = []
		self.object = object
		pass

	def eop(self):
		new  = self.document.createElement
		scale2str = self.scale2str
		coord2str = self.coord2str

		x = float(self.object.getAttribute('x'))
		y = float(self.object.getAttribute('y'))

		page = new('g')

		self.object.setAttribute('display', 'none')
		self.object.parentNode.insertBefore(page, self.object)
#		self.object.parentNode.removeChild(self.object)
		
		# 0. get bounding box (if needed)
		xmin, ymin, xmax, ymax = self._get_page_bbox(page)

		"""
		r = new('rect')
		r.setAttribute('x', str(xmin))
		r.setAttribute('y', str(ymin))
		r.setAttribute('width', str(xmax - xmin))
		r.setAttribute('height', str(ymax - ymin))
		r.setAttribute('fill', 'none')
		r.setAttribute('stroke', 'red')
		page.appendChild(r)
		"""
		

		fx = 0.5
		fy = 0.5

		xo = xmin + (xmax-xmin)*fx
		yo = ymin + (ymax-ymin)*fy
		
		dx = xo - x
		dy = yo - y

		t1 = 'translate(%s,%s)' % (coord2str(-xo), coord2str(-yo))
		s1 = 'scale(%s)' % str(self.mag)
		t2 = 'translate(%s,%s)' % (coord2str(x), coord2str(y))
		
		page.setAttribute('transform', ' '.join([t2, s1, t1]))

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
	

setup.options.use_bbox = True
setup.options.prettyXML = True

setup.options.enc_methods = utils.parse_enc_methods("c,t")

substs = {
	'A'		: '$\sin x + \cos x = 1$',
	"C'"	: '$\\frac{1}{x^2 + 1}$',
	"D"		: '\[P(t) = \sum_{i=0}^n p_i \cdot B_i^n(t)\]',
	"B"		: '\LaTeX\ \& \TeX !!!',
}

if __name__ == '__main__':
		filename = 'temporary'

		L = [
			'\\documentclass{article}',
			'\\pagestyle{empty}'
			'\\begin{document}',
		]
		for i, key in enumerate(substs):
			if i != 0: L.append("\\newpage")
			L.append(substs[key])

		L.append("\end{document}")

		file = open(filename + ".tex", 'w')
		for item in L:
			file.write(item + "\n")
		file.close()
		os.system("latex " + filename)

		dvi = binfile(filename + ".dvi", 'rb')
		comment, (num, den, mag, u, l), page_offset, fonts = dviparser.dviinfo(dvi)
		unit_mm = num/(den*10000.0)
		scale = unit_mm * 72.27/25.4
		mag   = mag/1000.0
		try:
			mag *= float(setup.options.scale)
		except ValueError:
			pass

		fontsel.preload()
		
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
			log.error("There were some unavailable fonts, skipping file '%s'; list of missing fonts: %s" % (dvi.name, ", ".join("%d=%s" % kf for kf in missing)))
			sys.exit(1)

		doc  = xml.dom.minidom.parse('b.svg')

		doc.documentElement.setAttribute('xmlns:xlink', "http://www.w3.org/1999/xlink")
		textitems = doc.getElementsByTagName('text')
		svg = EquationsManager(doc, 1.25 * mag, scale, unit_mm)
		for pageno, key in enumerate(substs):
			for text in textitems:
				if text.firstChild.wholeText == key:
					dvi.seek(page_offset[pageno])
					svg.new_page(text)
					dvi2svg.convert_page(dvi, svg)
					break

		svg.save('xxx.svg')

# vim: ts=4 sw=4 nowrap

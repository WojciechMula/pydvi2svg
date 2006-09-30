import re
import os
import cPickle

PATH = '/home/wojtek/prog/dvisvg/fonts/'

re_mapping = re.compile("^([0-9a-fA-F]{4}) N (.+)")

class SVGFont:
	def __init__(self, fontname):
		self.max_height = None
		self.glyphs     = {}
		
		# load data
		from xml.dom.minidom import parse
		data = parse(PATH + fontname + ".svg")
		font = data.getElementsByTagName('font')
		assert len(font) == 1
		font = font[0]

		mapping = {}

		f = open(PATH + fontname + '.cfg')
		for line in f:
			match = re_mapping.match(line)
			if match:
				code = int(match.group(1), 16)
				name = match.group(2)
				if name in mapping:
					mapping[name].append(code)
				else:
					mapping[name] = [code]

		f.close()

		# font has default width?
		if font.hasAttribute('horiz-adv-x'): 
			default_hadvx = float(font.getAttribute('horiz-adv-x'))

		# get info about font, if any
		font_face = font.getElementsByTagName('font-face')
		if len(font_face) == 1:
			font_face = font_face[0]
			if font_face.hasAttribute('bbox'):
				bbox = font_face.getAttribute('bbox')
				minx,miny, maxx,maxy = [float(v) for v in bbox.split()]
				self.max_height = maxy - miny
		
		# read info about glyphs
		for glyph in font.getElementsByTagName('glyph'):

			if not glyph.hasAttribute('d'):
				path = None
			else:
				path = glyph.getAttribute('d')

			# get horiz-adv-x
			if glyph.hasAttribute('horiz-adv-x'):
				hadvx = float(glyph.getAttribute('horiz-adv-x'))
			else:
				try:
					hadvx = default_hadvx
				except NameError:
					# calculate glyphs extends
					raise NotImplementedError

			name = glyph.getAttribute('glyph-name')
			for code in mapping[name]:
				self.glyphs[code] = (hadvx, path)

font_cache = {}

def get_glyph(fontname, code):
	global font_cache
	fontname = fontname.upper()
	if fontname not in font_cache:
		try:	
			# does we pickled the font?
			font_cache[fontname] = cPickle.load(open(PATH + fontname + ".pickle"))
		except IOError:
			font = SVGFont(PATH + fontname + ".svg", [])
			font_cache[fontname] = font
			cPickle.dump(font, open(PATH + fontname + ".pickle", 'w'))
	
	# get font
	font = font_cache[fontname]

	# and selected glyph
	if code not in font.glyphs:
		raise ValueError("%s %d (%04x) %s" % (fontname, code, code, str(font.glyphs.keys())))
	hadv, path = font.glyphs[code]
	return (hadv, path)

def get_height(fontname):
	global font_cache
	fontname = fontname.upper()
	if fontname not in font_cache:
		try:	
			# does we pickled the font?
			font_cache[fontname] = cPickle.load(open(PATH + fontname + ".pickle"))
		except IOError:
			# no, so load the font and pickle for futher use
			font = SVGFont(fontname)
			font_cache[fontname] = font
			cPickle.dump(font, open(PATH + fontname + ".pickle", 'w'))
	
	# get font maxheight
	return font_cache[fontname].max_height

# vim: ts=4 sw=4

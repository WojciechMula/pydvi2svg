import sys
import re
import os
import cPickle

svg_font_path	= '/home/wojtek/prog/fonts/'
cache_path		= '/home/wojtek/prog/fonts/'


verbose_level = 1

def info(string, verbose=0, halt=0):
	if verbose <= verbose_level:
		print >>sys.stderr, string
	if halt:
		sys.exit(halt)

def is_dir_ok(path):
	"""Test if PATH variable points to the correct location"""
	if not os.path.exists(path):
		raise IOError("Path '%s' does not exists" % path)
	
	if not os.path.isdir(path):
		raise IOError("'%s' it not a directory" % path)
	
	return path

class FontError(Exception):
	pass


re_number	= re.compile('(\d+)')
re_mapping	= re.compile("^([0-9a-fA-F]{4}) N (.+)")
def make_cache_file(fontname, designsize=None, encoding=None):
	dir  = os.listdir(is_dir_ok(svg_font_path))
	
	fontname = fontname.lower()
	dirl = [name.lower() for name in dir]

	# locate SVG
	try:
		s = dirl.index(fontname + '.svg')
	except ValueError:
		raise FontError("No SVG fonts found for '%s'" % fontname)
	else:
		info("There is SVG font %s" % dir[s], 1)
	
	# set encoding
	# TODO: provide set of standard TeX encodings
	if encoding == None:
		try:
			e = dirl.index(fontname + '.cfg')
		except ValueError:
			raise FontError("No CFG file found for '%s'" % fontname)
		else:
			info("No encoding given, but file %s should contain it" % dir[e], 1)
			encoding = {}
			for line in open(svg_font_path + dir[e], 'r'):
				match = re_mapping.match(line)
				if match:
					dvicode = int(match.group(1), 16)
					assert dvicode < 256

					name    = match.group(2)
					# more then one dvicode can be mapped on single glyph
					if name in encoding:
						encoding[name].append(dvicode)
					else:
						encoding[name] = [dvicode]

			if not len(encoding):
				raise FontError("File %s doesn't contain encoding information." % dir[e])
				No
	else:
		raise NotImplementedError

	# get designsize
	# TODO: read this info from TFM files
	if designsize == None:
		res = re_number.search(fontname)
		if res:
			designsize = float(res.group(1))
	if designsize == None:
		info("No design size resolved")
		designsize = 10.0

	# 2. Process SVG file
	
	# a. load file
	from xml.dom.minidom import parse
	data = parse(svg_font_path + dir[s])

	# b. get font element
	font = data.getElementsByTagName('font')
	if len(font) < 1:
		raise FontError("There should be at least one <font> element in SVG file")
	
	if len(font) > 1:
		# XXX: FontForge do not output more then 1
		info("There are more then one font definition in the file, using only first")
	font = font[0]
	
	# c. get default horizontal advance if any
	if font.hasAttribute('horiz-adv-x'): 
		default_hadvx = float(font.getAttribute('horiz-adv-x'))
	else:
		default_hadvx = None

	# d. get max height
	max_height = None
	font_face = font.getElementsByTagName('font-face')
	if len(font_face) == 1:
		font_face = font_face[0]
		if font_face.hasAttribute('bbox'):
			bbox = font_face.getAttribute('bbox')
			minx,miny, maxx,maxy = [float(v) for v in bbox.split()]
			max_height = maxy - miny
		
	if max_height == None:
		# TODO: use function bounding_box from path_element.py
		raise FontError("Can't determine max height of glyphs")
	
	# e. load fonts
	glyphs = {}
	for glyph in font.getElementsByTagName('glyph'):

		# 1. read path info
		path = None
		if glyph.hasAttribute('d'):	# is defined as <glyph> attribute
			path = glyph.getAttribute('d')
		else:
			# XXX: glyph is defined using childNodes and I assume
			#      there is just one path element
			path_elements = glyph.getElementsByTagName('path')
			if len(path_elements) == 0:		# no path elements at all
				pass
			elif len(path_elements) == 1:	# one path element
				path = path_elements[0].getAttribute('d')
			else: # more path
				pass # XXX: join them?

		# 2. get horiz-adv-x
		if glyph.hasAttribute('horiz-adv-x'):
			hadvx = float(glyph.getAttribute('horiz-adv-x'))
		else:
			try:
				hadvx = default_hadvx
			except NameError:
				# TODO: calculate glyphs extends
				raise NotImplementedError

		name = glyph.getAttribute('glyph-name')
		if name == "space":
			unicode = u" "
		else:
			unicode = glyph.getAttribute('unicode')

		for dvicode in encoding[name]:
			glyphs[dvicode] = (dvicode, unicode, name, hadvx, path)

	# write the cache file
	font_info  = (fontname, designsize, max_height)
	glyph_list = []
	for dvicode in xrange(256):
		if dvicode in glyphs:
			glyph_list.append(glyphs[dvicode])
		else:
			glyph_list.append(None)
	
	font = (font_info, glyph_list)
	cPickle.dump(font, open(cache_path + fontname + '.cache', 'wb'), protocol=cPickle.HIGHEST_PROTOCOL)

font_cache = {}

def get_font(fontname):
	try:
		font = font_cache[fontname]
		info("%s already in cache" % fontname, 3)
	except KeyError:
		try:
			font_cache[fontname] = font = cPickle.load(open(cache_path + fontname.lower() + '.cache', 'rb'))
			info("%s loaded from cache file" % fontname, 3)
		except:
			make_cache_file(fontname)
			font_cache[fontname] = font = cPickle.load(open(cache_path + fontname.lower() + '.cache', 'rb'))
			info("%s created new cache file" % fontname, 3)
	
	return font

def glyph_info(fontname, dvicode):
	return get_font(fontname)[1][dvicode]

def font_info(fontname):
	return get_font(fontname)[0]
	
def unknown_fonts(fontnames):
	dir  = [name.lower() for name in os.listdir(is_dir_ok(svg_font_path))]
	list = []
	for fontname in fontnames:
		if (fontname.lower()+'.svg') not in dir:
			list.append(fontname)
	return list

# vim: ts=4 sw=4

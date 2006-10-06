# pydvi2svg
# -*- coding: iso-8859-2 -*-
#
# SVG font & char encoding utilities
# $Id: fontsel.py,v 1.5 2006-10-06 17:56:08 wojtek Exp $
# 
# license: BSD
#
# author: Wojciech Muła
# e-mail: wojciech_mula@poczta.onet.pl

__changelog__ = '''
 6.10.2006
 	- added fontDB functions:
		- load fonts at given scale (create_DVI_font)
		- get glyph data, its scale and hadv for given char (get_char)
	- ovrride encoding of font
	- permanently modify encoding (change file setup.font_lookup)
 5.10.2006
	- removed unused function
	- use logging module
 2.10.2006
    - remove SVGFont class
	- added following functions:
		* make_cache_file
		* get_glyph
		* get_height
		* glyph_info
		* font_info
		* unknown_fonts
 1.10.2006
 	- moved font releated functions from main program here
'''

import sys
import re
import os
import cPickle
import logging

import setup
import findfile

from binfile  import binfile
from metrics  import read_TFM, TFMError, read_AFM, AFMError, read_MAP
from encoding import EncodingDB, EncodingDBError

# create encodingDB instance
encodingDB	= EncodingDB(setup.encoding_path, setup.tex_paths)

# get logger
log 		= logging.getLogger('fonts')

class FontError(Exception):
	pass

class Config(object):
	pass

config = Config()

# table using to translate long encoding names into shorter form
config.encoding_lookup	= {}

# dict contains trivial info about fonts: its
# encoding name (short form) and design size
config.fonts_lookup		= {}

# loaded fonts
config.fonts			= {}

# created DVI fonts
config.dvi_fonts		= {}

def create_DVI_font(fontname, k, s, d):
	"""
	Create a font identified by number k scaled with factor s/d.
	If encoding is None, then use default encoding assigned
	to fontname.
	"""

	# load font
	fontdata = load_font(fontname)

	class DVIFont:
		pass

	font = DVIFont()
	font.name			= fontname
	font.scale			= float(s)/d * fontdata.designsize/1000.0
	font.hadvscale		= float(s)/1000
	font.glyphs_dict	= fontdata.glyphs_dict
	font.encoding		= encodingDB.getencodingtbl(fontdata.encoding)

	config.dvi_fonts[k] = font

def get_char(fontnum, dvicode):
	"""
	Returns following data releated to character:
	- glyph (shape)
	- shape scale factor needed to fit current font size
	- width of char in TeX units
	"""
	font = config.dvi_fonts[fontnum]

	glyphname = font.encoding[dvicode]
	try:
		glyph = font.glyphs_dict[glyphname]
		return glyph.path, font.scale, glyph.hadv * font.hadvscale
	except KeyError, e:
		log.error("%s: missing char '%s'" % (font.name, glyphname))
		raise e

def preload(enc_repl={}):
	log.debug("Loading encoding names lookup from '%s'" % setup.enc_lookup)
	load_enc_lookup()
	
	log.debug("Loading font info from '%s'" % setup.font_lookup)
	load_font_info()
	for fontname, newenc in enc_repl.iteritems():
		if fontname not in config.fonts_lookup:
			continue

		enc, ds = config.fonts_lookup[fontname]
		if enc != newenc:
			log.debug("Encoding of '%s' set to %s", fontname, newenc)
			config.fonts_lookup[fontname] = (newenc, ds)


def load_font(fontname):
	try:
		font = config.fonts[fontname]
		log.debug("Getting font '%s' from cache" % fontname)
	except KeyError:
		filename = os.path.join(setup.cache_path + fontname.lower() + '.cache')
		if not os.path.exists(filename):
			log.debug("Cache file for '%s' font does not exists -- creating it" % fontname)
			make_cache_file(fontname)
			config.fonts[fontname] = font = cPickle.load(open(filename, 'rb'))
		else:
			log.debug("Loading font '%s' from cache file" % fontname)
			config.fonts[fontname] = font = cPickle.load(open(filename, 'rb'))

	if fontname in config.fonts_lookup:
		if font.encoding != config.fonts_lookup[fontname][0]:
			newencoding = config.fonts_lookup[fontname][0]
			log.debug("Overriding font encoding (%s->%s)" % (font.encoding, newencoding))
			font.encoding = newencoding

	return font
	

def load_enc_lookup():
	try:
		file = open(setup.enc_lookup, 'r')
		log.debug("Parsing file '%s'..." % setup.enc_lookup)
	except IOError:
		log.debug("... file '%s' not found" % setup.enc_lookup)

	for i, line in enumerate(file):
		# skip blank or commented lines
		line = line.strip()
		if not line or line[0] == '#':
			continue

		try:
			# line not empty, parse
			eqpos = line.rfind('=')
			if eqpos > -1:
				encodingname, encfile = line.rsplit('=', 2)
				encodingname = encodingname.strip()
				encfile      = encfile.strip()
				config.encoding_lookup[encodingname] = encfile
				log.debug("... line %d: '%s'=%s" % (i+1, encodingname, encfile))
			else:
				raise ValueError
		except ValueError:
			# wrong number of fields
			log.warning("... line %d has wrong format, skipping" % (i+1))
			continue
	
	file.close()

def load_font_info():
	try:
		file = open(setup.font_lookup, 'r')
		log.debug("Parsing file '%s'..." % setup.font_lookup)
	except IOError:
		log.debug("... file '%s' not found" % setup.font_lookup)
		return

	for i, line in enumerate(file):
		# skip blank or commented lines
		line = line.strip()
		if not line or line[0] == '#':
			continue

		try:
			fontname, encoding, designsize = line.split()
			if fontname not in config.fonts_lookup:
				config.fonts_lookup[fontname] = (encoding, float(designsize))
				log.debug("... line %d: %s @ %spt, enc. %s" % (
					i+1,
					fontname,
					str(float(designsize)),
					encoding,
				))
			else:
				log.warning("... line %d: font %s - duplicated entry ignored" % (i+1, fontname))
		except ValueError:
			# wrong number of fields
			log.waring("... line %d has wrong format, skipping" % (file.name, i+1))
			continue
	
	file.close()


tex_map_file_list = None
def get_encoding(fontname, checktfm=True, checkafm=True, grepmap=False):
	global tex_map_file_list
	"""
	Function (tries to) determine encoding of given font.

	Does following steps:
	- first checks a cache (loaded from setup.font_lookup)
	- if grepmap==True grep for all map files and find if fontname.(pfa|pfb)
	  is mapped
	- if checktfm==True seeks for corresponding TFM file and reads encoding name
	- if checkafm==True seeks for corresponding AFM file and reads encoding name
	"""
	if fontname in config.fonts_lookup:
		encoding, designsize = config.fonts_lookup[fontname]
		log.debug("... encoding %s (got from '%s')" % (encoding, setup.font_lookup))
		return (False, encoding)
	
	if grepmap:
		log.debug("... checking map files")
		if tex_map_file_list != None:
			log.debug("... ... list of map files is present.")
		else:
			log.debug("... ... list of map files dosn't exists - getting one (it may take a while...)")
			tex_map_file_list = findfile.find_all(setup.tex_paths, ".map")

		for filename in tex_map_file_list:
			log.debug("... ... ... scanning %s" % filename)
			enc = read_MAP(filename, fontname)
			if enc:
				log.debug("... ... ... encoding %s" % enc)
				return enc
	
	if checktfm:
		log.debug('... checking TFM file')
		filename = findfile.locate(fontname + '.tfm')
		if filename:
			log.debug("... ... using '%s'" % filename)
			file = binfile(filename, 'rb')
			try:
				_, _, encodingname, _ = read_TFM(file)
			except TFMError, e:
				log.error("... ... TFM error: %s" % str(TFMError))
			else:
				file.close()
				try:
					encoding = config.encoding_lookup[encodingname]
					log.debug("... ... encoding %s" % encoding)
					return (True, encoding)
				except KeyError:
					log.error("... ... font %s: unknown TeX encoding: '%s'" % (fontname, encodingname))
		else:
			log.debug("... ... TFM file not found")
	
	
	if checkafm:
		log.debug('... checking AFM file')
		filename = findfile.locate(fontname + '.afm')
		if filename:
			log.debug("... ... using '%s'" % filename)
			file = open(filename, 'r')
			try:
				encodingname, _, _ = read_AFM(file)
			except AFMError, e:
				log.error("... ... AFM error" + str(AFMError))
			else:
				file.close()
				try:
					if encodingname:
						encoding = config.encoding_lookup[encodingname]
						log.debug("... ... ... encoding %s" % encoding)
						return (True, encoding)
					else:
						log.error("... ... unknown AFM encoding: '%s'" % encodingname)
				except KeyError:
					log.error("... ... unknown AFM encoding: '%s'" % encodingname)
		else:
			log.debug("... ... AFM file not found")
	

	# encoding not resolved
	return (False, None)
		
		
def get_designsize(fontname):
	global tex_map_file_list
	"""
	Function (tries to) determine designsize of given font.

	Does following steps:
	- first checks a cache (loaded from setup.font_lookup)
	- if checktfm==True seeks for corresponding TFM file and reads designsize name
	"""
	if fontname in config.fonts_lookup:
		encoding, designsize = config.fonts_lookup[fontname]
		log.debug("Getting designsize for '%s' from file cache" % fontname)
		return designsize

	# read TFM, if any
	log.debug('Checking TFM file...')
	filename = findfile.locate(fontname + '.tfm')
	if filename:
		log.debug("Using file '%s'" % filename)
		file = binfile(filename, 'rb')
		try:
			_, designsize, _, _ = read_TFM(file)
		except TFMError, e:
			log.error("TFM error" + str(TFMError))
		else:
			file.close()
			return designsize / (2.0**20)
	else:
		log.warning("No TFM file found, default value 10.0 have been assumed")
		return 10.0
	
re_number	= re.compile('(\d+)')
re_mapping	= re.compile("^([0-9a-fA-F]{4}) N (.+)")
	
class Font:
	pass

class Glyph:
	def __init__(self):
		self.path    = None
		self.unicode = u""
		self.name    = ""

def make_cache_file(fontname):

	font = Font()
	font.name = fontname
	
	# locate SVG
	filename = findfile.findfile(fontname + '.svg', setup.svg_font_path, ignorecase=True)
	if filename:
		log.debug("Using SVG font '%s' as '%s'", filename, font.name)
	else:
		raise FontError("Can't find SVG font for '%s'" % font.name)
	
	# get designsize & encoding
	font.designsize = get_designsize(fontname)
	log.debug("Font '%s' designed at %spt" % (fontname, str(font.designsize)))
	newfile, font.encoding = get_encoding(fontname)
	if font.encoding == None:
		raise FontError("Can't determine encoding for font '%s'", font.name)
	else:
		log.debug("Font '%s' encoding is %s", font.name, font.encoding)
	
	if newfile:
		log.debug("Adding information about new font to '%s': %s@%fpt, enc. %s" % (
			setup.font_lookup,
			font.name,
			font.designsize,
			font.encoding)
		)
		file = open(setup.font_lookup, 'a')
		file.write("%s\t\t%s\t\t%s\n" % (font.name, font.encoding, str(font.designsize)))
		file.close()
	
	# 2. Process SVG file
	
	# a. load file
	from xml.dom.minidom import parse
	data = parse(filename)

	# b. get font element
	try:
		fontnode = data.getElementsByTagName('font')[0]
		# get default horizontal advance if any
		if fontnode.hasAttribute('horiz-adv-x'): 
			default_hadvx = float(fontnode.getAttribute('horiz-adv-x'))
		else:
			default_hadvx = None
	except IndexError:
		raise FontError("There should be at least one <font> element in SVG file")

	# d. load fonts
	font.glyphs_dict = {}
	for node in fontnode.getElementsByTagName('glyph'):

		# 1. read path info
		glyph = Glyph()
		if node.hasAttribute('d'):	# is defined as <glyph> attribute
			glyph.path = node.getAttribute('d')
		else:
			# XXX: glyph is defined using childNodes and I assume
			#      there is just one path element
			path_elements = node.getElementsByTagName('path')
			if len(path_elements) == 0:		# no path elements at all
				pass
			elif len(path_elements) == 1:	# one path element
				glyph.path = path_elements[0].getAttribute('d')
			else: # more paths
				pass # XXX: join them?
		
		# 2. get character name
		glyph.name = node.getAttribute('glyph-name')
		if  glyph.name == '':
			log.error("There is a glyph without name, skipping it")
			continue
		elif glyph.name == "space":
			glyph.unicode = u" "
		else:
			glyph.unicode = node.getAttribute('unicode')

		# 3. get horiz-adv-x
		if node.hasAttribute('horiz-adv-x'):
			glyph.hadv = float(node.getAttribute('horiz-adv-x'))
		elif default_hadvx != None:
			glyph.hadv = default_hadvx
		else:
			# XXX: calculate glyphs extends?
			raise FontError("Can't determine width of character '%s'", glyph.name)

		if glyph.name in font.glyphs_dict:
			log.error("Character '%s' already defined, skipping", glyph.name)
		else:
			font.glyphs_dict[glyph.name] = glyph
	#rof

	# e. write the cache file
	cPickle.dump(font, open(setup.cache_path + fontname + '.cache', 'wb'), protocol=cPickle.HIGHEST_PROTOCOL)

def is_font_supported(fontname):
	return findfile.findfile(fontname + ".svg", setup.svg_font_path, ignorecase=True) != None
	
def unavailable_fonts(fontslist):
	return [fontname for fontname in fontslist if not is_font_supported(fontname)]

# vim: ts=4 sw=4

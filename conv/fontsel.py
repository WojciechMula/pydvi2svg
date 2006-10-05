# pydvips v0.8
# -*- coding: iso-8859-2 -*-
#
# SVG font & char encoding utilities
# 
# license: BSD
#
# author: Wojciech Muła
# e-mail: wojciech_mula@poczta.onet.pl

__changelog__ = '''
5.10.2006
	- removed unused function
	- use logging module
'''

import sys
import re
import os
import cPickle
import logging

import setup
import findfile

from binfile import binfile
from metrics import read_TFM, TFMError, read_AFM, AFMError, read_MAP

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger('fonts')

class FontError(Exception):
	pass

class Config(object):
	pass

config = Config()

# table using to translate long encoding names into shorter form
config.encoding_lookup = {}

# table using to retrieve trivial info about given font: its
# encoding name (short form) and design size
config.fonts_lookup    = {}

def init():
	log.info("Loading encoding names lookup from '%s'" % setup.enc_lookup)
	load_enc_lookup()
	
	log.info("Loading font info from '%s'" % setup.font_lookup)
	load_font_info()

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
			fontname, encodingname, designsize = line.split()
			if fontname not in config.fonts_lookup:
				config.fonts_lookup[fontname] = (encodingname, float(designsize))
				log.debug("... line %d: %s @ %spt, enc. %s" % (
					i+1,
					fontname,
					str(float(designsize)),
					encodingname,
				))
			else:
				log.warning("... line %d: font %s - duplicated entry ignored" % (i+1, fontname))
		except ValueError:
			# wrong number of fields
			log.waring("... line %d has wrong format, skipping" % (file.name, i+1))
			continue
	
	file.close()

verbose_level = 0

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
				return ecn
	
	if checkafm:
		log.debug('... checking AFM file')
		filename = findfile.locate(fontname + '.afm')
		if filename:
			log.debug("... ... using '%s'" % filename)
			file = open(filename, 'r')
			try:
				encodingname, _ = read_AFM(file)
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
def make_cache_file(fontname):
	
	# locate SVG
	filename = findfile.findfile(fontname + '.svg', setup.svg_font_path, ignorecase=True)
	if filename:
		log.debug("Using SVG font '%s' as '%s'" % (filename, fontname))
	else:
		raise FontError("Can't find SVG font for '%s'" % fontname)
	
	# get designsize & encoding
	designsize = get_designsize(fontname)
	log.debug("Font '%s' designed at %spt" % (fontname, str(designsize)))
	newfile, encoding = get_encoding(fontname)
	if encoding == False:
		raise FontError("Can't determine encoding for font '%s'" % fontname)
	else:
		log.debug("Font '%s' encoding is %s" % (fontname, encoding))
	
	if newfile:
		log.debug("Adding information about new font to '%s': %s@%fpt, enc. %s" % (
			setup.font_lookup,
			fontname,
			designsize,
			encoding)
		)
		file = open(setup.font_lookup, 'a')
		file.write("%s\t\t%s\t\t%s\n" % (fontname, encoding, str(designsize)))
		file.close()
	

	# 2. Process SVG file
	
	# a. load file
	from xml.dom.minidom import parse
	data = parse(filename)

	# b. get font element
	font = data.getElementsByTagName('font')
	if len(font) < 1:
		raise FontError("There should be at least one <font> element in SVG file")
	
	if len(font) > 1:
		# XXX: FontForge do not output more then 1
		log.debug("There are more then one font definition in the file, using only first")
	font = font[0]
	
	# c. get default horizontal advance if any
	if font.hasAttribute('horiz-adv-x'): 
		default_hadvx = float(font.getAttribute('horiz-adv-x'))
	else:
		default_hadvx = None

	# d. load fonts
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
			else: # more paths
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

		#for dvicode in encoding[name]:
		#	glyphs[dvicode] = (dvicode, unicode, name, hadvx, path)
	
		if name in glyphs:
			raise ValueError("???")
		glyphs[name] = (unicode, hadvx, path)

	# e. write the cache file
	font_info  = (fontname, designsize)
	font = (encoding, font_info, glyphs)
	cPickle.dump(font, open(setup.cache_path + fontname + '.cache', 'wb'), protocol=cPickle.HIGHEST_PROTOCOL)

font_cache = {}

def get_font(fontname, recache):
	try:
		font = font_cache[fontname]
		log.debug("Getting font '%s' from cache" % fontname)
	except KeyError:
		filename = os.path.join(setup.cache_path + fontname.lower() + '.cache')
		if recache:
			log.debug("Forced to recreate cache file for '%s' font" % fontname)
			make_cache_file(fontname)
			font_cache[fontname] = font = cPickle.load(open(filename, 'rb'))
		elif not os.path.exists(filename):
			log.debug("Cache file for '%s' font does not exists -- creating it" % fontname)
			make_cache_file(fontname)
			font_cache[fontname] = font = cPickle.load(open(filename, 'rb'))
		else:
			log.debug("Loading font '%s' from cache file" % fontname)
			font_cache[fontname] = font = cPickle.load(open(filename, 'rb'))
	
	return font

def is_font_supported(fontname):
	return findfile.findfile(fontname + ".svg", setup.svg_font_path, ignorecase=True) != None
	
def unavailable_fonts(fontslist):
	return [fontname for fontname in fontslist if not is_font_supported(fontname)]

init()

# vim: ts=4 sw=4

import os
import xml.dom.minidom
import cPickle

from sets     import Set
from encoding import read_ENC, ENCFileError
from findfile import find_all

encfiles = find_all(['enc', '/usr/share/texmf/', '/usr/share/texmf-tetex/'], 'enc')

encodings = {}
for fullpath in encfiles:
	if os.path.isdir(fullpath):
		continue
	
	print "* %s" % fullpath

	path, filename = os.path.split(fullpath)
	encname = filename[:-4]

	if encname not in encodings:
		try:
			encodings[encname] = Set(read_ENC(open(fullpath, 'r'))[1])
		except ENCFileError:
			pass

def findbest(svgenc):
	result  = []
	mindiff = 2**32
	for encname, enc in encodings.iteritems():
		d = len(svgenc.difference(enc))
		result.append( (d, encname) )
		if d < mindiff:
			mindiff = d
	
	return filter(lambda x: x[0]==mindiff, result)

f = open('xxx', 'w')
svgfiles = find_all('fonts', 'svg')
svglist  = {}
for fullpath in svgfiles:
	print "- %s" % fullpath
	svg    = xml.dom.minidom.parse(fullpath)
	glyphs = svg.getElementsByTagName('glyph')
	svgenc = Set(element.getAttribute('glyph-name') for element in glyphs)
	svglist[fullpath] = svgenc
	
	s = "%s\t: %s\n" % (fullpath, str(findbest(svgenc)))
	print s,
	f.write(s)

f.close()

# vim: ts=4 sw=4

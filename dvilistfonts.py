import dviparser

if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1:
		f = dviparser.binfile(sys.argv[1])
		(comment, (num, den, mag, u, l), pages, fonts) = dviparser.dviinfo(f)
		for c,s,d,fnt in fonts.itervalues():
			print fnt
		f.close()

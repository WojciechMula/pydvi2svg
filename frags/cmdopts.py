import optparse
import utils

def parse_enc_methods(option, opt_str, value, parser):
	if len(parser.rargs) == 0:
		raise optparse.OptionValueError("--enc - argument required")
	parser.values.enc_repl = utils.parse_enc_methods(parser.rargs.pop(0))


def parse_args(args=None):
	parser = optparse.OptionParser()

	# DVI engine options
	parser.add_option(
		"--enc",
		help	= "Methods use to resolve font encoding; \
		           comma-separated list of keywords: \
				   cache, tfm, afm, map, guess.  Default: \
				   cache,tfm,afm.",
		dest	= "enc_repl",
		action	= "callback",
		callback= parse_enc_methods,
		default	= {},
	)

	parser.add_option("--pages",
	                  dest="pages")
	
	parser.add_option("--enc-methods",
	                  dest="enc_methods",
					  default="c,t,a")

	parser.add_option("--no-fontforge",
					  action="store_false",
	                  dest="use_fontforge",
					  default=True)
	
	parser.add_option("--no-fnt2meta",
					  action="store_false",
	                  dest="use_fnt2meta",
					  default=True)
	
	# SVGfrags options
	parser.add_option(
		"--no-strip",
		help	= "Do not strip leading & trailing spaces from strings",
		dest	= "frags_strip",
		action	= "store_false",
		default	= True,
	)

	parser.add_option(
		"--keep-tex",
		help	= "Do not remove temporary TeX files (useful for debugging)",
		dest	= "frags_keeptex",
		action	= "store_true",
		default	= False,
	)

	parser.add_option(
		"--no-keep-dvi",
		help	= "Do not remove temporary DVI files.  By default they are keep, and can be re-use",
		dest	= "frags_keepdvi",
		action	= "store_false",
		default	= False,
	)

	parser.add_option(
		"--remove-text-obj",
		help	= "Remove from SVG replaced <text> nodes",
		dest	= "frags_removetext",
		action	= "store_true",
		default	= False,
	)

	parser.add_option(
		"--no-hide-text-obj",
		help	= "Do not hide replaced <text> nodes.",
		dest	= "frags_hidetext",
		action	= "store_false",
		default	= True,
	)

	parser.add_option(
		"-f", "--force-overwrite",
		help	= "Overwrite existing file",
		dest	= "frags_overwrite_file",
		action	= "store_true",
		default	= False,
	)

	parser.add_option(
		"-i", "--input",
		help	= "Name of input SVG file",
		dest	= "input_svg",
		default	= ""
	)

	parser.add_option(
		"-o", "--output",
		help	= "Name of output SVG file",
		dest	= "output_svg",
		default	= ""
	)

	parser.add_option(
		"-r", "--rules",
		help	= "Name of text file that contains replacement rules",
		dest	= "input_txt",
		default	= ""
	)

	if args is not None:
		return parser.parse_args(args)
	else:
		return parser.parse_args()

#	parser.add_option("--verbose",
#					  action="store_true",
#	                  dest="verbose",
#					  default=False)
	
# vim: ts=4 sw=4 nowrap

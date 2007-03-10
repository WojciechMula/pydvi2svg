# changelog
"""
10.03.2007
	+ margins property
 9.03.2007
	- class approach:
	  + Tokenizer (base class)
	  + FragsTokenizer (specialized class)
	  + parser
 8.03.2007
	- first version
"""

"""
"string"|#id|rect(x,y,w,h)|point(x,y) -> "TeX"
	position: x|center/c|left/l|right/r, y|center/c|top/t|bottom/b|
	scale: number
	settowidth: number|rectid|this
	settoheight: number|rectid|this
	fit
	margin: number,[number,[number,number]]
"""

import re

re_spaces = re.compile(r'(\s*)')
re_quoted_string = re.compile(r'\s*"((?:\\"|[^"])*)"')
re_number = re.compile(r'\s*([+-]?\d*\.\d+|[+-]?\d+\.\d*|[-+]?\d+)')
re_comma  = re.compile(r'\s*,\s*')

re_id		= re.compile(r'\s*(#[a-zA-Z0-9._:-]+)')
re_fit		= re.compile(r'\s*fit(\s+|$)')
re_arrow	= re.compile(r'\s*(?:->|=>|=)')
re_comment = re.compile('\s*%.*\n')
re_openingbrace = re.compile(r'\s*\(')
re_closingbrace = re.compile(r'\s*\)')

class SyntaxError(ValueError):
	pass

class Tokenizer(object):
	def __init__(self, string):
		self.str  = string
		self.last = ""
		self.last_count = 30
		self._re_cache = {}
	
	def __nonzero__(self):
		return len(self.str) > 0
	
	def consume(self, regexp, err_msg=""):
		match = regexp.match(self.str)
		if not match:
			if err_msg:
#				err_msg = "\n%s...\n%s" % (self.str[:20], str(err_msg))
				self.error(err_msg)
			else:
				return None

		self.last = (self.last + self.str[:match.end()])[-self.last_count:]
		self.str  = self.str[match.end():]
		try:
			return match.groups()[0]
		except IndexError:
			return True
	
	def literal(self, string, err_msg=""):
		try:
			regexp = self._re_cache[string]
		except KeyError:
			regexp = re.compile('('+string+')', re.IGNORECASE)
			self._re_cache[string] = regexp

		return self.consume(regexp, err_msg)
	
	def error(self, err_msg=""):
		# XXX: I don't like it
		s1 = self.last.replace('\n', r'\n').replace('\t', ' ')
		s2 = self.str[:self.last_count].replace('\n', r'\n').replace('\t', ' ')
		s3 = " " * len(s1)
		s4 = "^" * min(len(s2), self.last_count/2)

		if err_msg:
			err_msg = "Syntax error: " + err_msg
		else:
			err_msg = "Syntax error"

		err_msg = ''.join(["\n", s1, s2, "\n", s3, s4, "\n", err_msg])
		raise SyntaxError(err_msg)


class FragsTokenizer(Tokenizer):
	def eatspaces(self):
		return len(self.consume(re_spaces))
	
	def eatcomment(self):
		return self.consume(re_comment)
	
	def number(self, err_msg=""):
		v = self.consume(re_number, err_msg)
		try:
			return float(v)
		except ValueError:
			self.error("Invalid number '%s'" % s)
	
	def string(self, err_msg=""):
		return self.consume(re_quoted_string, err_msg)
	
	def id(self, err_msg=""):
		return self.consume(re_id, err_msg)
	
	def comma(self, err_msg=""):
		return self.consume(re_comma, err_msg)
	
	def literal(self, string):
		self.eatspaces()
		return super(FragsTokenizer, self).literal(string)
	
	def keyword(self, keyword):
		if self.literal(keyword + "\s*:\s*"):
			return True
		else:
			return None


def parse(string):

	tokens = FragsTokenizer(string)

	def get_target():
		target = tokens.string()
		if target: return ('string', target)
		
		target = tokens.id()
		if target: return ('id', target)

		if tokens.literal('rect'):
			tokens.consume(re_openingbrace, "opening brace needed")
			x = tokens.number("number 'x'"); tokens.comma("coma expeced")
			y = tokens.number("number 'y'"); tokens.comma("coma expeced")
			w = tokens.number("number 'widht'" ); tokens.comma("coma expeced")
			h = tokens.number("number 'height'")
			tokens.consume(re_closingbrace, "closing brace needed")
			return ('rect', (x, y, w, h))
		
		if tokens.literal('point'):
			tokens.consume(re_openingbrace, "opening brace needed")
			x = tokens.number("number 'x'"); tokens.comma("coma expeced")
			y = tokens.number("number 'y'");
			tokens.consume(re_closingbrace, "closing brace needed")
			return ('point', (x, y))
		tokens.error("literal string, id, rect definition or point location required")


	def get_px():
		px = tokens.number()
		if not px:
			px = tokens.literal('left')   or tokens.literal('l') or \
				 tokens.literal('right')  or tokens.literal('r') or \
				 tokens.literal('center') or tokens.literal('c')
			if px is None:
				tokens.error("Number or string 'left', 'right' or 'center' required")
			return {'left':0.0, 'l':0.0, 'right':1.0, 'r':1.0, 'center':0.5, 'c':0.5}[px]
		else:
			return px
	
	def get_py():
		py = tokens.number()
		if not py:
			py = tokens.literal('top')    or tokens.literal('t') or \
				 tokens.literal('bottom') or tokens.literal('b') or \
				 tokens.literal('center') or tokens.literal('c')
			if py is None:
				tokens.error("Number or string 'top', 'bottom' or 'center' required")
			return {'top':0.0, 't':0.0, 'bottom':1.0, 'b':1.0, 'center':0.5, 'c':0.5}[py]
		else:
			return py
	
	def get_settoxxx():
		v = tokens.consume(re_number)
		if v is None:
			v = tokens.id()
			if v: return v

			v = tokens.literal('this')
			if v: return 'this'
		else:
			return v

		token.error("Number, object id or string 'this' required")
	
	def get_margins():
		if tokens.keyword('margin'):
			l = r = t = b = tokens.number()
			if tokens.comma():
				t = b = tokens.number('top/bottom margin required')
			else:
				return (l, r, t, b)

			if tokens.comma():
				r = t
				t = tokens.number('top margin required');  tokens.comma('comma expeced')
				b = tokens.number('bottom margin required')

			return (l, r, t, b)
		else:
			return (0.0, 0.0, 0.0, 0.0)


	while tokens:
		tokens.eatspaces()
		if tokens.eatcomment(): continue
		
		if not tokens:
			break

		# string/id/rect/point	
		target = get_target()

		# =>
		tokens.consume(re_arrow, "=, -> or => required")

		# replacement -- (La)TeX expression
		tex = tokens.string("Expeced quoted TeX expression")
		
		# margin: m
		# margin: mx,my
		# margin: ml,mr,mt,mb
		margins = get_margins()

		# position: px, py
		px = 0.5
		py = 0.5
		if tokens.keyword('position'):
			px = get_px()
			if tokens.comma():
				py = get_py()
	
		# scale: number
		if tokens.keyword('scale'):
			scale = tokens.number("scale factor needed")
		else:
			scale = 1.0


		# settowidth: number|id|this
		if tokens.keyword('settowidth') or tokens.keyword('scaletowidth'):
			settowidth = get_settoxxx()
			scale = 1.0
		else:
			settowidth = None
		
		# settoheight: number|id|this
		if tokens.keyword('settoheight') or tokens.keyword('scaletoheight'):
			settoheight = get_settoxxx()
			scale = 1.0
		else:
			settoheight = None
	

		# fit
		if tokens.consume(re_fit):
			settowidth = settoheight = None
			scale = 1.0
			fit = True
		else:
			fit = False
		
		# final touches: if we refer to point or text, these
		# objects doesn't have width/heigt, so settowidth,
		# settoheight & fit are disabled
		if target[0] in ['string', 'point']:
			settowidth = settoheight = None
			fit = False

		#print (target, tex, px, py, scale, settowidth, settoheight, fit)
		yield (target, tex, px, py, margins, scale, settowidth, settoheight, fit)


if __name__ == '__main__':
	sample = """
	point(10, -.5) = "This is sample text" position:0.2,bottom
	"LaTeX" -> "\\LaTeX" % position: left, 0.57 settoheight: this
	  %  "emc2"  -> "$e = mc^2$" settowidth :  #rect02-a
	  rect  (   10, 5.5, 100, 200.5  ) -> "$\\fract{1}{x^2 + 1}$" position: right, 0.2 fit
	"""
	for item in parse(sample):
		print item	

# vim: ts=4 sw=4 nowrap

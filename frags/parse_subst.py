"""
"string"|#id|rect(x,y,w,h) -> "TeX"
	position: x|center/c|left/l|right/r, y|center/c|top/t|bottom/b|
	settowidth: number|rectid|this
	settoheight: number|rectid|this
	fit
"""

import re

re_quoted_string = re.compile(r'\s*"((?:\\"|[^"])*)"')
re_id     = re.compile(r'\s*(#[a-zA-Z0-9_-]+)')
re_number = re.compile(r'\s*([+-]?\d*\.\d+|[+-]?\d+\.\d*|[-+]?\d+)')
re_rect   = re.compile(r'\s*rect\s*\(', re.IGNORECASE)
re_closingbrace  = re.compile(r'\s*\)')
re_comma  = re.compile(r'\s*,\s*')
re_colon  = re.compile(r'\s*:\s*')
re_spaces = re.compile(r'\s*')
re_arrow  = re.compile(r'->|=>|=')


def tokenize(string):
	class Dummy: pass
	s   = Dummy()
	s.s = string

	def consume(regexp, match_needed=""):
		m = regexp.match(s.s)
		if not m:
			if match_needed:
				raise ValueError(str(match_needed))
			else:
				return None

		s.s = s.s[m.end():]
		if m.groups():
			return m.groups()[0]
		else:
			return True
	
	def consume_string(string, match_needed=False):
		regexp = re.compile('('+string+')', re.IGNORECASE)
		consume(re_spaces)
		return consume(regexp, match_needed)
	
	def notNone(value, info="None not accpeted!"):
		if value is None:
			raise ValueError(info)
		else:
			return value

	while s.s:
		consume(re_spaces)
		if not s.s:
			break

		A = consume(re_quoted_string) or consume(re_id)
		if A is None:
			consume(re_rect, "rect expeced")

			x = consume(re_number, "number 'x'"); consume(re_comma, "comma expeced")
			y = consume(re_number, "number 'y'"); consume(re_comma, "comma expeced")
			w = consume(re_number, "number 'width'"); consume(re_comma, "comma expeced")
			h = consume(re_number, "number 'height'")
			A = (x, y, w, h)

			consume(re_closingbrace, "you forgot to close brace")

		consume(re_spaces)
		consume(re_arrow, True)
		tex = consume(re_quoted_string, True)

		position = consume_string('position')
		px = 0.5
		py = 0.5
		if position:
			if consume(re_colon, True):
				px = consume_string('left')   or \
				     consume_string('right')  or \
				     consume_string('center') or \
				     consume(re_number)
				notNone(px)
				try:
					px = {'left': 0.0, 'center': 0.5, 'right': 1.0}[px.lower()]
				except KeyError, AttributeError:
					pass

			if consume(re_comma):
				py = consume_string('top')    or \
				     consume_string('bottom') or \
				     consume_string('center') or \
				     consume(re_number)
				notNone(py)
				try:
					py = {'top': 0.0, 'center': 0.5, 'bottom': 1.0}[py.lower()]
				except KeyError, AttributeError:
					pass


		settowidth = consume_string('settowidth')
		fw = None
		if settowidth and consume(re_colon, True):
			fw = consume_string('this') or \
			     consume(re_id) or \
			     consume(re_number);
			notNone(fw, "Dupa")
		
		settoheight = consume_string('settoheight')
		fh = None
		if settoheight and consume(re_colon, True):
			fh = consume_string('this') or \
			     consume(re_id) or \
			     consume(re_number);
			notNone(fh, "Dupa")
	
		fit = consume_string('fit')
			
				
		print A, tex, px, py, fw, fh, fit



sample = """
"LaTeX" -> "\\LaTeX" position: left, 0.57 settoheight: this
"emc2"  -> "$e = mc^2$" settowidth :  #rect02-a
  rect  (   10, 5.5, 100, 200.5  ) -> "$\\fract{1}{x^2 + 1}" position: right, 0.2 fit
"""
tokenize(sample)

"""
for kind, value in tokenize(sample):
	print "%s: %s" % (kind, value)
"""

import re
RegularExpressionType = type(re.compile(' '))

def preprocess(*expr):
	"""
	Gets expression or pair (callback, expression) and
	depending of expression type return proper rule instance.
	"""
	if len(expr) == 2:
		if callable(expr[0]):
			callback, expr = expr
		else:
			raise ValueError("First argument must be callable")
	elif len(expr) == 1:
		expr = expr[0]
		callback = None
	else:
		raise ValueError("Too many arguments; 1 or 2 allowed")


	# string: if string is enclosed in () is returned
	# otherwise is eaten
	if type(expr) is str:
		if len(expr) > 2 and expr[0] == '(' and expr[-1] == ')':
			if len(expr) > 3:
				return string(expr[1:-1], callback)
			else:
				return char(expr[1:-1], callback)
		else:
			if len(expr) == 1:
				return eat(char(expr, callback))
			else:
				return eat(string(expr, callback))

	# regexp
	elif type(expr) is RegularExpressionType:
		return regexp(expr, callback)
	
	# rule instance
	elif isinstance(expr, rule):
		if callback is not None:  # set callback if wasn't set
			expr.callback = callback
		return expr
	
	else:
		raise ValueError("Don't know how to deal with %s (%s)" % (str(expr), type(expr)))

token = preprocess

class rule(object):
	"Base class for parser"
	def __init__(self, expr, callback=None):
		assert callback is None or callable(callback), "Callback have to be callable or None"
		self.expr     = expr
		self.callback = callback
		
	def match(self, string):
		try:
			length, matched = self.get(string)
			if self.callback is not None:
				matched = self.callback(string, length, matched)

			return (length, matched)
		except TypeError:
			return None
	
	def get(self, string):
		raise RuntimeError("Abstract method called")


class char(rule):
	"Matches single char"
	def get(self, string):
		try:
			if self.expr == string[0]:
				return (1, [self.expr])
		except IndexError:
			pass # empty string
			

class string(rule):
	"Matches string"
	def get(self, str):
		if str.startswith(self.expr):
			return (len(self.expr), [self.expr])


class regexp(rule):
	"Matches regular expression"
	def get(self, string):
		match = self.expr.match(string)
		if match:
			if len(match.groups()) == 1:
				return (match.end(), [match.groups()[0]])
			elif len(match.groups()) > 1:
				return (match.end(), [match.groups()])
			else:
				return (match.end(), [])


class eat(rule):
	"Matches anything, but returns no data"
	def get(self, string):
		try:
			length, matched = self.expr.match(string)
			return (length, [])
		except TypeError:
			pass # no match


class seq(rule):
	"""
	Matches ALL expressions from the list.
	Optional ws rule is consumed before processing
	every expression list.
	"""

	def __init__(self, *expr):
		if len(expr) > 1 and callable(expr[0]):
			self.callback = expr[0]
			expr = expr[1:]
		else:
			self.callback = None
		
		self.expr = [preprocess(e) for e in expr]
	
	ws = []

	def eat_ws(self, string):
		if seq.ws:
			try:
				length, matched = seq.ws.match(string)
				if length > 0:
					return (length, string[length:])
			except TypeError:
				pass

		return (0, string)
	
	def get(self, string):
		length  = 0
		matched = []
		for expr in self.expr:
			try:
				l, string = self.eat_ws(string)
				length = length + l

				l, m   = expr.match(string)
				length = length + l
				string = string[l:]
				matched.extend(m)
			except TypeError:
				return None # not all expression matches

		return (length, matched)


class glued(seq):
	"Like seq, but ws is not processed, even if present"	
	def eat_ws(self, string):
		return (0, string)


class optional(rule):
	"Matches 0 or 1 times"
	def __init__(self, *expr):
		self.callback = None
		if len(expr) > 1:
			self.expr = seq(*expr)
		else:
			self.expr = preprocess(*expr)

	def get(self, string):
		try:
			length, matched = self.expr.match(string)
			return (length, matched)
		except TypeError:
			return (0, []) # no match

class alt(seq):
	"Matches FIRST expressions from the list"
	def get(self, string):
		for expr in self.expr:
			try:
				length, matched = expr.match(string)
				return (length, matched)
			except TypeError:
				pass

class infty(seq):
	"While any of expression from the list matches, consume input"
	def get(self, string):
		matches = []
		length  = 0
		while True:
			for expr in self.expr:
				try:
					l, m = expr.match(string)
					length += l
					string  = string[l:]
					matches.extend(m)
					break
				except TypeError:
					pass
			else:
				# no matches
				break

		if length:
			return (length, matches)
		else:
			return None


########################################################################

space 	= re.compile(r'\s+')
comment	= re.compile('\s*%.*\n')

seq.ws = infty(space, comment)

def number_cb(l, s, r):
	return [float(r[0])]
number = token(number_cb, re.compile(r'([+-]?\d*\.\d+|[+-]?\d+\.\d*|[-+]?\d+)'))


def numorperc_cb(l, s, r):
	if len(r) == 2:
		# perc
		return [('%', r[0])]
	else:
		return r
numorperc = glued(numorperc_cb, number, optional("(%)"))

def quoted_string_cb(l, s, r):
	return [r[0].replace('\\"', '"')]
quoted_string = token(quoted_string_cb, re.compile(r'"((?:\\"|[^"])*)"'))

def xml_id_cb(l, s, r):
	return [('id', r[0])]
xml_id = token(xml_id_cb, re.compile(r'#([a-zA-Z0-9._:-]+)'))

def rect_cb(l, s, r):
	return [tuple(r)]
rect = seq(rect_cb, "rect", "(", number, ",", number, ",", number, ",", number, ")")

def point_cb(l, s, r):
	return [tuple(r)]
point = seq("point", "(", number, ",", number, ")")


def margins_cb(l, s, r):
	if len(r) == 1:
		m = r[0]
		return [(m, m, m, m)]
	elif len(r) == 2:
		mx, my = r
		return [(mx, mx, my, my)]
	else: # 4 elements
		return [tuple(r)]

margins = seq(margins_cb,
	"margins", ":", numorperc,
	 optional(",", numorperc, optional(",", numorperc, ",", numorperc))
)

# number|perc|width(id)|height(id)
def wh_cb(l, s, r):
	wh, (_, id) = r
	return [(wh, id)]
scaledim = alt(numorperc, number, seq(wh_cb, alt("(width)", "(height)"), "(", xml_id, ")"))

# scale: fit | (scaledim [, scaledim])
def scale_cb(l, s, r):
	if len(r) == 1: # fit/one scaledim
		return [('scale', r[0])]
	else: # two scaledim
		return [('scale', r[0], r[1])]
scale = seq(scale_cb,
	"scale", ":", alt("(fit)", seq(scaledim, optional(",", scaledim)))
)

def setdim_cb(l, s, r):
	return [tuple(r)]
setdim  = alt(number, xml_id, "(this)")
setwidth  = seq(setdim_cb, "(setwidth)", ":", setdim)
setheight = seq(setdim_cb, "(setheight)", ":", setdim)

def position_cb(l, s, r):
	PX = {'center':0.5, 'c':0.5, 'left':0.0, 'l':0.0, 'right':1.0,  'r':1.0}
	PY = {'center':0.5, 'c':0.5, 'top':0.0,  't':0.0, 'bottom':1.0, 'b':1.0}
	if len(r) == 1: # single argument
		py = 0.5
		px = r[0]
		if type(px) is str:
			px = PX[px]
		elif type(px) is tuple: # ('%', float)
			px = px[1] * 0.01

		return [('position', px, py)]
	else: # two args
		px = r[0]
		if type(px) is str:
			px = PX[px]
		elif type(px) is tuple: # ('%', float)
			px = px[1] * 0.01
		
		py = r[1]
		if type(py) is str:
			py = PY[py]
		elif type(py) is tuple: # ('%', float)
			py = py[1] * 0.01

		return [('position', px, py)]
		

position = seq(position_cb, 
	"position", ":",
	
	alt(numorperc, number, "(center)", "(c)", "(left)", "(l)", "(right)", "(r)"),
	optional(
		",", alt(numorperc, number, "(center)", "(c)", "(top)", "(t)", "(bottom)", "(b)")
	)
)

subst = seq(
	alt(quoted_string, xml_id, rect, point),
	eat(token(re.compile(r'(?:->|=>|=)'))),
	quoted_string,
	
	optional(position),
	optional(margins),
	optional(
		alt(
			scale,
			seq(optional(setwidth), optional(setheight)),
		)
	)
)

#print scale.match("  scale   :     150% ,       width(    #aaa )   ")
#print rect.match("rect(10,50,10,20)")
#print point.match("point(10,50)")
#print margins.match("   margins   : 10.0, 20,  40,  50")
#print margins.match("   margins   : 10.0")
#print margins.match("   margins   : 10.0, 20.0")
print position.match("    position  :   -.5,    bottom  ")
print subst.match("""
% sample comment
	rect(10, 20, 30, 50) -> % and another
	"text"
	position: 60%, bottom
	setwidth: this
	setheight: #aabb
""")

# vim: ts=4 sw=4 nowrap

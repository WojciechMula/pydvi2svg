import re

CONSUME	= True
regexp	= type(re.compile(' '))

def consume(expr):
	return token(expr, consume=True)

class token(object):
	
	every_token = None

	def __init__(self, expr, consume=False, fireeverytoken=True):
		if type(expr) is str:
			# (word) -> return word
			if not expr:
				raise ValueError("Empty token!")
			if len(expr) > 2 and expr[0] == '(' and expr[-1] == ')':
				self.expr    = expr[1:-1]
				self.consume = False
			else:
				self.expr    = expr
				self.consume = True

		elif type(expr) is regexp:
			self.expr    = expr
			self.consume = bool(consume)

		else:
			self.expr    = expr
			self.consume = bool(consume)
	
		self.fireeverytoken = bool(fireeverytoken)


	def match(self, s):
		L = 0
		if self.fireeverytoken and token.every_token is not None:
			while True:
				for e in token.every_token:
					m = e.match(s)
					if m:
						L = L + m.end()
						s = s[m.end():]
						break
				else:
					break

		
		m = None
		if isinstance(self.expr, token):
			m = self.expr.match(s)
		elif type(self.expr) is str:
			if s.startswith(self.expr):
				m = (len(self.expr), [self.expr])
		else: # regexp
			m = self.expr.match(s)
			if m:
				try:
					m = (m.end(), [m.groups()[0]])
				except IndexError:
					m = (m.end(), [])

		if m is not None:
			if self.consume:
				return (L+m[0], [])
			else:
				return (L+m[0], m[1])
	
class rule(object):
	pass

class optional(rule):
	# match 0 or 1
	def __init__(self, *expr):
		if len(expr) == 1:
			self.expr = token(expr[0])
		else:
			self.expr = seq(*expr)
	
	def match(self, s):
		m = self.expr.match(s)
		if m:
			return m
		else:
			return (0, "")

class seq(token):
	def __init__(self, *exprlist):
		self.expr = []
		for expr in exprlist:
			if type(expr) in [str, regexp]:
				expr = token(expr)
			self.expr.append(expr)
		
	def match(self, s):
		r = []
		t = 0
		for subexpr in self.expr:
			try:
				l, ss = subexpr.match(s)
				s = s[l:]
				r.extend(ss)
				t += l
			except TypeError:
				return None

		return (t, r)

class alt(seq):
	def match(self, s):
		for subexpr in self.expr:
			m = subexpr.match(s)
			if m: return m

class repeat(token):
	def __init__(self, count, expr):
		super(repeat, self).__init__(expr)
		self.count = max(0, count)
	
	def match(self, s):
		r = []
		t = 0
		if self.count == 0:
			while True:
				m = self.expr.match(s)
				if m:
					l, ss = m
					s = s[l:]
					r.extend(ss)
					t += l
				else:
					return (t, r)
		else:
			for i in xrange(self.count):
				m = self.expr.match(s)
				if m:
					l, ss = m
					s = s[l:]
					r.extend(ss)
					t += l
				else:
					return None
			return (t, r)


quoted_string	= re.compile(r'"((?:\\"|[^"])*)"')
arrows			= re.compile(r'(?:->|=>|=)')
space 			= re.compile(r'\s+')
number			= re.compile(r'([+-]?\d*\.\d+|[+-]?\d+\.\d*|[-+]?\d+)')
xml_id			= re.compile(r'(#[a-zA-Z0-9._:-]+)')
comment			= re.compile('\s*%.*\n')

numorperc	= seq(number, optional("(%)"))

rect = seq("rect", "(", number, ",", number, ",", number, ",", number, ")")
point = seq("point", "(", number, ",", number, ")")
margins = seq(
	"margins", ":", numorperc,
	 optional(",", numorperc, optional(",", numorperc, ",", numorperc))
)

# number|perc|width(id)|height(id)
scaledim = alt(numorperc, number, seq(alt("width", "height"), "(", xml_id, ")"))

# scale: fit | (scaledim [, scaledim])
scale = seq("scale", ":", alt("(fit)", seq(scaledim, optional(",", scaledim))))

setdim  = alt(number, xml_id, "(this)")
setwidth  = seq("setwidth", ":", setdim)
setheight = seq("setheight", ":", setdim)

position = seq(
	"position", ":",
	
	alt(numorperc, number, "(center)", "(c)", "(left)", "(l)", "(right)", "(r)"),
	optional(
		",", alt(numorperc, number, "(center)", "(c)", "(top)", "(t)", "(bottom)", "(b)")
	)
)

subst = seq(
	alt(quoted_string, xml_id, rect, point),
	consume(arrows),
	quoted_string,
	
	optional(position),
	optional(margins),
	optional(
		alt(
			scale,
			optional(setwidth),
			optional(setheight),
		)
	)
)

token.every_token = [space, comment]

#print scale.match("   scale: fit ")
#print rect.match("   rect  (  10, 50,  10, 20 ) ")
#print point.match("   point  (  10, 50 ) ")
#print margins.match(  " margins: 10, 20, 40, 50  ")
#print position.match("  position :  -.5, 100%  ")
print subst.match('  rect(10, 20, 30, 50) -> "text" scale: 10, width ( #a51 ) ')

# vim: ts=4 sw=4

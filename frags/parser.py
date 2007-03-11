import re

CONSUME = True

class token(object):
	def __init__(self, expr, eat=False):
		self.expr = expr
		self.eat  = bool(eat)
	
	def match(self, s):
		L = 0
		m = space.match(s)
		if m: L += m.end()
		
		m = comment.match(s)
		if m: L += m.end()

		if L:
			s = s[L:]

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
			if self.eat:
				return (L+m[0], [])
			else:
				return (L+m[0], m[1])


class required(token):
	def __init__(self, expr, eat=False):
		super(required, self).__init__(expr, eat)
		if type(expr) is str:
			self.expr = token(expr)
		else:
			self.expr = expr

literal = required
	
class optional(required):
	
	def match(self, s):
		m = super(optional, self).match(s)
		if m:
			return m
		else:
			return (0, "")

regexp = type(re.compile(' '))
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
				l, ss = m = subexpr.match(s)
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

numorperc	= seq(required(number), optional("%"))

rect		= seq(
				required("rect"),
				required("(", CONSUME),
				required(number),
				required(",", CONSUME),
				required(number),
				required(",", CONSUME),
				required(number),
				required(",", CONSUME),
				required(number),
				required(")", CONSUME),
			)

point		= seq(
				required("point"),
				required("(", CONSUME),
				required(number),
				required(",", CONSUME),
				required(number),
				required(")", CONSUME),
			)

margins		= seq(
				required("margins", CONSUME),
				required(":", CONSUME),

				required(numorperc),
				optional(seq(
					required(",", CONSUME),
					required(numorperc),
					optional(seq(
						required(",", CONSUME),
						required(numorperc),
						required(",", CONSUME),
						required(numorperc),
					))
				))
			)

# number|perc|width(id)|height(id)
scaledim	= alt(
		required(numorperc),
		required(number),
		seq(
			alt(literal("width"), literal("height")),
			literal("(", CONSUME),
			required(xml_id),
			literal(")", CONSUME)
		),
	)

setdim = alt(
		required(number),
		required(xml_id),
		literal("this"),
	)

# scale: number[%]
scale		= seq(
		required("scale", CONSUME),
		required(":", CONSUME),
		alt(
			literal("fit"),
			seq(
				required(scaledim),
				optional(seq(
					required(",", CONSUME),
					required(scaledim)
				))
			)
		)
	)

position = seq(
	optional(space),
	required("position", CONSUME),
	optional(space),
	required(":", CONSUME),
	optional(space),

	required(
		alt( 
			seq(required(number), optional("%")),
			literal("center"), literal("c"),
			literal("left"),   literal("l"),
			literal("right"),  literal("r"),
		)
	),

	optional(seq(
		required(",", CONSUME),
		alt( 
			seq(required(number), optional("%")),
			literal("center"), literal("c"),
			literal("top"),    literal("t"),
			literal("bottom"), literal("b"),
		)
	))
)

subst = required(seq(
	alt(quoted_string, xml_id, rect, point),
	required(arrows, CONSUME),
	required(quoted_string),
))

#print scale.match("   scale:  123% ")
#print rect.match("   rect  (  10, 50,  10, 20 ) ")
#print point.match("   point  (  10, 50 ) ")
#print margins.match(  " margins: 10, 20, 40, 50  ")
#print position.match("  position :  -.5, 100%  ")
#print subst.match('  rect(10, 20, 30, 50) -> "text" ')

a = seq(required(",", CONSUME), required(number))

s = "     scale  :   width(#ccc)     ,              width(#aaa)"
print scale.match(s)

# vim: ts=4 sw=4

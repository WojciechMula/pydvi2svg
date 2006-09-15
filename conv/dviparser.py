from struct import unpack

class Reader:
	def __init__(self, data):
		self.data = data
		self.pos  = 0
	
	def uint8(self):
		x = unpack('B', self.data[self.pos])[0]
		self.pos += 1
		return x

	def uint16(self):
		x = unpack('>H', self.data[self.pos:self.pos+2])[0]
		self.pos += 2
		return x

	def uint24(self):
		x = unpack('>I', '\0' + self.data[self.pos:self.pos+3])[0]
		self.pos += 3
		return x

	def uint32(self):
		x = unpack('>L', self.data[self.pos:self.pos+4])[0]
		self.pos += 4
		return x

	def int8(self):
		x = unpack('b', self.data[self.pos])[0]
		self.pos += 1
		return x

	def int16(self):
		x = unpack('>h', self.data[self.pos:self.pos+2])[0]
		self.pos += 2
		return x

	def int24(self):
		x = unpack('>i', self.data[self.pos:self.pos+3] + '\0')[0] >> 8
		self.pos += 3
		return x

	def int32(self):
		x = unpack('>l', self.data[self.pos:self.pos+4])[0]
		self.pos += 4
		return x

	def string(self, len):
		s = self.data[self.pos:self.pos + len]
		self.pos += len
		return s
	
	def __nonzero__(self):
		return self.pos < len(self.data)
	
def parse(reader):
	stack = []

	h, v = 0, 0
	while reader:
		command = reader.uint8()
		if command <= 127: # set_char_i (0-127)
			yield ("set_char", command)
		elif command == 128: # set1
			yield ("set_char", reader.uint8())
		elif command == 129: # set2
			yield ("set_char", reader.uint16())
		elif command == 130: # set3
			yield ("set_char", reader.uint24())
		elif command == 131: # set4
			yield ("set_char", reader.uint16())

		elif command == 132: # set_rule
			a, b = reader.uint16(), reader.uint16()
			yield ("set_rule", (a,b))

		elif command == 133: # put1
			yield ("put", reader.uint8())
		elif command == 134: # put2
			yield ("put", reader.uint16())
		elif command == 135: # put3
			yield ("put", reader.uint24())
		elif command == 136: # put4
			yield ("put", reader.uint32())

		elif command == 136: # put_rule
			a, b = reader.uint32(), reader.uint32()
			yield ("put_rule", (a, b))
		elif command == 138: # nop
			yield ("nop", None)
		elif command == 139: # bop
			c0 = reader.uint32()
			c1 = reader.uint32()
			c2 = reader.uint32()
			c3 = reader.uint32()
			c4 = reader.uint32()
			c5 = reader.uint32()
			c6 = reader.uint32()
			c7 = reader.uint32()
			c8 = reader.uint32()
			c9 = reader.uint32()
			p  = reader.int32()
			yield ("bop", (c0,c1,c2,c3,c4,c5,c6,c7,c8,c9, p))
		elif command == 140: # eop
			yield ("eop", None)
		elif command == 141: # push
			yield ("push", None)
		elif command == 142: # pop
			yield ("pop", None)
		elif command == 143: # right1
			yield ("right", reader.int8())
		elif command == 144: # right2
			yield ("right", reader.int16())
		elif command == 145: # right3
			yield ("right", reader.int24())
		elif command == 146: # right4
			yield ("right", reader.int32())
		
		elif command == 147: # w0
			yield ("w0", None)
		elif command == 148: # w1
			yield ("w", reader.int8())
		elif command == 149: # w2
			yield ("w", reader.int16())
		elif command == 150: # w3
			yield ("w", reader.int24())
		elif command == 151: # w4
			yield ("w", reader.int32())

		elif command == 152: # x0
			yield ("x0", None)
		elif command == 153: # x1
			yield ("x", reader.int8())
		elif command == 154: # x2
			yield ("x", reader.int16())
		elif command == 155: # x3
			yield ("x", reader.int24())
		elif command == 156: # x4
			yield ("x", reader.int32())
		
		elif command == 157: # down1
			yield ("down", reader.int8())
		elif command == 158: # down2
			yield ("down", reader.int16())
		elif command == 159: # down3
			yield ("down", reader.int24())
		elif command == 160: # down4
			yield ("down", reader.int32())
		
		elif command == 161: # y0
			yield ("y0", None)
		elif command == 162: # y1
			yield ("y", reader.int8())
		elif command == 163: # y2
			yield ("y", reader.int16())
		elif command == 164: # y3
			yield ("y", reader.int24())
		elif command == 165: # y4
			yield ("y", reader.int32())

		elif command == 166: # z0
			yield ("z0", None)
		elif command == 167: # z1
			yield ("z", reader.int8())
		elif command == 168: # z2
			yield ("z", reader.int16())
		elif command == 169: # z3
			yield ("z", reader.int24())
		elif command == 170: # z4
			yield ("z", reader.int32())

		elif 234 >= command >= 171:
			yield ("fnt_num", command - 171)
		elif command == 235:
			yield ("fnt_num", reader.uint8())
		elif command == 236:
			yield ("fnt_num", reader.uint16())
		elif command == 237:
			yield ("fnt_num", reader.uint24())
		elif command == 238:
			yield ("fnt_num", reader.uint32())

		elif command == 239:
			k = reader.uint8()
			yield ("xxx", reader.string(k+2))
		elif command == 240:
			k = reader.uint16()
			yield ("xxx", reader.string(k+2))
		elif command == 241:
			k = reader.uint24()
			yield ("xxx", reader.string(k+2))
		elif command == 242:
			k = reader.uint32()
			yield ("xxx", reader.string(k+2))

		elif command == 243:
			k = reader.uint8()
			c = reader.uint32()
			s = reader.uint32()
			d = reader.uint32()
			a = reader.uint8()
			l = reader.uint8()
			dir = reader.string(a)
			fnt = reader.string(l)
			yield ("fnt_def", (k,c,s,d, dir, fnt))
		elif command == 244:
			k = reader.uint16()
			c = reader.uint32()
			s = reader.uint32()
			d = reader.uint32()
			a = reader.uint8()
			l = reader.uint8()
			dir = reader.string(a)
			fnt = reader.string(l)
			yield ("fnt_def", (k,c,s,d, dir, fnt))
		elif command == 245:
			k = reader.uint24()
			c = reader.uint32()
			s = reader.uint32()
			d = reader.uint32()
			a = reader.uint8()
			l = reader.uint8()
			dir = reader.string(a)
			fnt = reader.string(l)
			yield ("fnt_def", (k,c,s,d, dir, fnt))
		elif command == 246:
			k = reader.uint32()
			c = reader.uint32()
			s = reader.uint32()
			d = reader.uint32()
			a = reader.uint8()
			l = reader.uint8()
			dir = reader.string(a)
			fnt = reader.string(l)
			yield ("fnt_def", (k,c,s,d, dir, fnt))

		elif command == 247:
			i   = reader.uint8()
			num = reader.uint32()
			den = reader.uint32()
			mag = reader.uint32()
			k   = reader.uint8()
			x   = reader.string(k)
			yield ("pre", (i, num, den, mag, x))
		elif command == 248:
			i   = reader.uint8()
			num = reader.uint32()
			den = reader.uint32()
			mag = reader.uint32()
			l   = reader.uint32()
			u   = reader.uint32()
			s   = reader.uint16()
			t   = reader.uint16()
			yield ("post", (i, num, den, mag, x))
		elif command == 249:
			q = reader.uint32()
			i = reader.uint8()
			yield ("post_post", (q, i))
		else:
			yield ("undefined", command)

reader = Reader(open('/home/wojtek/tmp/a.dvi').read())
for item in parse(reader):
	print item

# changelog
"""
 9.03.2007
	+ safe_float
	+ get_bbox/get_width/get_height
	+ collect_Id
"""

def safe_float(string, default=0.0):
	try:
		return float(string)
	except ValueError:
		return default


def get_bbox(object):
	"Returns BBox of given object (rect/circle/ellipse are supported)"

	tag = object.tagName

	def safe_get(object, attribute):
		return safe_float(object.getAttribute(attribute))
	if tag == 'rect':
		Xmin = safe_get(object, 'x')
		Ymin = safe_get(object, 'y')
		Xmax = Xmin + safe_get(object, 'width')
		Ymax = Ymin + safe_get(object, 'height')
	elif tag == 'circle':
		cx = safe_get(object, 'cx')
		cy = safe_get(object, 'cy')
		rx = ry = safe_get(object, 'r')

		Xmin = cx - rx
		Ymin = cy - ry
		Xmax = cx + rx
		Ymax = cy + ry

	elif tag == 'ellipse':
		cx = safe_get(object, 'cx')
		cy = safe_get(object, 'cy')
		rx = safe_get(object, 'rx')
		ry = safe_get(object, 'ry')

		Xmin = cx - rx
		Ymin = cy - ry
		Xmax = cx + rx
		Ymax = cy + ry
	else:
		raise ValueError("Can't deal with tag <%s>" % tag)

	return (Xmin, Ymin, Xmax, Ymax)


def get_width(object):
	"Returns width of object"
	xmin, ymin, xmax, ymax = get_bbox(object)
	return xmax-xmin


def get_height(object):
	"Returns width of object"
	xmin, ymin, xmax, ymax = get_bbox(object)
	return ymax-ymin


def collect_Id(XML, d={}):
	# hack
	for object in XML.childNodes:
		try:
			v = object.getAttribute('id')
			if v: d.update([(v, object)])
		except AttributeError: # no hasAttr
			pass
		collect_Id(object, d)

# vim: ts=4 sw=4 noexpandtab nowrap

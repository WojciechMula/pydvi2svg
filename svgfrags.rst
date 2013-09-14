
``SVGfrags``
------------------------------------------------------------------------

``SVGfrags`` is utility build on top of ``pydvi2svg``, that 
includes pieces of TeX/LaTeX expressions into existing SVG file.
It works similar to well known ``psfrags`` LaTeX package, but
has some additional features.

``SVGfrags`` is distributed with ``pydvi2svg``, see Installation__ section.

__ index.html#installation

Replacement rules have to be defined in separate file, and
must follow this simple syntax::

	SVG target => TeX expression [additional options]
	% the same comments style as in (La)TeX


You can see `detailed syntax`__, or **better** read next
sections and take a look at example.

__ frags/svgfrags_grammar.txt


Brief overview
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``SVG target`` could be (case A):

- Quoted text phrase, for example ``"some text"`` --- all
  occurrences of ``some text`` are **replaced** by adequate
  *TeX expression*.
- XML id attribute --- ``<text>`` node that has such id
  is **replaced** with adequate *TeX expression*.
- ``point(x, y)`` --- put *TeX expression* at arbitrary
  position.


Additionally ``SVG target`` could refer to rectangular area,
where *TeX expression* is placed (case B):

- XML id attribute refers to element ``<rect>``, ``<circle>``
  or ``<ellipse>`` (bounding box of these objects are considered).
- ``rect(x, y, width, height)`` --- arbitrary defined rectangle.


*TeX expression* could be:

- Quoted string, like ``"$\sin x + \cos x = 1$"``
- Word ``this`` (unquoted!) --- if ``SVG target`` is text or
  id refers to ``<text>`` node, then *TeX expression* gets
  value of ``SVG target``.  In other words TeX expression
  are read from SVG document.


Additional options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``position``
::::::::::::::::::::::::::::::

Place *TeX expression* relative to ``SVG target`` object.

Syntax::

	position ::= px ["," py]

By default ``py = 1.0`` and ``px = 0.0`` (case B) or ``px = inherit``
(case A).

Arguments ``px`` and ``py`` define point inside rectangle (bounding box
of *TeX expression*, and also in target rectangle in case B). For
example ``px = 0.5``, ``py = 0.5`` is center point; ``px = 0.0``,
``py = 1.0`` --- left lower corner, and so on.

``px`` and ``py`` can be:

* number
* percent, i.e. number followed by char '%'

Some useful constants are also defined:

* ``px`` --- ``center = 0.5``, ``left = 0.0``, ``right = 1.0``
* ``py`` --- ``center = 0.5``, ``top = 0.0``, ``bottom = 1.0``


**case A** --- ``SVG target`` points to **reference point** in document canvas
	Point inside bbox of *TeX expression* is calculated and then
	expression is moved to make this point and **reference** equal.

	In this case ``px`` can have value ``inherit`` (default),
	then ``px`` gets value (if possible) from SVG attribute
	``text-anchor`` or from CSS style string.  These values are
	``start = 0.0``, ``middle = 0.5`` and ``end = 1.0`` (see
	`SVG spec`__ for more info about ``text-anchor``).

	__ http://www.w3.org/TR/SVG/text.html#TextAnchorProperty


**case B** --- ``SVG target`` points to **rectangular area**
	Points inside bbox of *TeX expression* **and** target
	rectangle are calculated and then expression is moved
	to make these points equal.

	For example if ``px = 0.5``, ``py = 0.5`` then *TeX
	expression* is centered.


``margins``
::::::::::::::::::::::::::::::


Additional margins around bounding box of *TeX expression*; applied
**before** scaling.  Syntax:

- ``margin: m`` --- left, right, top and bottom margin are equal ``m``
- ``margin: mx, my`` --- left and right are equal ``mx``, top and bottom
  margin are equal ``my``
- ``margin: ml, mr, mt, mb`` --- all margins can have different values


``scale``
::::::::::::::::::::::::::::::

Uniform or nonuniform scale of *TeX expression*.

Syntax::

	scale: "fit" | (sx ["," sy])

Value ``fit`` is suitable only in case B --- *TeX expression* is
uniformly scaled to fill a target rectangle.

Scale factor ``sx``/``sy`` values:

- Number;
- Percent;
- Word ``uniform`` --- if just one scale direction is set and
  uniform scaling is needed, then another direction have get this
  value;   if both ``sx`` and ``sy`` has value ``uniform`` then 
  no scale is applied;
- Word ``length`` followed by number --- set width/height
  of *TeX expression* to exact value;
- ``width(#id)``/``height(#id)`` --- set width/height of
  *TeX expression* to width or height of object with given id;
- ``width(this)``/``height(this)`` --- set width/height
  of *TeX expression* to width or height of ``SVG target``
  rectangle; valid only in case B.


Command line options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``-i``, ``--input``
	SVG input file

``-o``, ``--output``
	SVG input file

``-r``, ``--rules``
	name of text file that contains replacement pairs

``--no-strip``
	By default leading & trailing spaces in strings (target string &
	SVG text) are stripped --- this options disabled it

``--keep-tex``
	Do not remove temporary TeX files (useful for debugging)

``--keep-dvi``
	Do not remove temporary DVI files;  if rules file are not changed,
	then DVI can be resued

``--no-hide-text-obj``
	By default replaced text nodes are hide, i.e. property
	``display`` gets value ``none`` --- this option disables it.

``--remove-text-obj``
	Remove replaced text nodes.

``-f``, ``--force-overwrite``
	By default ``SVGfrags`` do not overwrite existing
	files --- this option turns off protection.

``--traceback``
	In case of error whole Python traceback is printed;
	it is useful just for debugging.


``SVGfrags`` accepts also following ``pydvi2svg`` options:

* ``--enc``
* ``--enc-repl``
* ``--no-fontforge``
* ``--no-fnt2meta``



Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Substitution list:
	.. include:: samples/svgfrags-sample.txt
	   :literal:

Sample `source image <samples/svgfrags-sample.svg>`_ I've drawn in Inkscape_
	.. image:: samples/svgfrags-sample.png
	   :align: center

`Result <samples/svgfrags-sample-res.svg>`_
	.. image:: samples/svgfrags-sample-res.png
	   :align: center

`Result (marked bounding boxes and reference points of TeX expressions <samples/svgfrags-sample-debug.svg>`_ 
	.. image:: samples/svgfrags-sample-debug.png
	   :align: center


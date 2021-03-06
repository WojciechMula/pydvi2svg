
``pydvi2svg``
------------------------------------------------------------------------

Introduction
~~~~~~~~~~~~

This is another DVI to SVG converter (and is written in Python_).

When I was started to write this program I just want to export
**mathematical expressions**.  But since DVI is just a set of commands
that puts characters and move magic current point around a page,
``pydvi2svg`` is able to convert any kind of document.

There is partial support for ``color.sty`` specials.

Why another converter?  Because programs I've checked --- if they worked of
course --- embeded SVG font in the file.  This is not supported by most
SVG viewer/editor programs, including Inkscape_ that I use often.
Because of that ``pydvi2svg`` embeds *glifs* as a paths and simply links
to them. It works perfectly. Tested with gqview, rsvg, Inkscape,
Firefox 1.5-2.0 and Opera 9.


Samples
~~~~~~~

1. Article borrowed from English Wikipedia about DVI file format.
   Font face used: *Computer Modern*.

	* TeX__
	* DVI__
	* SVG `page 1`__ i `2`__

__ samples/sample1.tex
__ samples/sample1.dvi
__ samples/sample10001.svg
__ samples/sample10002.svg

2. Article borrowed from polish Wikipedia about `Antykwa
   Półtawskiego`__ --- the original polish font face.  Of course
   if you open SVG you will see this font "in action".

	* TeX__
	* DVI__
	* SVG__

__ https://pl.wikipedia.org/wiki/Antykwa_P%C3%B3%C5%82tawskiego
__ samples/sample2.tex
__ samples/sample2.dvi
__ samples/sample20001.svg

Wikipedia articles are licensed under GNU GFDL license.


Prerequisites
~~~~~~~~~~~~~

- Python_ interpreter, version 2.4
- If you need additional SVG fonts, you will need TeX installation
  (all its' utilities, fonts, etc.) and:

  * fnt2meta__ --- pydvi2svg utility to convert Type1 fonts; if you don't
    need METAFONT, just Type1 fonts this utility should be enough
  * free, multiplatform font editor Fontforge_ that is able
    to save SVG fonts (pydvi2svg uses Fontforge to convert Type1
    fonts)
  * mftrace__ and autotrace__ or potrace__ --- to convert METAFONT
    fonts to SVG

__ fnt2meta.c
__ http://lilypond.org/mftrace/
__ http://autotrace.sourceforge.net
__ http://potrace.sourceforge.net


Installation
~~~~~~~~~~~~

Following archives are needed:

1. `pydvi2svg.tar.bz2 <pydvi2svg.tar.bz2>`_	--- source files of ``pydvi2svg`` & ``SVGfrags``
2. `fonts.tar.bz2 <fonts.tar.bz2>`_ ---  *Computer Modern* fonts converted to SVG 

If you have them, then::

	$ tar -xjf pydvi2svg.tar.bz2
	$ tar -xjf fonts.tar.bz2

After correct installation directory tree should looks
as follow::

	pydvi2svg
	 |
	 +- cache           - empty dir
	 +- conv            - dvi2svg program files
	 +- frags           - SVGfrags program files
	 +- enc             - set of *.enc files
	 +- fonts
	     |
	     +- cm          - set of *.svg files


Now you can create symbolic link to pydvi2svg.py (and/or svgfrags.py)
in some directory listed from ``$PATH``, for example::

	sudo ln -sf <full path to script>/dvi2svg.py /usr/local/bin/

If ``realpath`` utility is present in your system, then::

	sudo ln -sf `realpath pydvi2svg/dvi2svg.py` /usr/local/bin


Program options
~~~~~~~~~~~~~~~

::

	dvi2svg.py [OPTION] file.dvi [target SVG/dir]
	  	
For example::

	dvi2svg.py file.dvi                   # output: file.svg 
	dvi2svg.py file.dvi test.svg          # output: test.svg
	dvi2svg.py file.dvi dir/              # output: dir/file.svg
	dvi2svg.py file.dvi dir/test.svg      # output: dir/test.svg

You can set as many input-output pairs as you want, for example::

	dvi2svg.py file1.dvi file2.dvi output2.svg file3.dvi outputdir


**Options**:

``--pages`` [list]
	List of document pages or page ranges to convert.  List's
	element are separated by colons.  Examples::

		--pages 1,2,3,4,7       # convert pages 1, 2, 3, 4 and 7
		--pages 1-4,7           # above shorter
		--pages 7-              # convert all pages starting from 7th
		--pages -10             # convert pages 1-10
	
	By default all pages are converted.

``--enc-method`` [list]
	Choose methods used to determine font encoding:

	* ``cache`` (or ``c``) --- encoding is readed from file
	  ``enc/font.info`` (or is set with option ``--enc``)
	* ``TFM`` (or ``t``) --- encoding is readed from TFM associated with font
	* ``AFM`` (or ``a``) --- encoding is readed from AFM associated with font
	* ``MAP`` (or ``m``) --- scans all ``.map`` files and try
	  to find encoding used by other programs (like ``dvipis``);
	  it is quite slow, but could bring good results if Type1
	  fonts are used
	* ``guess`` (or ``g``) --- scans all known encodings (stored in
	  files ``enc/*``) and hit best one, i.e. encoding that covers
	  all or almost all characters defined in font; it could find
	  more then one encoding --- in this case propositions are printed
	  and programs do not perform any action; you have to try proposed
	  encodings by passing them with ``--enc`` switch

	Default value: **cache,tfm,afm**

``--enc`` [list]
	Override (or set) encoding of selected fonts.  Elements are
	separated with colons, and has format ``font name``:``encoding name``.
	For example::
	
		--enc cmr12:ot1,pltt12:pltt

``--scale`` **[non-negative number]**
	Change default scale of document

	Default value: **1.0**

``--paper-size`` **[value]**

	value:

	* page format name, like A4, B3, etc. (see Wikipedia__);
	  for example ``--paper-size A4``, ``--paper-size=B5``
	* string ``query`` --- all known names are printed and program exits
	* string ``bbox`` --- paper size is set to bounding box of page;
	  additionaly margin around bbox can be set:
	  
	  - ``bbox:margin`` --- all margin equal
	  - ``bbox:marginx,marginy`` --- margin left & right equal marginx,
	    margin top & bottom equal marginy
	  - ``bbox:margin_left,margin_right,margin_top,margin_bottom``
	  
	  for example ``--paper-size=bbox:10``, ``--paper-size bbox:5,20``,
	  ``--paper-size=bbox:10,20,30,40``

	Default value: **A4**

__ https://en.wikipedia.org/wiki/Paper_size

``--always-number``
	Append page number to output name even if **one** page
	is converted.

``--single-file``
	All pages are saved in single file. (By default pages are
	saved in separate files).

``--no-fontforge``
	Never use Fontforge (even if it is present)

``--no-fnt2meta``
	Never use fnt2meta (even if it is present)

``--verbose``
	Print all messages.

``--pretty-xml``
	"Pretty formatting" of SVG (files become larger, but are easy
	to read).


Solving common problems
~~~~~~~~~~~~~~~~~~~~~~~

Where can I find other fonts saved in SVG format
::::::::::::::::::::::::::::::::::::::::::::::::

The easiest way is to convert your own fonts with Fontforge_ assistance.
SVG font have to be placed in ``fonts`` directory or its subdirectory.

Fontforge is able to read most vector font formats---in a TeX
installation we usually find Type1 fonts (``PFB`` or ``PFA``).
If there is just Metafont source, you still can convert font:
Fontforge use autotrace_ or potrace_ to trace glyph's vector
outlines.


Before you create font (**Generate font...**) assure that glyph's
names are not changed (option **No Rename** set).

.. _autotrace:	http://autotrace.sourceforge.net
.. _potrace:	http://potrace.sourceforge.net


If you use other utility, make sure that output SVG fits following
rules:

* ``<glyph>`` element has attributes ``name`` and ``d`` (path)
* if element hasn't got ``d`` attribute there must be just one child
  element ``<path>`` contains it

SVG have to get following structure:: 

	<font>
		<glyph name="..." d="..."/>
		<glyph name="..." d="..."/>
		...
	</font>

or

::
	
	<font>
		<glyph name="...">
			<path d="..."/>
		</glyph>
		<glyph name="...">
			<path d="..."/>
		</glyph>
		...
	</font>

(Of course these rules are not fixed and I'm able to change them, but
have never met SVG fonts with different structure).


I got warning ``missing char``
::::::::::::::::::::::::::::::

Usually it means that encoding of certain font is not correct.  Try
to change it with command line option ``--enc``: look in ``enc``
subdirectory or locate other ``.enc`` files in your TeX installation.

If you find correct encoding you can change ``pydvi2svg`` settings
permanently.  You have to update file ``enc/file.info``; single
line has format::

	font_name        encoding_name        designsize

Here is a sample::

	pltt12           pltt                 12.000000



``pydvi2svg`` tries to find TFM files and read encoding name (it tries
AFM files too, but it is not well tested).   But if SVG font has been
converted from, for example, Type1 format its' encoding may be
different.

For example TFM file that describe font ``pltt12`` claims that encoding
is "TeX typewriter text", i.e. ``texnansi``. But since this font was
converted from ``PFB`` we have to a look into some ``.map`` file, and
than will notice that TeX applies encoding file called ``pltt.enc`` (so,
we must set encoding ``pltt``). 

Likewise CM fonts may have encoding OT1 instead of T1.


I got error ``Unknown TeX/AFM encoding``
::::::::::::::::::::::::::::::::::::::::

You have to check which ``*.enc`` describe reported encoding.
Files are placed in directory ``enc`` and somewhere in your
TeX installation tree.  If you find adequate encoding, then
update file ``enc/enc.info`` (and of course drop
me a line).


.. _Fontforge:	http://fontforge.sourceforge.net/
.. _Python:	    http://www.python.org/
.. _SVG:	    http://www.w3.org/TR/SVG/
.. _Inkscape:   http://www.inkscape.org/
.. _BSD:        http://www.opensource.org/licenses/bsd-license.php

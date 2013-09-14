========================================================================
                      pydvi2svg & SVGfrags
========================================================================

``pydvi2svg`` converts DVI files (output from TeX) to SVG vector graphics

``SVGfrags`` is utility build on top of ``pydvi2svg``, that 
includes pieces of TeX/LaTeX expressions into existing SVG file.


Documentation
------------------------------------------------------------------------

* `pydvi2svg`__
* `SVGfrags`__

__ doc/pydvi2svg.doc
__ doc/svgfrags.doc

License
------------------------------------------------------------------------

* Both **programs**, i.e. ``pydvi2svg`` & ``SVGfrags`` are licensed
  under BSD_ license.
* Fonts keep their licenses and copyrights.  I putted them here
  in a other format to make user's life bit easier.


News
------------------------------------------------------------------------

13.03.2007

	* Beta version of ``SVGfrags``!
	* **pl**: Na razie usuwam polską dokumentację, bo się trochę
	  zdezaktualizowała, a naprawdę są ciekawsze rzeczy od jej
	  pisania.


7.03.2007

	* Better, and I hope more obvious, command line parsing.  Now
	  output file name or output directory can be set.  For example::

	  	dvi2svg.py file.dvi                   # output: file.svg 
		dvi2svg.py file.dvi test.svg          # output: test.svg
		dvi2svg.py file.dvi dir/              # output: dir/file.svg
		dvi2svg.py file.dvi dir/test.svg      # output: dir/test.svg
	
	* New option ``--always-number`` --- affects on output file name:
	  append page number to output name even if **one** page is converted.

	* Option ``--paper-size=bbox`` accepts four numbers, for left,
	  right, top and  bottom margin, i.e.
	  ``--paper-size=bbox:left,right,top,bottom``

6.03.2007
	
	* Switch ``--paper-size`` accept new keyword ``bbox`` (see description
	  of this option for details) --- paper size is set to bounding box
	  of page.
	  
	  Sample: `famous Einstein equation <samples/emc2.svg>`_
	* new option ``--verbose``

4.03.2007

	* added support for ``mftrace`` utility --- automatically conversion
	  of METAFONT fonts is available

3.03.2007

	* generate a bit smaller SVG files
	* new options ``--no-fontforge`` and ``--no-fnt2meta`` that
	  disables use of FontForge/fnt2meta
	* option ``--paper-size`` accepts value "query" --- all known
	  names & sizes are printed

2.03.2007

	* Improved ``.PFA``/``.PFB`` searching
	* Another bug fixed

1.03.2007
	
	Some bugs were fixed, thanks for help to **R (Chandra)
	Chandrasekhar**.

16.10.2006

	If ``pydvi2svg`` can't find SVG but Type1 fonts (``PFA`` or ``PFB``)
	are available in your TeX installation then **automatically** use
	FontForge (or fnt2meta) to converts such font.
	
	`fnt2meta.c`__ is a small utility that reads font file and prints
	glyph outlines (need FreeType2_).  Compilation::

		gcc -O2 -lfreetype fnt2meta.c -o fnt2meta
	
	or::
		
		gcc -O2 `freetype-config --libs` `freetype-config --cflags` -o fnt2meta fnt2meta.c
	

15.10.2006

	New methods to determine encoding (see ``--enc-methods`` switch)

__ fnt2meta.c
.. _FreeType2:	http://www.freetype.org




Remarks, errors, patches
------------------------------------------------------------------------

Please send to author any remarks, bugs, patches, questions, etc.:

	Wojciech Muła, wojciech_mula@poczta.onet.pl



.. _Fontforge:	http://fontforge.sourceforge.net/
.. _Python:	    http://www.python.org/
.. _SVG:	    http://www.w3.org/TR/SVG/
.. _Inkscape:   http://www.inkscape.org/
.. _BSD:        http://www.opensource.org/licenses/bsd-license.php

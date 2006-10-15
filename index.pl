Polski
------------------------------------------------------------------------

.. _Fontforge:	http://fontforge.sourceforge.net/
.. _Python:	    http://www.python.org/
.. _SVG:	    http://www.w3.org/TR/SVG/
.. _Inkscape:   http://www.inkscape.org/
.. _BSD:        http://www.opensource.org/licenses/bsd-license.php


Wprowadzenie
~~~~~~~~~~~~

G³ównym celem jaki stawia³em sobie pisz±c ten program by³a mo¿liwo¶æ
³atwego wstawiania **wzorów** z³o¿onych w LaTeX-u do obrazków zapisanych
w formacie SVG_.  Istnieje te¿ czê¶ciowe wsparcie dla pakietu ``color.sty``.

Dlaczego kolejny konwerter?  Programy które testowa³em, o ile rzecz
jasna uda³o mi siê uruchomiæ, osadza³y fonty w plikach SVG i ustawia³y
odpowiednie w³asno¶ci stylu.  Tego niestety nie obs³uguje wiêkszo¶æ
programów do wy¶wietlania/edycji plików SVG, w tym u¿ywany przeze mnie
Inkscape_.  Dlatego ``pydvi2svg`` osadza glify bezpo¶rednio w rysunku, a
z tym ju¿ ¿aden program nie powinien mieæ k³opotów --- testowane w
Inkscape, Firefox 1.5 oraz gqview.


Przyk³ad
~~~~~~~~

1. Artyku³ z Wikipedii nt plików DVI (tekst z³o¿ony krojem *Computer
   Modern*):

	* TeX__
	* DVI__
	* SVG `strona 1.`__ i `2.`__

__ samples/sample1.tex
__ samples/sample1.dvi
__ samples/sample10001.svg
__ samples/sample10002.svg

2. Artyku³ z polskiej Wikipedii z³o¿ony :plwiki:`Antykwa Pó³tawskiego|Antykw±
   Pó³tawkiego` na temat tego¿ kroju:

	* TeX__
	* DVI__
	* SVG__

__ samples/sample2.tex
__ samples/sample2.dvi
__ samples/sample20001.svg


Wymagania wstêpne
~~~~~~~~~~~~~~~~~

- Dzia³aj±cy interpreter jêzyka Python_ w wersji 2.4
- Je¶li potrzebne bêd± inne fonty ni¿ dostêpne tutaj nale¿y
  mieæ zaintalowanego TeX z przyleg³o¶ciami, oraz darmowy
  program Fontforge_ do konwersji fontowych plików.

Instalacja
~~~~~~~~~~

Nale¿y ¶ci±gn±æ dwa archiwa:

1. `pydvi2svg.tar.bz2 <pydvi2svg.tar.bz2>`_	--- pliki ¼ród³owe
2. `fonts.tar.bz2 <fonts.tar.bz2>`_			--- fonty *Computer Modern* w formacie SVG

Kolejne kroki instalacji:

1. Rozpakowaæ plik ``pydvi2svg.tar.bz2`` - utworzony zostanie katalog ``pydvi2svg``
2. Przej¶æ do tego katalogu 
3. Rozpakowaæ w nim plik ``fonts.tar.bz2`` -- utworzony zostanie
   podkatalog ``fonts``.


Po poprawnej instalacji struktura katalogów powinna wygl±daæ
nastêpuj±co::

	pydvi2svg
	 |
	 +- enc
	 |
	 +- fonts
	     |
	     +- cm



Opcje programu
~~~~~~~~~~~~~~

::

    python dvi2svg.py  [OPCJE] pliki.dvi ...


**Opcje**:

``--pages`` [lista]
	Lista stron lub zakresów stron, które maj± zostaæ przetworzone.
	Kolejne elementy listy s± oddzielane przecinkami, np.::

		--pages 1,2,3,4,7       # przetworzenie stron 1, 2, 3, 4 oraz 7
		--pages 1-4,7           # powy¿sze krócej
		--pages 7-              # przetworzenie stron od 7 do koñca
		--pages -10             # przetworzenie stron od pierwszej do 10
	
	(Domy¶lnie konwertowane s± wszystkie strony).

``--enc-method`` [lista] **(nowe)**
	Lista nazw oddzielonych przecinkami.

	Okre¶la metody wyznaczania kodowania dla fontów oraz kolejno¶æ 
	w jakiej zostan± wykonane:

	* ``cache`` (lub ``c``) --- kodowanie jest pobierane z pliku
	  ``enc/font.info`` (lub z linii poleceñ, je¶li zastosowano
	  opisan± ni¿ej opcjê ``--enc``)
	* ``TFM`` (lub ``t``) --- kodowanie jest odczytywane z pliku TFM
	* ``AFM`` (lub ``a``) --- kodowanie jest odczytywane z pliku AFM
	* ``MAP`` (lub ``m``) --- metoda do¶æ powolna, powinna byæ stosowana
	  gdy fonty SVG zosta³y skonwertowane z formatu Type1: skanuje
	  wszystkie pliki map i próbuje znale¼æ w jaki sposób mapuj± ten
	  font inne programy (np. ``dvips``)
	* ``guess`` (lub ``g``) --- ,,dochochodzimy do wyniku
	  najszlachetniejsz± metod± znan± matematyce --- zgadujemy''; a na
	  powa¿nie: wyszukiwane jest takie kodowanie, które pokrywa jak
	  najwiêksz± liczbê znaków dostêpnych w foncie SVG.  Mo¿e zdarzyæ
	  siê tak, ¿e zostanie znalezione wiêcej plików kodowañ i wówczas
	  program koñczy siê --- wówczas nale¿y wypróbowaæ podane kodowania
	  (opcja ``--enc``).

	Domy¶lnie: cache,tfm

``--enc`` [lista]
	Nadpisanie u¿ywanych przez ``pydvi2svg`` kodowañ dla okre¶lonych
	fontów.  Elementy listy s± oddzielone przecinkami, a ka¿dy ma format
	``nazwa_fontu``:``nazwa kodowania``, np.::

		--enc cmr12:ot1,pltt12:pltt

``--scale`` [liczba rzeczywista=1.0]
	Zmiana domy¶lnego skalowanie dokumentu

``--paper-size`` [nazwa formatu strony=A4]
	Ustalenie okre¶lonego formatu strony (nazwy zgodne
	z norm± :plwiki:`Format arkusza|ISO 216`)

``--single-file``
	Wszystkie strony trafiaj± do jednego pliku.  (Domy¶lnie ka¿da stron
	wêdruje do odrêbnego pliku).

``--pretty-xml``
	,,£adne formatowanie'' wynikowego pliku SVG (pliki staj± siê wiêksze)


Rozwi±zywanie problemów
~~~~~~~~~~~~~~~~~~~~~~~

Sk±d wzi±æ inne fonty w formacie SVG?
:::::::::::::::::::::::::::::::::::::

Najpro¶ciej skonwertowaæ zainstalowane w systemie fonty za pomoc±
**darmowego**, **wieloplatformowego** programu Fontforge_.
Wynikowe pliki musz± trafiæ do katalogu ``fonts`` (lub jego
podkatalogu).


Fontforge potrafi odczytaæ wiêkszo¶æ fontów wektorowych, w TeX-u
przewa¿nie bêd± to formaty ``PFB`` lub ``PFA``.  Gdyby takowych
plików nie by³o, to je¶li tylko zainstalowane s± narzêdzia
autotrace_ lub potrace_ odczytaæ tak¿e fonty MetaFontowe.

Przy generowaniu pliku (**Generate font...**) nale¿y upewniæ siê,
¿e nie s± zmieniane nazwy znaków (ustawione **No Rename**).

.. _autotrace:	http://autotrace.sourceforge.net
.. _potrace:	http://potrace.sourceforge.net


Je¶li u¿ywasz innego programu upewnij siê, ¿e glify w wynikowym pliku
SVG maj± nazwê (atrybut ``name``) oraz ¶cie¿kê (atrybut ``d``).  Je¶li
nie ma ¶cie¿ki bezpo¶rednio w tagu ``<glyhp>`` powinien istnieæ potomny
wêze³ o nazwie ``<path>`` z atrybutem ``d``.  Plik SVG musi mieæ
mniej wiêcej tak± strukturê::

	<font>
		<glyph name="..." d="..."/>
		<glyph name="..." d="..."/>
		...
	</font>

lub

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

(Je¶li bêdzie taka potrzeba mogê rzecz jasna rozszerzyæ akceptowane
struktury SVG, po prostu do tej pory nie spotka³em siê z innymi).

Dostajê komunikat ``missing char``
::::::::::::::::::::::::::::::::::

Oznacza to zazwyczaj, ¿e wybrane jest niew³a¶ciwe kodowanie dla danego
fontu.  Nale¿y spróbowaæ podaæ kodowanie z linii poleceñ opcj±
``--enc``.

Je¶li po ponownym uruchomieniu znikn± te komunikaty, to znaczy, ¿e
wybrali¶my dobre kodowanie i wówczas mo¿na na sta³e zmieniæ wpis w pliku
``enc/file.info``. Pojedynczy wiersz ma format::

	nazwa_fontu        nazwa_kodowania        designsize

powinno to wygl±daæ np. tak::

	pltt12             pltt                   12.000000


Program ``pydvi2svg`` je¶li tylko mo¿e zagl±da do plików TFM i odczytuje
stamt±d nazwê kodowania (próbuje tak¿e pliki AFM, ale to nie jest dobrze
przetestowane).  Jednak je¶li konwersja do formatu SVG zosta³a wykonana
z formatu np. PFB to kodowanie w tym pliku mo¿e siê ró¿niæ.

Np. dla fontu ``pltt12`` (przekonwertowane z pliku PFB) program odczyta
z TFM-a kodowanie "TeX typewriter text", czyli ``texnansi``. Ale je¶li
zagl±dniemy do jakiego¶ pliku map, oka¿e siê, ¿e plik ``pltt12.pfb``
jest przekodowywany przez ``pltt.enc`` (czyli kodowanie powinno byæ jak
w powy¿szym przyk³adzie --- ``pltt``).

Podobnie fonty CM mog± mieæ inne kodowanie, u mnie jest to OT1.


Dostajê b³±d ``Unknown TeX/AFM encoding``
:::::::::::::::::::::::::::::::::::::::::

Nale¿y stwierdziæ jakiemu plikowi ``*.enc`` z katalogu ``enc`` lub
instalacji TeX-a jest przyporz±dkowane dane kodowanie i uzupe³niæ
wpis w pliku ``enc/enc.info``.  Oraz koniecznie mnie o tym powiadomiæ.


Znane problemy
~~~~~~~~~~~~~~

To jest problem Inkscape_, ale poniewa¿ odkry³em go podczas edycji
plików wygenerowanych przez ``pldvi2svg`` wiêc ostrzegam.

W Inkscape 0.44.1 z locales ``LC_ALL=pl_PL`` przy przesuwaniu strony
niektóre litery mog± staæ siê ogromne (program gubi informacje o
przekszta³ceniach); zmiana locales na ``LC_ALL=C`` rozwi±zuje problem.


Licencja
~~~~~~~~

* **Licencja programu** --- BSD_.
* Licencja fontów --- taka sama jak ¼ród³owych, tzn. tych rozprowadzanych
  w dystrybucjach TeX-a.  Udostêpniam je tutaj w innym formacie jedynie dla
  wygody PT U¿ytkowników.


Uwagi, wnioski, poprawki
~~~~~~~~~~~~~~~~~~~~~~~~

Uprzejmie proszê wszelkie uwagi, wnioski, poprawki, pytania itd.
kierowaæ do autora:

	Wojciech Mu³a, wojciech_mula@poczta.onet.pl

..
	vim: tw=72 ts=4 sw=4 noexpandtab

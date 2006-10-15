Polski
------------------------------------------------------------------------

.. _Fontforge:	http://fontforge.sourceforge.net/
.. _Python:	    http://www.python.org/
.. _SVG:	    http://www.w3.org/TR/SVG/
.. _Inkscape:   http://www.inkscape.org/
.. _BSD:        http://www.opensource.org/licenses/bsd-license.php


Wprowadzenie
~~~~~~~~~~~~

G��wnym celem jaki stawia�em sobie pisz�c ten program by�a mo�liwo��
�atwego wstawiania **wzor�w** z�o�onych w LaTeX-u do obrazk�w zapisanych
w formacie SVG_.  Istnieje te� cz�ciowe wsparcie dla pakietu ``color.sty``.

Dlaczego kolejny konwerter?  Programy kt�re testowa�em, o ile rzecz
jasna uda�o mi si� uruchomi�, osadza�y fonty w plikach SVG i ustawia�y
odpowiednie w�asno�ci stylu.  Tego niestety nie obs�uguje wi�kszo��
program�w do wy�wietlania/edycji plik�w SVG, w tym u�ywany przeze mnie
Inkscape_.  Dlatego ``pydvi2svg`` osadza glify bezpo�rednio w rysunku, a
z tym ju� �aden program nie powinien mie� k�opot�w --- testowane w
Inkscape, Firefox 1.5 oraz gqview.


Przyk�ad
~~~~~~~~

1. Artyku� z Wikipedii nt plik�w DVI (tekst z�o�ony krojem *Computer
   Modern*):

	* TeX__
	* DVI__
	* SVG `strona 1.`__ i `2.`__

__ samples/sample1.tex
__ samples/sample1.dvi
__ samples/sample10001.svg
__ samples/sample10002.svg

2. Artyku� z polskiej Wikipedii z�o�ony :plwiki:`Antykwa P�tawskiego|Antykw�
   P�tawkiego` na temat tego� kroju:

	* TeX__
	* DVI__
	* SVG__

__ samples/sample2.tex
__ samples/sample2.dvi
__ samples/sample20001.svg


Wymagania wst�pne
~~~~~~~~~~~~~~~~~

- Dzia�aj�cy interpreter j�zyka Python_ w wersji 2.4
- Je�li potrzebne b�d� inne fonty ni� dost�pne tutaj nale�y
  mie� zaintalowanego TeX z przyleg�o�ciami, oraz darmowy
  program Fontforge_ do konwersji fontowych plik�w.

Instalacja
~~~~~~~~~~

Nale�y �ci�gn�� dwa archiwa:

1. `pydvi2svg.tar.bz2 <pydvi2svg.tar.bz2>`_	--- pliki �r�d�owe
2. `fonts.tar.bz2 <fonts.tar.bz2>`_			--- fonty *Computer Modern* w formacie SVG

Kolejne kroki instalacji:

1. Rozpakowa� plik ``pydvi2svg.tar.bz2`` - utworzony zostanie katalog ``pydvi2svg``
2. Przej�� do tego katalogu 
3. Rozpakowa� w nim plik ``fonts.tar.bz2`` -- utworzony zostanie
   podkatalog ``fonts``.


Po poprawnej instalacji struktura katalog�w powinna wygl�da�
nast�puj�co::

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
	Lista stron lub zakres�w stron, kt�re maj� zosta� przetworzone.
	Kolejne elementy listy s� oddzielane przecinkami, np.::

		--pages 1,2,3,4,7       # przetworzenie stron 1, 2, 3, 4 oraz 7
		--pages 1-4,7           # powy�sze kr�cej
		--pages 7-              # przetworzenie stron od 7 do ko�ca
		--pages -10             # przetworzenie stron od pierwszej do 10
	
	(Domy�lnie konwertowane s� wszystkie strony).

``--enc-method`` [lista] **(nowe)**
	Lista nazw oddzielonych przecinkami.

	Okre�la metody wyznaczania kodowania dla font�w oraz kolejno�� 
	w jakiej zostan� wykonane:

	* ``cache`` (lub ``c``) --- kodowanie jest pobierane z pliku
	  ``enc/font.info`` (lub z linii polece�, je�li zastosowano
	  opisan� ni�ej opcj� ``--enc``)
	* ``TFM`` (lub ``t``) --- kodowanie jest odczytywane z pliku TFM
	* ``AFM`` (lub ``a``) --- kodowanie jest odczytywane z pliku AFM
	* ``MAP`` (lub ``m``) --- metoda do�� powolna, powinna by� stosowana
	  gdy fonty SVG zosta�y skonwertowane z formatu Type1: skanuje
	  wszystkie pliki map i pr�buje znale�� w jaki spos�b mapuj� ten
	  font inne programy (np. ``dvips``)
	* ``guess`` (lub ``g``) --- ,,dochochodzimy do wyniku
	  najszlachetniejsz� metod� znan� matematyce --- zgadujemy''; a na
	  powa�nie: wyszukiwane jest takie kodowanie, kt�re pokrywa jak
	  najwi�ksz� liczb� znak�w dost�pnych w foncie SVG.  Mo�e zdarzy�
	  si� tak, �e zostanie znalezione wi�cej plik�w kodowa� i w�wczas
	  program ko�czy si� --- w�wczas nale�y wypr�bowa� podane kodowania
	  (opcja ``--enc``).

	Domy�lnie: cache,tfm

``--enc`` [lista]
	Nadpisanie u�ywanych przez ``pydvi2svg`` kodowa� dla okre�lonych
	font�w.  Elementy listy s� oddzielone przecinkami, a ka�dy ma format
	``nazwa_fontu``:``nazwa kodowania``, np.::

		--enc cmr12:ot1,pltt12:pltt

``--scale`` [liczba rzeczywista=1.0]
	Zmiana domy�lnego skalowanie dokumentu

``--paper-size`` [nazwa formatu strony=A4]
	Ustalenie okre�lonego formatu strony (nazwy zgodne
	z norm� :plwiki:`Format arkusza|ISO 216`)

``--single-file``
	Wszystkie strony trafiaj� do jednego pliku.  (Domy�lnie ka�da stron
	w�druje do odr�bnego pliku).

``--pretty-xml``
	,,�adne formatowanie'' wynikowego pliku SVG (pliki staj� si� wi�ksze)


Rozwi�zywanie problem�w
~~~~~~~~~~~~~~~~~~~~~~~

Sk�d wzi�� inne fonty w formacie SVG?
:::::::::::::::::::::::::::::::::::::

Najpro�ciej skonwertowa� zainstalowane w systemie fonty za pomoc�
**darmowego**, **wieloplatformowego** programu Fontforge_.
Wynikowe pliki musz� trafi� do katalogu ``fonts`` (lub jego
podkatalogu).


Fontforge potrafi odczyta� wi�kszo�� font�w wektorowych, w TeX-u
przewa�nie b�d� to formaty ``PFB`` lub ``PFA``.  Gdyby takowych
plik�w nie by�o, to je�li tylko zainstalowane s� narz�dzia
autotrace_ lub potrace_ odczyta� tak�e fonty MetaFontowe.

Przy generowaniu pliku (**Generate font...**) nale�y upewni� si�,
�e nie s� zmieniane nazwy znak�w (ustawione **No Rename**).

.. _autotrace:	http://autotrace.sourceforge.net
.. _potrace:	http://potrace.sourceforge.net


Je�li u�ywasz innego programu upewnij si�, �e glify w wynikowym pliku
SVG maj� nazw� (atrybut ``name``) oraz �cie�k� (atrybut ``d``).  Je�li
nie ma �cie�ki bezpo�rednio w tagu ``<glyhp>`` powinien istnie� potomny
w�ze� o nazwie ``<path>`` z atrybutem ``d``.  Plik SVG musi mie�
mniej wi�cej tak� struktur�::

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

(Je�li b�dzie taka potrzeba mog� rzecz jasna rozszerzy� akceptowane
struktury SVG, po prostu do tej pory nie spotka�em si� z innymi).

Dostaj� komunikat ``missing char``
::::::::::::::::::::::::::::::::::

Oznacza to zazwyczaj, �e wybrane jest niew�a�ciwe kodowanie dla danego
fontu.  Nale�y spr�bowa� poda� kodowanie z linii polece� opcj�
``--enc``.

Je�li po ponownym uruchomieniu znikn� te komunikaty, to znaczy, �e
wybrali�my dobre kodowanie i w�wczas mo�na na sta�e zmieni� wpis w pliku
``enc/file.info``. Pojedynczy wiersz ma format::

	nazwa_fontu        nazwa_kodowania        designsize

powinno to wygl�da� np. tak::

	pltt12             pltt                   12.000000


Program ``pydvi2svg`` je�li tylko mo�e zagl�da do plik�w TFM i odczytuje
stamt�d nazw� kodowania (pr�buje tak�e pliki AFM, ale to nie jest dobrze
przetestowane).  Jednak je�li konwersja do formatu SVG zosta�a wykonana
z formatu np. PFB to kodowanie w tym pliku mo�e si� r�ni�.

Np. dla fontu ``pltt12`` (przekonwertowane z pliku PFB) program odczyta
z TFM-a kodowanie "TeX typewriter text", czyli ``texnansi``. Ale je�li
zagl�dniemy do jakiego� pliku map, oka�e si�, �e plik ``pltt12.pfb``
jest przekodowywany przez ``pltt.enc`` (czyli kodowanie powinno by� jak
w powy�szym przyk�adzie --- ``pltt``).

Podobnie fonty CM mog� mie� inne kodowanie, u mnie jest to OT1.


Dostaj� b��d ``Unknown TeX/AFM encoding``
:::::::::::::::::::::::::::::::::::::::::

Nale�y stwierdzi� jakiemu plikowi ``*.enc`` z katalogu ``enc`` lub
instalacji TeX-a jest przyporz�dkowane dane kodowanie i uzupe�ni�
wpis w pliku ``enc/enc.info``.  Oraz koniecznie mnie o tym powiadomi�.


Znane problemy
~~~~~~~~~~~~~~

To jest problem Inkscape_, ale poniewa� odkry�em go podczas edycji
plik�w wygenerowanych przez ``pldvi2svg`` wi�c ostrzegam.

W Inkscape 0.44.1 z locales ``LC_ALL=pl_PL`` przy przesuwaniu strony
niekt�re litery mog� sta� si� ogromne (program gubi informacje o
przekszta�ceniach); zmiana locales na ``LC_ALL=C`` rozwi�zuje problem.


Licencja
~~~~~~~~

* **Licencja programu** --- BSD_.
* Licencja font�w --- taka sama jak �r�d�owych, tzn. tych rozprowadzanych
  w dystrybucjach TeX-a.  Udost�pniam je tutaj w innym formacie jedynie dla
  wygody PT U�ytkownik�w.


Uwagi, wnioski, poprawki
~~~~~~~~~~~~~~~~~~~~~~~~

Uprzejmie prosz� wszelkie uwagi, wnioski, poprawki, pytania itd.
kierowa� do autora:

	Wojciech Mu�a, wojciech_mula@poczta.onet.pl

..
	vim: tw=72 ts=4 sw=4 noexpandtab

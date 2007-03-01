#!/bin/sh

#tar -cjf fonts.tar.bz2 fonts/cm
cd ..
tar --exclude=pydvi2svg/path_element.py -cjf pydvi2svg/pydvi2svg.tar.bz2 pydvi2svg/*.py pydvi2svg/enc pydvi2svg/cache

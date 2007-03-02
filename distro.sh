#!/bin/sh

d=pydvi2svg
cd ..
tar --exclude=$d/path_element.py --exclude=$d/enc/CVS -cjf $d/$d.tar.bz2 $d/*.py $d/enc $d/cache
tar -cjf $d/fonts.tar.bz2 $d/fonts/cm/*
tar --exclude=$d/path_element.py --exclude=$d/enc/CVS -cjf $d/$d-full.tar.bz2 $d/*.py $d/enc $d/cache $d/fonts/cm/*

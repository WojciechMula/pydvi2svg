#!/bin/sh

d=pydvi2svg
cd ..
tar --exclude=$d/enc/CVS --exclude=$d/cache/* -cjf $d/$d.tar.bz2 $d/*.py $d/enc $d/cache $d/conv/*.py $d/frags/*.py
#tar -cjf $d/fonts.tar.bz2 $d/fonts/cm/*
#tar --exclude=$d/enc/CVS --exclude=$d/cache/* -cjf $d/$d-full.tar.bz2 $d/*.py $d/enc $d/cache $d/fonts/cm/*

# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.5.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

from ipstartup import *
from pymapbox import Twomaps
from pymapbox.elections import clean, get, show

const, constcentres = clean.general()

year1 = 2011
wards, wardcentres = clean.local(year1)
m1 = show.get_map(wards, wardcentres, const, constcentres)

year2 = 2015
wards, wardcentres = clean.local(year2)
m2 = show.get_map(wards, wardcentres, const, constcentres)

m1.title = f"Libdem%winner for local elections {year2} (left of slider is {year1})"
s = Twomaps(m1, m2, "slider")
s

s.save("localld_slider2015")

A("hhh").xml()

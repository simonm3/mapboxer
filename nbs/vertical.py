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
from pymapbox.elections import get, clean, show
from pymapbox import Twomaps

const, constcentres = clean.ge(2010)

year1 = 2011
wards, wardcentres = clean.local(year1)
m1 = show.get_map(wards, wardcentres, const, constcentres, "party")

year2 = 2015
wards, wardcentres = clean.local(year2)
m2 = show.get_map(wards, wardcentres, const, constcentres, "party")
m1.title = f"Local election {year2} (left of slider is {year1})"

m1.title = f"Local election top is {year1}, bottom is {year2})"
s = Twomaps(m1, m2, "vertical")
s

s.save("local_vertical")


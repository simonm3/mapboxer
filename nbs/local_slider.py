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
import geopandas as gpd
import plotly.express as px
from mapboxer.elections import get, clean, show
from mapboxer.utils import iframe
from mapboxer import Twomaps

const, constcentres = clean.ge(2010)

year1=2011
wards, wardcentres = clean.local(year1)
m1 = show.get_map(wards[:50], wardcentres[:50], const[:50], constcentres[:50], "party")

year2=2015
wards, wardcentres = clean.local(year2)
m2 = show.get_map(wards[:50], wardcentres[:50], const[:50], constcentres[:50], "party")

m1.title = f"Local elections {year2} (left of slider is {year1})"
s = Twomaps(m1, m2, "slider")
iframe(s.html())

s.save("local_slider2015")



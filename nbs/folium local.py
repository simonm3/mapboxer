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

const, constcentres = clean.ge(2010)

year = 2017
wards, wardcentres = clean.local(year)

import folium
m = folium.Map(location= [52.1917, -1.7083], zoom_start=12)
m.zoom_start=12
m

m = show.get_fol(wards, wardcentres, const, constcentres, "party")
m.title = f"Local election {year}"
m

m.save(f"folium{year}.html")

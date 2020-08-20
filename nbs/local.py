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
m = show.get_map(wards, wardcentres, const, constcentres, "party")
m.title = f"Local election {year}"
iframe(m.html())

m.save(f"local{year}.html")

for year in tqdm(range(2011, 2020)):
    wards, wardcentres = clean.local(year)
    m = show.get_map(wards, wardcentres, const, constcentres, "party")
    m.title = f"Local election {year}"
    m.save(f"local{year}.html")



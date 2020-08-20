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
from mapboxer import Map
from mapboxer.elections import get
from mapboxer.utils import replace_quotes, iframe, points2border

# get voter data
voters = pd.read_csv("../data/voters.csv")
border = voters = voters[voters.longitude.notnull() & voters.latitude.notnull()]
voters = voters.rename(columns=dict(localauthorityname="authority", pollingdistrictname="pd", longitude="lon", latitude="lat"))
replace_quotes(voters)
voters = gpd.GeoDataFrame(voters, geometry=gpd.points_from_xy(voters.lon, voters.lat))

# get borders
pds = points2border(voters, ["authority", "wardname", "pd"])

# clip to constituency
constituencies = get.constituencies()
constituencies = constituencies[constituencies.const=="West Dorset"]
border = constituencies.dissolve("const")
pds = gpd.clip(pds, border).reset_index()

# derived data and minimise
wards = pds.dissolve(by=["authority", "wardname"])[["geometry"]]
pds_c = pds.copy()[["pd", "geometry"]]
pds_c.geometry = pds_c.centroid
pds = pds[["geometry"]]

# # map

# +
m = Map()
m.center = [-2.58, 50.7977]
m.zoom = 10

m.add_source("wards", wards)
m.add_source("pds", pds)
m.add_source("pds_c", pds_c)

m.add_layer("wards", type="line", source="wards", paint=dict(line_width=3))
m.add_layer("Polling_district", type="line", source="pds")
m.add_layer("PD_names", type="symbol", source="pds_c", property="pd")
m.add_layer_selector()
m.title = "Polling district and ward boundaries generated from a list of geocoded voters"
iframe(m.html())
# -

m.save("pollingdistricts")



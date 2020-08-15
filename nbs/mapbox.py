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
from mapboxer.map import *

# # uk districts

# +
# job
job = pd.read_excel("../../registr/metadata/job.xlsx")
job = job[~job.jobtype.isin(["dev", "invalid"])]
job = job.groupby("authority").sum().reset_index()[["authority", "names"]]

# borders
borders = gpd.read_file(
    r"../..\registr\metadata\Local_Authority_Districts__December_2017__Boundaries_in_Great_Britain-shp\Local_Authority_Districts__December_2017__Boundaries_in_Great_Britain.shp"
)
# for 200 creates map in 3 seconds versus 1'30. likely loads faster too.
borders.geometry = borders.geometry.simplify(1000)
borders.geometry = borders.geometry.to_crs(epsg=4326)
borders = borders.rename(columns=dict(lad17nm="authority"))
borders.authority = borders.authority.str.replace("'", "")

# merged
df = borders.merge(job, on="authority", how="left")
df.loc[df.names > 0, "registr"] = "user"
df.registr = df.registr.fillna("non-user")

# centroids for text labels
df_c = df.copy()
df_c.geometry = df_c.geometry.centroid
# -

m.sourcesdf["ukdistricts"]["data"].dtypes

# +
m = UKMap()

# data sources
m.addSource("ukdistricts", df)
m.addSource("centroids", df_c)

# layers
m.addLayer("shading", type="fill", source="ukdistricts", property="names")
m.addLayer("border", type="line", source="ukdistricts")
m.addLayer("names", type="symbol", source="centroids", property="authority")

# non-mapbox features
m.title = f"Registr usage up to July 2020"
m.iframe()
# -

m.layers

print(m.html())

with open("map2.html", "w") as f:
    f.write(m.html())

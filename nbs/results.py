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
from mapboxer.elections import get

# # get data

allres = []
for year in range(2010, 2016):
    allres.append(get.res_local(year))
allres = pd.concat(allres)
allres.head()

# # tables

df = allres.copy()
df.loc[~df.party.isin(["C", "LD", "UKIP", "Lab", "Grn"]), "party"] = "other"
cands = pd.crosstab(df.party, df.year, df.wardname, aggfunc="count")
cands["total"] = cands.sum(axis=1)
d("candidates")
cands.style.format("{:,}")

missing = cands.max(axis=0)-cands
d("missing candidates")
missing.style.format("{:,}")

d("missing candidates%")
(missing/cands.max(axis=0)).style.format("{:.0%}")

votes = pd.crosstab(df.party, df.year, df.votes, aggfunc="sum")
votes["total"] = votes.sum(axis=1)
d("vote share")
(votes/votes.sum(axis=0)).style.format("{:.0%}")

d("votes/candidate")
(votes/cands).style.format("{:,.0f}")

df[(df.year==2010) & (df.party=="LD")]

df[(df.year==2015) & (df.party=="LD")] # 4300

# # ratio

# ratio by year
df = allres.copy()
df = pd.crosstab(
    [df.authority, df.wardname, df.year], df.party, df.votes, aggfunc="sum"
).reset_index()
df.columns.name = ""
df = df.fillna(0)
df["ratio"] = df.LD / df.drop(["LD", "year"], axis=1).max(axis=1)
df.ratio = df.ratio * 100

# by year
byyear = pd.crosstab([df.authority, df.wardname], df.year, df.ratio, aggfunc="first").reset_index()
byyear[byyear.authority=="Stratford-on-Avon"]

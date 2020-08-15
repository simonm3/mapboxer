""" add calculated columns; merge geometry and data """

import logging

import geopandas as gpd
import pandas as pd

from ..utils import fuzzymerge
from . import get

log = logging.getLogger(__name__)


def general():
    const = get.constituencies()
    const.geometry = const.geometry.simplify(0.001)
    res_ge = get.ge()

    # cleanup res_ge names (not from ONS; no code; names changed)
    matches = [
        ("South East Cambridgeshire", "Cambridgeshire South East"),
        ("North West Norfolk", "Norfolk North West"),
        ("North West Durham", "Durham North West"),
        ("South West Norfolk", "Norfolk South West"),
        ("North East Hampshire", "Hampshire East"),
        ("North East Somerset", "Somerset North East"),
    ]
    for a, b in matches:
        res_ge.loc[res_ge.const == b, "const"] = a

    # merge (fuzzy)
    const = fuzzymerge(const, res_ge, "const")
    const = const[const.fuzzyscore >= 90]
    const = const[["ratio", "geometry"]]

    # centroids
    constcentres = const.copy()
    constcentres.geometry = constcentres.centroid

    return const, constcentres


def local(year):
    wards = get.wards(year)
    # wards.geometry = borders.geometry.simplify(.003)
    del wards["year"]

    local = get.local(year)
    del local["year"]

    # calculate ratio
    df = local.copy()
    df = pd.crosstab(
        [df.authority, df.wardname], df.party, df.votes, aggfunc="sum"
    ).reset_index()
    df.columns.name = ""
    df = df.fillna(0)
    df["ratio"] = df.LD / df.drop("LD", axis=1).max(axis=1)
    df.ratio = df.ratio * 100
    df = df[["authority", "wardname", "ratio"]]

    # calculate winner and merge
    local = local.sort_values("votes", ascending=False)
    local = local.drop_duplicates(["authority", "wardname"])
    local.loc[~local.party.isin(["C", "LD", "UKIP", "Lab", "Grn"]), "party"] = "Other"
    local = local.merge(df, how="left").reset_index(drop=True)

    # merge borders
    wards = wards.merge(local, on=["authority", "wardname"], how="left",)

    # centroids
    wardcentres = wards.copy()
    wardcentres.geometry = wardcentres.geometry.centroid
    return wards, wardcentres

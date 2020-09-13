""" add calculated columns; merge geometry and data """

import logging

import geopandas as gpd
import pandas as pd

from ..utils import fuzzymerge
from . import get

log = logging.getLogger(__name__)


def ge(year):
    const = get.constituencies()
    const.geometry = const.geometry.simplify(0.001)
    res_ge = get.ge(year)

    # convert to ONS constituency names (ONS : electoral calculus)
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
    const = fuzzymerge(const, res_ge, "const", 90)
    const = const[["ratio", "geometry"]]

    # centroids
    constcentres = const.copy()
    constcentres.geometry = constcentres.centroid

    return const, constcentres


def local(year):
    wards = get.wards(year)
    # wards.geometry = borders.geometry.simplify(.003)

    local = get.local(year)
    del local["year"]

    # calculate ratio
    df = local.copy()
    df = pd.crosstab(df.wardcode, df.party, df.votes, aggfunc="sum").reset_index()
    df.columns.name = ""
    df = df.fillna(0)
    df["ratio"] = df.LD / df.drop("LD", axis=1).max(axis=1)
    df.ratio = df.ratio * 100
    df = df[["wardcode", "ratio"]]

    # calculate winner and merge
    local = local.sort_values("votes", ascending=False).drop_duplicates("wardcode")
    local.loc[local.party.isin(["SNP", "PC"]), "party"] = "NAT"
    local.loc[
        ~local.party.isin(["C", "LD", "UKIP", "Lab", "Grn", "NAT"]), "party"
    ] = "Other"
    local = local.merge(df, how="left").reset_index(drop=True)

    # merge borders
    wards = wards[["wardcode", "wardname", "geometry"]].merge(
        local.drop("wardname", axis=1), on=["wardcode"], how="left"
    )

    # centroids
    wardcentres = wards.copy()
    wardcentres.geometry = wardcentres.geometry.centroid
    return wards, wardcentres

""" load raw data into common column names and formats """

import logging
import re

import geopandas as gpd
import pandas as pd

from ..utils import replace_quotes

log = logging.getLogger(__name__)


## geography ##########################################################


def constituencies(year=2017):
    if year == 2010:
        df = gpd.read_file(
            "../data/boundaries/consituency-2010/westminster_const_region.shp"
        )
        df = df.rename(columns=dict(NAME="const"))
        df.const = df.const.apply(lambda x: re.sub(" Const$", "", x))
        df.const = df.const.apply(lambda x: re.sub(" Co$", "", x))
        df.const = df.const.apply(lambda x: re.sub(" Boro$", "", x))
        df.const = df.const.apply(lambda x: re.sub(" Burgh$", "", x))
    else:
        df = gpd.read_file(
            "../data/boundaries/Westminster_Parliamentary_Constituencies__December_2017__Boundaries_UK-shp/Westminster_Parliamentary_Constituencies__December_2017__Boundaries_UK.shp"
        )
        df = df.rename(columns=dict(pcon17nm="const"))
    replace_quotes(df)
    df.geometry = df.geometry.to_crs(epsg=4326)
    return df[["const", "geometry"]]


def districts(year):
    df = gpd.read_file(
        "../data/boundaries/Local_Authority_Districts__December_2015__Boundaries-shp\Local_Authority_Districts__December_2015__Boundaries.shp"
    )
    df = df.rename(columns=dict(lad15nm="authority"))
    df["year"] = year
    replace_quotes(df)
    df.geometry = df.geometry.to_crs(epsg=4326)
    return df[["authority", "year", "geometry"]]


def wards(year):
    if year <= 2014:
        df = gpd.read_file(
            "../data/boundaries/Wards__December_2011__Boundaries_EW_BGC-shp\Wards__December_2011__Boundaries_EW_BGC.shp"
        )
        lookup = pd.read_csv(
            "../data/boundaries/Ward_to_Census_Merged_Ward_to_Local_Authority_District__December_2011__Lookup_in_England_and_Wales.csv"
        )
        lookup.columns = [c.lower() for c in lookup.columns]
        df = df.merge(lookup[["wd11cd", "lad11nm"]], on="wd11cd")
        df = df.rename(columns=dict(wd11nm="wardname", lad11nm="authority"))
    elif year == 2015:
        df = gpd.read_file(
            "../data/boundaries/Wards__December_2015__Boundaries-shp\Wards__December_2015__Boundaries.shp"
        )
        df = df.rename(columns=dict(wd15nm="wardname", lad15nm="authority"))

    df["year"] = year
    replace_quotes(df)
    df.geometry = df.geometry.to_crs(epsg=4326)
    return df[["authority", "wardname", "year", "geometry"]]


## results#############################################################################


def ge():
    """ gets results and matches against constituency file
    year=2010 as ot changed until 2021?
    """
    # electoralcalculus
    df = pd.read_excel("../data/pivottablefull.xlsx", sheet_name="data")
    df = df[df.Year == 2010]
    df = pd.crosstab(df.Constituency, df.Party, df.Vote, aggfunc="sum")
    df = df.reset_index().rename(columns=dict(Constituency="const"))
    df["ratio"] = df.LIB / df.drop(columns="LIB").max(axis=1) * 100
    df.ratio = df.ratio.fillna(0).astype(int)

    return df.reset_index()[["const", "ratio"]]


def local(year):
    if year == 2010:
        names = ["authority", "wardname", "person", "party", "votes", "elected"]
        header = None
    elif year >= 2011 and year <= 2014:
        names = ["wardname", "authority", "person", "party", "votes", "elected"]
        header = 0
    elif year >= 2015:
        names = [
            "authority",
            "ons",
            "wardname",
            "ons2",
            "person",
            "party",
            "votes",
            "elected",
        ]
        header = 0

    df = pd.read_csv(
        f"../data/local/{year}_results.csv", header=header, index_col=False, names=names
    )
    df["year"] = year
    replace_quotes(df)
    return df[["authority", "wardname", "year", "party", "votes"]]

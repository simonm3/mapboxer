""" load raw data 
    
* common column names and formats
* 
"""

import logging
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

from ..utils import replace_quotes

log = logging.getLogger(__name__)

data = Path(__file__).parent.parent.parent / "data"


## geography ##########################################################


def constituencies(year=2017):
    """ boundaries unchanged 2010-2020 """
    path = data / "boundaries"
    df = gpd.read_file(
        path
        / "Westminster_Parliamentary_Constituencies__December_2017__Boundaries_UK-shp/Westminster_Parliamentary_Constituencies__December_2017__Boundaries_UK.shp"
    )
    df = df.rename(columns=dict(pcon17nm="const"))
    replace_quotes(df)
    df.geometry = df.geometry.to_crs(epsg=4326)
    return df[["const", "geometry"]]


def districts(year):
    path = data / "boundaries"
    f = "Local_Authority_Districts__December_2015__Boundaries-shp/Local_Authority_Districts__December_2015__Boundaries.shp"
    df = gpd.read_file(path / f)
    df = df.rename(columns=dict(lad15nm="authority"))
    df["year"] = year
    replace_quotes(df)
    df.geometry = df.geometry.to_crs(epsg=4326)
    return df[["authority", "year", "geometry"]]


def wards(year):
    path = data / "boundaries"
    if (year <= 2010) or (year in [2012, 2013, 2014]):
        log.warning(f"using 2011 boundary as {year} not available")
        year = 2011
    elif year >= 2020:
        log.warning(f"using 2019 boundary as {year} not available")
        year = 2019

    if year == 2011:
        f = "Wards__December_2011__Boundaries_EW_BGC-shp/Wards__December_2011__Boundaries_EW_BGC.shp"
    elif year == 2015:
        f = "Wards__December_2015__Boundaries-shp/Wards__December_2015__Boundaries.shp"
    elif year == 2016:
        f = "Wards__December_2016__Boundaries-shp/Wards__December_2016__Boundaries.shp"
    elif year == 2017:
        f = "Wards__December_2017__Boundaries_in_the_UK__WGS84_-shp"
    elif year == 2018:
        f = "Wards__December_2018__Boundaries_UK-shp/Wards__December_2018__Boundaries_UK.shp"
    elif year == 2019:
        f = "Wards__December_2019__Boundaries_UK_BGC-shp/Wards__December_2019__Boundaries_UK_BGC.shp"

    y2 = str(year)[-2:]
    df = gpd.read_file(path / f)
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns={f"wd{y2}nm": "wardname", f"wd{y2}cd": "wardcode"})
    replace_quotes(df)
    df.geometry = df.geometry.to_crs(epsg=4326)
    return df[["wardcode", "wardname", "geometry"]]


## results#############################################################################


def ge(year):
    """ ge results 1995-2019 from electoralcalculus """
    df = pd.read_excel(data / "ge/pivottablefull.xlsx", sheet_name="data")
    df = df[df.Year == year]
    df = pd.crosstab(df.Constituency, df.Party, df.Vote, aggfunc="sum")
    df = df.reset_index().rename(columns=dict(Constituency="const"))
    df["ratio"] = df.LIB / df.drop(columns="LIB").max(axis=1) * 100
    df.ratio = df.ratio.fillna(0).astype(int)

    return df.reset_index()[["const", "ratio"]]


def local(year):
    """ 2010-2019 from andrew teale """
    path = data / "local"
    params = dict()

    if year == 2010:
        names = ["authority", "wardname", "person", "party", "votes", "elected"]
    elif year >= 2011 and year <= 2014:
        names = ["wardname", "authority", "person", "party", "votes", "elected"]
        params = dict(skiprows=1)
    elif year >= 2015:
        names = [
            "authority",
            "authcode",
            "wardname",
            "wardcode",
            "person",
            "party",
            "votes",
            "elected",
        ]
        params = dict(skiprows=1)

    if year <= 2015:
        f = f"{year}_results.csv"
    elif year == 2016:
        f = "leap-2016-05-05.csv"
    elif year == 2017:
        f = "leap-2017-05-04.csv"
    elif year == 2018:
        f = "leap-2018-05-03-partial.csv"
    elif year == 2019:
        f = "leap-2019-05-02-partial.csv"
        params = dict(skiprows=1)

    df = pd.read_csv(path / f, index_col=False, names=names, **params)
    df = df.rename(columns=dict(wd11nm="wardname", lad11nm="authority"))
    df["year"] = year
    replace_quotes(df)

    # lookup wardcode
    if year <= 2014:
        f = (
            data
            / "boundaries/Ward_to_Census_Merged_Ward_to_Local_Authority_District__December_2011__Lookup_in_England_and_Wales.csv"
        )
        lookup = pd.read_csv(f)
        lookup.columns = [c.lower() for c in lookup.columns]
        lookup = lookup.rename(
            columns=dict(wd11nm="wardname", lad11nm="authority", wd11cd="wardcode")
        )
        df = df.merge(lookup, on=["authority", "wardname"], how="left")

    # wardcode unique whereas wardname is not (e.g. Abbey is very common)
    return df[["authority", "wardcode", "wardname", "year", "party", "votes"]]

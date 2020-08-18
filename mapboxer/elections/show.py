""" define maps """

import logging

import pandas as pd

from mapboxer.map import Map

from . import get

log = logging.getLogger(__name__)


def get_ratio_stopslabels(df):
    """ return stops and labels """

    # stops= no candidate, won
    active = df[df.ratio.between(0, 100, inclusive=False)]
    df["cats"], bins = pd.cut(
        active.ratio.astype(int), bins=[0, 33, 66, 100], labels=False, retbins=True,
    )
    df.cats += 1
    df.loc[df.ratio == 0, "cats"] = 0
    df.loc[df.ratio >= 100, "cats"] = 100
    df.cats = df.cats.fillna(-9999)

    # stops are category strings [0, 1,2,3]; bins are values [0, 15, 33]
    stops = [str(int(x)) for x in df.cats.sort_values().unique()]
    binlabels = [f"{int(s)}-{int(bins[i+1])}%" for i, s in enumerate(bins[:-1])]
    labels = ["no election", "no libdem"] + binlabels + ["won"]
    # convert to force discrete categories
    df.cats = df.cats.astype(int).astype(str)
    return stops, labels


def get_map(wards, wardcentres, const, constcentres, shading="ratio"):
    """ configure map with ward and constituency boundaries.

    :param shading: data column to use for shading. "ratio" or "party". 
    :return: mapbox map

    Alternative shading requires configuration::
    
        labels in order required for legend
        colorset tailored to categories
        stops None for categorical. see get_shading for qcut or cut.
    """
    m = Map()
    m.center = [-1.7083, 52.1917]
    m.zoom = 10

    if shading == "ratio":
        stops, labels = get_ratio_stopslabels(wards)
        # grey, yellow, [blue, green*2], libdem
        colorset = ["#dddddd", "#ffeb99", "#d3f6f3", "#a7e9af", "#75b79e", "#FAA61A"]
    elif shading == "party":
        labels = ["no election", "C", "Lab", "LD", "UKIP", "Grn", "NAT", "Other"]
        stops = labels
        colorset = [
            "#dddddd",
            "#00aeef",
            "#DC241f",
            "#FAA61A",
            "#470A65",
            "#6AB023",
            "#fdf38e",
            "gray",
        ]
        wards["cats"] = wards.party
        wards.cats = wards.cats.fillna("no election")
    else:
        raise Exception("shading must be party or ratio")

    # select columns only to reduce data on page
    wards = wards[["cats", "geometry"]]
    wardcentres = wardcentres[["wardname", "geometry"]]

    # data sources
    m.add_source("wards", wards)
    m.add_source("wardcentres", wardcentres)
    m.add_source("const", const)
    m.add_source("constcentres", constcentres)

    # layers
    m.add_layer(
        "shading",
        type="fill",
        source="wards",
        property="cats",
        stops=stops,
        labels=labels,
        colorset=colorset,
    )
    m.add_layer("wards", type="line", source="wards")
    m.add_layer("wardnames", type="symbol", source="wardcentres", property="wardname")
    m.add_layer("constituencies", type="line", source="const", paint=dict(line_width=3))
    m.add_layer(
        "GE2010_pcwin",
        type="symbol",
        source="constcentres",
        property="ratio",
        layout=dict(text_size=40),
    )

    # non-mapbox features
    m.add_layer_selector()

    return m

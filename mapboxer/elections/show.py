""" define maps """

import logging
from os.path import expanduser

import pandas as pd
import yaml

from mapboxer.map import Map

from . import get

log = logging.getLogger(__name__)


def get_map(wards, wardcentres, const, constcentres, x="ratio"):
    """
    map with ward and constituency boundaries; ward names; consituency results 2010; shading of party/ldratio

    :param x: data column "ratio" or "party". 
    :return: mapbox map
    """
    m = Map()
    m.center = [-1.7083, 52.1917]
    m.zoom = 10
    m.style = "mapbox://styles/mapbox/streets-v11"
    m.api = yaml.safe_load(open(expanduser("~") + "/.mapbox/creds.yaml"))

    x, cats, colorset, wards = get_cats(x, wards)

    # source shared by 2 layers
    m.add_source("wards", wards[["geometry", x]])

    # layers
    m.add_layer(
        "shading", type="fill", source="wards", x=x, cats=cats, colorset=colorset,
    )
    m.add_layer("constituencies", type="line", source=const, paint=dict(line_width=3))
    m.add_layer("wards", type="line", source="wards")
    m.add_layer("wardnames", type="symbol", source=wardcentres, x="wardname")
    m.add_layer(
        "GE2010_pcwin",
        type="symbol",
        source=constcentres,
        x="ratio",
        layout=dict(text_size=40),
    )

    return m


def get_ipy(wards, wardcentres, const, constcentres, x="ratio"):
    from ipyleaflet import Map, Marker, GeoJSON, basemaps, GeoData, LayersControl
    from mapboxer.utils import geojson

    m = Map()
    m.center = [52.1917, -1.7083]
    m.zoom = 10
    m.scroll_wheel_zoom = True

    x, cats, colorset, wards = get_cats(x, wards)

    # create style columns
    wards["fillcolor"] = wards[x].map(dict(zip(cats, colorset)))
    wards = wards[["geometry", "wardname", "fillcolor"]]
    wardcentres = wardcentres[["wardname", "geometry"]]

    def wardstyle(row):
        return dict(fillColor=row["properties"]["fillcolor"], fillOpacity=1)

    layer = GeoJSON(
        name="constituencies",
        data=geojson(const),
        style=dict(fillColor="#00000000", weight=3),
    )
    m.add_layer(layer)

    layer = GeoJSON(
        name="wards",
        data=geojson(wards),
        style_callback=wardstyle,
        style=dict(weight=1),
    )
    m.add_layer(layer)

    m.add_control(LayersControl())

    return m


def get_fol(wards, wardcentres, const, constcentres, x="ratio"):
    """
    folium map with ward and constituency boundaries; ward names; consituency results 2010; shading of party/ldratio

    :param shading: data column to use for shading. "ratio" or "party". 
    :return: mapbox map
    """
    import yaml
    from os.path import expanduser
    import folium as f

    m = f.Map(location=[52.1917, -1.7083], zoom_start=12,)
    # m.tiles = "Mapbox"
    # m.API_key = yaml.safe_load(open(expanduser("~") + "/.mapbox/creds.yaml"))

    x, cats, colorset, wards = get_cats(x, wards)

    # create style columns
    wards["fillcolor"] = wards[x].map(dict(zip(cats, colorset)))
    wards = wards[["geometry", "wardname", "fillcolor"]]
    wardcentres = wardcentres[["wardname", "geometry"]]

    def wardstyle(row):
        return dict(fillColor=row["properties"]["fillcolor"], fillOpacity=1)

    f.GeoJson(
        const, name="constituencies", style_function=lambda x: dict(weight=3),
    ).add_to(m)

    f.GeoJson(wards, name="wards", style_function=wardstyle,).add_to(m)
    f.LayerControl().add_to(m)

    return m


def get_cats(x, wards):
    """ prepare category, color data """
    if x == "ratio":
        # bespoke cats to split wards with a libdem candidate
        x = "cats"
        active = wards[wards.ratio.between(0, 100, inclusive=False)]
        cats = ["0-33%", "33-66%", "66-100%"]
        wards["cats"] = pd.cut(
            active.ratio.astype(int), bins=[0, 33, 66, 100], labels=cats
        ).astype(str)
        wards.loc[wards.ratio == 0, "cats"] = "no libdem"
        wards.loc[wards.ratio >= 100, "cats"] = "won"
        wards.cats = wards.cats.fillna("no election")

        # legend and colors
        cats = ["no election", "no libdem"] + cats + ["won"]
        # grey, yellow, [blue, green*2], libdem
        colorset = ["#dddddd", "#ffeb99", "#d3f6f3", "#a7e9af", "#75b79e", "#FAA61A"]
    elif x == "party":
        # legend and colors
        cats = ["no election", "C", "Lab", "LD", "UKIP", "Grn", "NAT", "Other"]
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
        wards.party = wards.party.fillna("no election")
    else:
        raise Exception("shading must be party or ratio")

    return x, cats, colorset, wards

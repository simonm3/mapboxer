import json
import logging
import os
from os.path import expanduser
from pathlib import Path

import geopandas
import pandas as pd
import plotly.express as px
import yaml
import yatl
from colour import Color
from IPython.display import HTML
from yatl import DIV, INPUT, LABEL, SPAN, XML

from .dotdict import autodict, dotdict
from .utils import change_keys, geojson, tempdir

log = logging.getLogger(__name__)

token = yaml.safe_load(open(expanduser("~") + "/.mapbox/creds.yaml"))


class Map:
    """ mapbox map """

    # root parameters passed to mapboxgl.map. openstreetmap centred on UK.
    container = "map"
    style = "mapbox://styles/mapbox/streets-v11"
    center = [-1.5, 53]
    zoom = 5

    def __init__(self):
        pre_init = self.__dict__.copy()

        # format
        self.layers = []

        # data
        self.sources = dict()

        # extra to mapbox
        self.colorset = px.colors.qualitative.Set3
        self.grayscale = lambda stops: [
            c.hex for c in Color("white").range_to(Color("black"), stops)
        ]
        self.legends = ""
        self.layer_selector = ""
        self.sourcesdf = dict()
        self.title = ""
        self.map2 = None

        # variables declared in init are not part of root
        self.excluded = None
        self.excluded = set(self.__dict__) - set(pre_init)

    # input #######################################################

    def add_source(self, id=None, data=None, **kwargs):
        """ add a data source. store raw dataframe and geojson
        :param id: name of source that layers can use to identify
        :param data: geodataframe
        :param kwargs: any mapbox layer parameters in addition to the above
        """
        # raw dataframe
        kwargs["data"] = data
        kwargs.setdefault("type", "geojson")
        self.sourcesdf[id] = kwargs

        # converted to geojson
        s = kwargs.copy()
        s["data"] = geojson(s["data"])
        self.sources[id] = json.dumps(change_keys(s))

    def add_layer(self, id=None, **kwargs):
        """ add a layer to the map with defaults for text_color, text_size, fill colors, legend
        :param id: name of layer used in layerselector
        :param property: source data column name
        :param colorset: list of colors to use for shading. defaults to Set3.
        :param stops: break points. int for quantiles; list for cuts or categories
        :param labels: text for legend; default is category OR <value
        :param method: set to "interpolate" for linear change over range (only relevant for continuous scale)
        :param kwargs: any mapbox layer parameters in addition to the above
        """
        dd = autodict(kwargs)
        dd.id = id
        dd.legend = []
        df = self.sourcesdf[kwargs["source"]]["data"]

        # defaults for symbol/text
        if dd.type == "symbol":
            dd.paint.setdefault("text_color", "#2a3f5f")
            dd.layout.setdefault("text_field", ["get", dd.property])
            dd.layout.setdefault("text_size", 10)
        elif dd.type == "fill":
            self.add_layer_fill(dd, df)

        kwargs = change_keys(dd).to_dict()
        self.layers.append(kwargs)

    def add_layer_fill(self, dd, df):
        """ create json for fill layer """
        property_ = dd.property

        # categoric data
        if df[property_].dtype == "O":
            df["cats"] = df[property_]
            method = "match"
            stops = dd.get("stops", df.cats.unique())
            labels = dd.get("labels", stops)
        # numeric data
        else:

            # integer is qcut with default quartiles
            stops = dd.get("stops", 4)
            if isinstance(stops, int):
                df["cats"] = pd.qcut(df[df[property_].notnull()][property_], stops)

            # list uses cut which is inclusive i.e. stops=[min, q1,q2,q3, max]
            else:
                df["cats"] = pd.cut(df[dd.property], bins=stops)

            df.cats = df.cats[df.cats.notnull()].apply(lambda x: x.right)

            # must be integers to match steps
            df.cats = df.cats.astype(float).fillna(-9999).astype(int)

            # stops and labels
            stops = sorted(df.cats.unique())
            labels = dd.get("labels", ["none"] + [f"<{level}" for level in stops[1:]])

            # step or interpolated
            method = dd.get("method", "step")

        # colorset
        if method == "interpolated":
            colorset = dd.get("colorset", self.grayscale(len(stops)))
        else:
            colorset = dd.get("colorset", self.colorset)

        # paint
        # exact match
        if method == "match":
            dd.paint.fill_color = ["match", ["get", "cats"]]
            for stop in list(zip(stops, colorset)):
                dd.paint.fill_color.extend(stop)
            dd.paint.fill_color.append("white")
        # highest category below value
        elif method == "step":
            dd.paint.fill_color = ["step", ["get", "cats"], colorset[0]]
            for stop in list(zip(stops, colorset))[1:]:
                dd.paint.fill_color.extend(stop)
        # interpolated between two categories
        elif method == "interpolated":
            dd.paint.fill_color = ["interpolate", ["linear"], ["get", property_]]
            for stop in list(zip(stops, colorset)):
                dd.paint.fill_color.extend(stop)

        # legend
        dd.legend = list(zip(labels, colorset))

    def add_layer_selector(self):
        self.layer_selector = self.get_layer_selector()

    # output ###########################################################################

    def root(self):
        """ return dict of root variables including inherited """
        r = {
            k: getattr(self, k)
            for k in dir(self)
            if not (
                k in self.excluded or k.startswith("__") or callable(getattr(self, k))
            )
        }
        return r

    def html(self):
        """ return html page
        """
        with tempdir(Path(__file__).parent.parent / "templates"):
            html = open(f"../templates/map.html").read()
            self.legends = self.get_legends()

            return yatl.render(
                html, delimiters="[[ ]]", context=dict(token=token, map1=self),
            )

    def save(self, filename):
        """ save map as html """
        if not os.path.splitext(filename)[-1]:
            filename = filename + ".html"
        if not filename.find(os.sep) >= 0:
            filename = Path(__file__).parent.parent / "data/output" / filename
        with open(filename, "w", encoding="utf8") as f:
            f.write(self.html())

    def get_legends(self):
        """ return legends mapping labels to colors in first fill layer
        """
        legends = DIV()
        for layer in self.layers:
            if not "legend" in layer:
                continue
            legend = DIV(_id=f"{layer['id']}_legend")
            for label, color in layer["legend"]:
                entry = SPAN(_style="display:block; margin:5px")
                key = SPAN(
                    _style=f"background-color:{color}; padding-left: 10px; margin-right:10px"
                )
                entry.append(key)
                entry.append(SPAN(label))
                legend.append(entry)
            legends.append(legend)
        return legends

    def get_layer_selector(self):
        """ add layer selecter """
        fg = DIV(_class="filter-group")
        for layer in self.layers:
            fg.append(INPUT(_type="checkbox", _id=layer["id"], _checked=True))
            fg.append(LABEL(layer["id"], _for=layer["id"]))
        return fg

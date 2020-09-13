import json
import logging
import os
from functools import partial
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
    container = "map1"
    style = "mapbox://styles/mapbox/streets-v11"
    center = [-1.5, 53]
    zoom = 5

    def __init__(self):
        # variables declared in init are not part of root
        pre_init = self.__dict__.copy()

        # format
        self.layers = []

        # data
        self.sources = dict()

        # extra to mapbox
        # [square, triangle]
        self.shapeset = ["\u25a0", "\u25b2"]
        self.colorset = px.colors.qualitative.Set3
        self.grayscale = lambda cats: [
            c.hex for c in Color("white").range_to(Color("black"), cats)
        ]
        self.showlegends = True
        self.showtoggles = True
        self.legends = None
        self.toggles = None
        self.sourcesdf = dict()
        self.title = ""

        self.excluded = None
        self.excluded = set(self.__dict__) - set(pre_init)

    def _repr_html_(self):
        """ display in notebook as iframe """
        html = self.html().replace('"', "'")
        iframe = f'<iframe id="mapframe", srcdoc="{html}" style="border: 0" width="100%", height="500px"></iframe>'
        return iframe

    # input #######################################################

    def add_source(self, name=None, data=None, **kwargs):
        """ add a data source. store raw dataframe and geojson
        :param name: name of source
        :param data: geodataframe
        :param kwargs: any mapbox layer parameters in addition to the above

        only required when sharing source between layers
        normally easier to just pass source as parameter to add_layer.
        """
        # raw dataframe
        self.sourcesdf[name] = data

        # geojson
        kwargs.setdefault("type", "geojson")
        kwargs["data"] = geojson(data)
        self.sources[name] = json.dumps(kwargs)

    def add_layer(self, id=None, **kwargs):
        """ add a layer to the map
        * full mapbox style specification via kwargs
        * dotdict parameters with underscores converted to dashes e.g. paint.fill_color
        * additional parameters to simplify e.g. define categories/labels/colors from data or explicitly
        * defaults that can be overridden
        * accepts geopandas data
        * option to add legend and layer toggle

        Required:
        :param id: id of layer
        :param source: name of source or geodataframe
        :param x: first source column name

        Optional:
        :param cats: sequence for legend; string list=categories; numeric list=cuts; int=quantiles.
        :param colorset: list of colors to use for shading. defaults to Set3.
        :param labels: default is cats for categoric; "<value" for continuous
        :param method: "interpolate" for linear change over range (only relevant for continuous scale)
        :param y: second source column name
        :param ycats: cats for y axis
        :param visible: visibility of layer
        :param showlegend: False to not show legend. default True.
        :param showtoggle: False to not show toggle. default True.
        :param kwargs: any mapbox layer parameters in addition to the above

        Layer types as per mapbox style specification
        ---------------------------------------------
        symbol
            if y category
                color+shape points using font for shapes
            else
                text only by default. can add image using kwargs.
        fill
            categoric or interpolated colors
        circle
            color points with faster rendering than symbol images
        others (use kwargs)
            background, line, raster, fill-extrusion, heatmap, hillshade
        """
        dd = autodict(kwargs)
        dd.id = id
        dd.layout.visibility = "visible" if dd.pop("visible", True) else "none"

        # move source data to sources
        if not isinstance(dd.source, str):
            # minimise to required cols
            cols = ["geometry"]
            for col in ["x", "y"]:
                if col in dd:
                    cols.append(col)
            self.add_source(id, dd.source)
            dd.source = id

        # defaults for layers
        df = self.sourcesdf[dd.source]
        if dd.type == "symbol":
            if "y" in dd:
                self.add_layer_shape(dd, df)
            else:
                self.add_layer_symbol(dd, df)
        elif dd.type == "fill":
            self.add_layer_fill(dd, df)
        elif dd.type == "circle":
            self.add_layer_circle(dd, df)

        kwargs = change_keys(dd).to_dict()
        self.layers.append(kwargs)

    def add_layer_symbol(self, dd, df):
        """ create json for plain grey text with no icon """
        dd.paint.setdefault("text_color", "#2a3f5f")
        dd.layout.setdefault("text_field", ["get", dd.x])
        dd.layout.setdefault("text_size", 10)

    def add_layer_circle(self, dd, df):
        """ create json for circle/point layer """
        # data
        colorset = dd.get("colorset", self.colorset)
        cats = dd.get("cats", df[dd.x].unique())

        # paint
        dd.paint.circle_radius = dict(base=1.75, stops=[[12, 2], [22, 180]])
        dd.paint.circle_color = ["match", ["get", dd.x]]
        for cat in list(zip(cats, colorset)):
            dd.paint.circle_color.extend(cat)
        dd.paint.circle_color.append("white")

        # legend
        if dd.get("showlegend", True):
            labels = dd.get("labels", cats)
            dd.legend = list(zip(labels, colorset))

    def add_layer_fill(self, dd, df):
        """ create json for fill layer """
        x = df[dd.x]

        # categoric data
        if x.dtype == "O":
            method = "match"
            cats = dd.get("cats", x.unique())
            labels = dd.get("labels", cats)
        # numeric data
        else:
            # integer cats is qcut with default quartiles
            cats = dd.get("cats", 4)
            if isinstance(cats, int):
                cats = pd.qcut(x, cats, retbins=True)
            labels = dd.get("labels", [f"<{level}" for level in cats] + ["none"])

            # can be "interpolated"
            method = dd.get("method", "step")

        # colorset
        if "colorset" in dd:
            colorset = dd.colorset
        else:
            colorset = (
                self.grayscale(len(cats)) if method == "interpolated" else self.colorset
            )

        # paint
        # exact match
        if method == "match":
            dd.paint.fill_color = ["match", ["get", dd.x]]
            for cat in list(zip(cats, colorset)):
                dd.paint.fill_color.extend(cat)
            dd.paint.fill_color.append("white")
        # highest category below value
        elif method == "step":
            dd.paint.fill_color = ["step", ["get", dd.x, "white"]]
            for cat in list(zip(cats, colorset)):
                dd.paint.fill_color.extend(cat)
        # interpolated between two categories
        elif method == "interpolated":
            dd.paint.fill_color = ["interpolate", ["linear"], ["get", dd.x]]
            for cat in list(zip(cats, colorset)):
                dd.paint.fill_color.extend(cat)

        # legend
        if dd.get("showlegend", True):
            dd.legend = list(zip(labels, colorset))

    def add_layer_shape(self, dd, df):
        """ create json for points with shape*color. uses text with shape font """
        # data
        colorset = dd.get("colorset", self.colorset)
        shapeset = dd.get("shapeset", self.shapeset)
        cats = dd.get("cats", df[dd.x].unique())
        ycats = dd.get("ycats", df[dd.y].unique())

        # color
        dd.paint.text_color = ["match", ["get", dd.x]]
        for cat in list(zip(cats, colorset)):
            dd.paint.text_color.extend(cat)
        dd.paint.text_color.append("white")

        # shape
        dd.layout.text_allow_overlap = True
        dd.layout.setdefault("text_field", ["get", dd.y])
        dd.layout.text_field = ["match", ["get", dd.y]]
        for cat in list(zip(ycats, shapeset)):
            dd.layout.text_field.extend(cat)
        dd.layout.text_field.append("X")
        dd.layout.setdefault("text_size", 15)

        # legend
        if dd.get("showlegend", True):
            labels = dd.get("labels", cats)
            dd.legend = list(zip(labels, colorset)) + list(zip(ycats, shapeset))

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
            self.toggles = self.get_toggles()
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
            if not layer.get("showlegend", self.showlegends):
                continue
            if "legend" not in layer:
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

    def get_toggles(self):
        """ add buttons to toggle layers """
        fg = DIV(_class="filter-group")
        for layer in self.layers:
            if not layer.get("showtoggle", self.showtoggles):
                continue
            try:
                checked = layer["layout"]["visibility"] == "visible"
            except:
                checked = True
            fg.append(INPUT(_type="checkbox", _id=layer["id"], _checked=checked,))
            fg.append(LABEL(layer["id"], _for=layer["id"]))
        return fg

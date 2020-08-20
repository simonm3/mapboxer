import contextlib
import difflib
import json
import logging
import os
from io import BytesIO

import geopandas as gpd
import pandas as pd
from fuzzywuzzy import fuzz, process
from IPython.display import HTML
from scipy.spatial import Voronoi
from shapely.geometry import MultiPoint, Polygon

log = logging.getLogger(__name__)


def replace_quotes(df):
    """ remove single quotes from all str columns 
    quotes are an issue in json string such as "'name' : 'Jane's Cafe'"
    todo escape rather than replace?
    """
    for col in [c for c in df if df[c].dtype == object]:
        try:
            df[col] = df[col].str.replace("'", "")
        except:
            log.warning(f"cannot remove quotes from {col}")


@contextlib.contextmanager
def tempdir(path):
    """ change folder temporarily """
    saved = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(saved)


def geojson(gdf):
    """ return geojson from geodataframe
    includes geometry, crs, properties (from other columns)
    """
    f = BytesIO()
    gdf.to_file(f, driver="GeoJSON")

    return json.loads(f.getvalue())


def change_keys(obj, convert=None):
    """
    Recursively replace dict keys
    :param convert: function to convert keys. default replaces _ with -

    e.g. translates dict(text_color="black") to {"text-color":"black"} as required for mapbox
    """
    if convert is None:
        convert = lambda x: x.replace("_", "-")

    if isinstance(obj, dict):
        new = obj.__class__()
        for k, v in obj.items():
            new[convert(k)] = change_keys(v, convert)
        return new

    if isinstance(obj, (list, set, tuple)):
        new = obj.__class__(change_keys(v, convert) for v in obj)
        return new

    return obj


def fuzzymerge(df1, df2, key):
    """ merge df1 to best fit on df2

    :param key: column to merge on. must be in df1 and df2
    :return: merged dataframe sorted by fuzzyscore to enable checking lowest scores

    e.g. match area names on two data sources such as "Birmingham, West" and "West Birmingham"
    
    """
    df1 = df1.copy()
    df2 = df2.copy()

    # unmatched
    merged = df1.merge(df2[[key]], on=key, how="outer", indicator=True)
    unmatched1 = merged[merged._merge == "left_only"][key].tolist()
    unmatched2 = merged[merged._merge == "right_only"][key].tolist()

    # map the unmatched
    mapper = []
    for v in unmatched1:
        res = process.extractOne(v, unmatched2)
        if not res:
            res = (v, "no match", 0)
        mapper.append([v, *res])
        # faster but may cause errors
        # unmatched2.remove(res[0])
    mapper = pd.DataFrame(mapper, columns=[key, "fuzzykey", "fuzzyscore"])
    df1 = df1.merge(mapper, on=key, how="left")

    # matched
    matched = df1[key].isin(df2[key])
    df1.loc[matched, "fuzzykey"] = df1[key]
    df1.loc[matched, "fuzzyscore"] = 100

    # fuzzy match
    res = df1.merge(df2.rename(columns={key: "fuzzykey"}), on="fuzzykey", how="left")
    cols = [key, "fuzzykey", "fuzzyscore"]
    return res.sort_values("fuzzyscore")[cols + list(set(res.columns) - set(cols))]


def iframe(html):
    """ wrap html page in iframe
    """
    html = html.replace('"', "'")
    iframe = f'<iframe id="mapframe", srcdoc="{html}" style="border: 0" width="100%", height="500px"></iframe>'
    return HTML(iframe)


def get_voronoi(df):
    """ return df with geometry column set to voronoi region (boundary around each point)
    :param df: geodataframe of points
    :return: geodataframe of voronoi regions
    """
    df = df.copy()
    points = [(p.x, p.y) for p in df.geometry]
    # add 4 outer points to ensure all data has a region. otherwise voronoi region is undefined for outermost points.
    points.extend(
        list(MultiPoint(points).envelope.buffer(0.2).envelope.exterior.coords)[1:]
    )
    vor = Voronoi(points)
    df["geometry"] = [
        Polygon(vor.vertices[vor.regions[i]]) for i in vor.point_region[:-4]
    ]
    return df


def points2border(points, area_key):
    """ create area borders from a set of points
    :param points: geodataframe of points
    :param area_key: columns that identify the points in each area
    :return: geodataframe of area boundaries that are contiguous and non-overlapping

    Defines boundaries based on primary polygons excluding points in secondary polygons and polygon in polygon
    """
    # voronoi pass 1. output includes multipolygons and polygon in polygon.
    voronoi1 = get_voronoi(points)
    borders1 = voronoi1.dissolve(by=area_key)[["geometry"]]

    # reduce each area to primary polygon with most points
    polygons = borders1.reset_index().explode()
    df = gpd.tools.sjoin(polygons, points, op="contains", how="right")
    polygons["points"] = df.groupby(["index_left0", "index_left1"]).count().geometry
    polygons = polygons.sort_values("points", ascending=False).drop_duplicates(area_key)

    # reduce points to those in primary polygon. remove duplicates (polygon in polygon)
    df = gpd.tools.sjoin(polygons, points, op="contains", how="right")
    points2 = points.loc[
        df[(df.pd_x == df.pd_y) & ~df.index.duplicated(keep=False)].index
    ]

    # voronoi pass2 excluding outofarea points.
    voronoi2 = get_voronoi(points2)
    borders2 = voronoi2.dissolve(by=area_key)[["geometry"]]

    return borders2

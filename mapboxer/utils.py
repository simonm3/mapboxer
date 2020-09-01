import contextlib
import difflib
import json
import logging
import os
from functools import partial
from io import BytesIO
from multiprocessing import Pool
from time import sleep

import geopandas as gpd
import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz, process
from geopy.distance import geodesic
from scipy.spatial import Voronoi
from shapely.geometry import MultiPoint, Point, Polygon
from tqdm.auto import tqdm

log = logging.getLogger(__name__)

# pandas utils ###############################################


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


def fuzzymerge(df1, df2, key, minscore=None):
    """ merges on fuzzy text key
    exact matches first; then unmatched df1 to closest unmatched on df2
    left join that expects zero or one match in df2
    warns if duplicates matches
    
    :param key: column to merge on. must be in df1 and df2
    :param minscore: if set then returns only matches above this
    :return: merged dataframe. if minscore=None then show scores to identify appropriate minscore cutoff.

    e.g. match area names on two data sources such as "Birmingham, West" and "West Birmingham"
    """
    df1 = df1.copy()
    df2 = df2.copy()

    # get exact matches first as faster
    merged = df1.merge(df2[[key]], on=key, how="outer", indicator=True)
    unmatched1 = merged[merged._merge == "left_only"][key].tolist()
    unmatched2 = merged[merged._merge == "right_only"][key].tolist()

    # fuzzy matches. mapper will contain list of tuples (unmatched1, best match, score)
    mapper = []
    for v in unmatched1:
        # returns tuple (best match, score)
        res = process.extractOne(v, unmatched2)
        if not res:
            res = (v, "no match", 0)
        mapper.append([v, *res])
    mapper = pd.DataFrame(mapper, columns=[key, "fuzzykey", "fuzzyscore"])
    df1 = df1.merge(mapper, on=key, how="left")

    # matched
    matched = df1[key].isin(df2[key])
    df1.loc[matched, "fuzzykey"] = df1[key]
    df1.loc[matched, "fuzzyscore"] = 100

    # fuzzy match
    res = df1.merge(df2.rename(columns={key: "fuzzykey"}), on="fuzzykey", how="left")
    fuz = ["fuzzykey", "fuzzyscore"]
    if minscore is None:
        # to check what minscore should be
        return res.sort_values("fuzzyscore").set_index([key] + fuz)
    else:
        # after setting minscore
        res = res[res.fuzzyscore > minscore]
        dupes = res.loc[res.fuzzykey.duplicated(keep=False), fuz]
        if len(dupes) > 0:
            log.warning(f"some duplicate matches\n{dupes}")
        return res.drop(fuz, axis=1).set_index(key)


def mapply(df, func, **kwargs):
    """ apply func to dataframe using multiprocessing to split across cores
    :param df: pandas dataframe
    :param func: function to apply to df
    :param ncores: number of cores. default cpu_count.
    :param nsplit: number of splits in dataframe. default cpu_count.
    :param kwargs: all kwargs not listed above are passed to func
    func is any function and can be tested using basic df.apply
    """
    ncores = kwargs.pop("ncores", os.cpu_count())
    nsplits = kwargs.pop("nsplits", os.cpu_count())
    # partial enables additional parameters as pool.map just accepts iterator
    func = partial(func, **kwargs)
    chunks = np.array_split(df, nsplits)
    pool = Pool(ncores)
    res = tqdm(pool.map(func, chunks), total=nsplits)
    df = pd.concat(res)
    pool.close()
    pool.join()
    return df


pd.DataFrame.mapply = mapply

# general utils ###############################################


@contextlib.contextmanager
def tempdir(path):
    """ change folder temporarily """
    saved = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(saved)


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


# geo utils ###############################################################


def geojson(gdf):
    """ return geojson from geodataframe
    includes geometry, crs, properties (from other columns)
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        gdf = gpd.GeoDataFrame(gdf)
    f = BytesIO()
    gdf.to_file(f, driver="GeoJSON")

    return json.loads(f.getvalue())


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


def km2deg(km, a=(50.8, 2.7)):
    """ convert km to degrees distance
    :param a: latitude, longtitude of point. default is Dorset, uk.
    """
    b = a[0] + 0.1, a[1] + 0.1
    deg = np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)
    return km * deg / geodesic(a, b).km


def deg2km(deg, a=(50.8, 2.7)):
    """ convert distance from degrees to km
    :param a: latitude, longtitude of point. default is Dorset, uk.
    """
    return deg / km2deg(1)

import contextlib
import difflib
import json
import os
from io import BytesIO

import pandas as pd
from fuzzywuzzy import fuzz, process
from IPython.display import HTML


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

This is a thin python wrapper for mapbox. It generates javscript to execute mapboxgl and create mapbox maps.

Create a map using minimal defaults
-----------------------------------

Set root settings as required::

    from mapboxer import Map
    m = Map()
    m.center = [-1.7083, 52.1917]
    m.zoom = 10

Add data sources
----------------

This is a dataframe with column for geometry (shapes)::

    m.add_source("wards", wards)

Add layers
----------

Mapboxer has defaults for text_color, text_size, fill colors, legend, colorset, stops and labels. It automatically creates checkboxes to hide/show layers; and a legend. If the property column is numeric it is treated as continuous; and non-numeric as categoric. You can pass colorset, stops and labels, method as parameters and these will be translated into the fill_color specification. In addition you can pass a dict with any json meeting mapbox style specification using "_" instead of "-".

add a boundary layer with additional mapbox style for line-width::

    m.add_layer("wards", type="line", source="wards", paint=dict(line_width=3))

add a symbol layer with names. This datasource must have columns for geometry (points) and wardname.::

    m.add_layer("wardnames", type="symbol", source="wardcentres", property="wardname")

add a fill layer. This datasource must have columns for geometry (shapes) and cats::

    m.add_layer("shading", type="fill", source="wards", property="cats")

Change layout
-------------

There are templates for a single map and two maps using a slider. You can adapt the html, css and js to create new designs as required.

Examples
--------

See nbs folder for notebook examples creating maps of uk election data. The data can be downloaded from here:

    https://1drv.ms/u/s!ArsX3Y0hmkzcyuFlmbXhfkenAnmyQg?e=k5VH92







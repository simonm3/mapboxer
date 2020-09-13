This is a thin python wrapper for mapbox. It generates javscript to execute mapboxgl and create mapbox maps.

Create a map using minimal defaults
-----------------------------------

Set root settings as required::

    from mapboxer import Map
    m = Map()
    m.center = [-1.7083, 52.1917]
    m.zoom = 10

Add layers
----------

* full mapbox style specification via kwargs
* dotdict parameters with underscores converted to dashes e.g. paint.fill_color
* defaults that can be overridden
* accepts geopandas data
* see add_layers parameters for more detail

add a boundary layer with additional mapbox style for line-width::

    m.add_layer("wards", type="line", x=wards, paint=dict(line_width=3))

add a symbol layer with names. This datasource must have columns for geometry (points) and wardname.::

    m.add_layer("wardnames", type="symbol", source=wardcentres, x="wardname")

add a fill layer. This datasource must have columns for geometry (shapes) and cats::

    m.add_layer("shading", type="fill", source=wards, x="cats")

Add data sources
----------------

Typically add_layer is passed a source=mydata where mydata is a geodataframe. Alternatively one can call add_source separately. This enables one source to be shared by different layers::

    m.add_source("wards", wards)
    m.add_layer("wards", type="line", source="wards", paint=dict(line_width=3)


Change layout
-------------

There are templates for a single map, two maps using a slider, and two maps arranged vertically. You can adapt the html, css and js to create new designs as required.

Examples
--------

See nbs folder for notebook examples creating maps of uk election data. The data can be downloaded from here:

    https://1drv.ms/u/s!ArsX3Y0hmkzcyuFlmbXhfkenAnmyQg?e=k5VH92







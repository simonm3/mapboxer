var map2 = new mapboxgl.Map(
    [[=XML(map2.root())]]
);
map2.on('load', function () {
    // sources
    [[for k, v in map2.sources.items():]]
    map2.addSource('[[=k]]', [[=XML(v)]]);
    [[pass]]

    // layers
    [[for layer in map2.layers:]]
    map2.addLayer([[=XML(json.dumps(layer))]]);
    [[pass]]

    // show/hide map1 layer and legend
    for (layerid of [[=XML([layer["id"] for layer in map1.layers])]]) {
    // When the checkbox changes, update the visibility of the layer and legend
    $("#" + layerid).change(function (e) {
        map1.setLayoutProperty(e.target.id, 'visibility', e.target.checked ? 'visible' : 'none');
        map2.setLayoutProperty(e.target.id, 'visibility', e.target.checked ? 'visible' : 'none');
        $("#" + e.target.id + "_legend").toggle()
    });
    // end for
}
[[pass]]

syncMaps([map1, map2])
})
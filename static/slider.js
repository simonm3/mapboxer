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
    map2.addLayer([[=XML(layer)]]);
    [[pass]]

    // show/hide layer and legend
    for (layername of [[=XML([layer["id"] for layer in map2.layers])]]) {
    // When the checkbox changes, update the visibility of the layer.
    $("#" + layername).change(function (e) {
        // show/hide fill layer
        map1.setLayoutProperty(e.target.id, 'visibility', e.target.checked ? 'visible' : 'none');
        map2.setLayoutProperty(e.target.id, 'visibility', e.target.checked ? 'visible' : 'none');

        // show/hide legend
        $("#" + e.target.id + "_legend").toggle()
    });
    // end for
}
[[pass]]

let compare = new mapboxgl.Compare(map1, map2, '#slider');
compare.setSlider(0) //$("#comparison-container").width())
})
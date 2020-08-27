[[from yatl import XML
  import json
]]
mapboxgl.accessToken = '[[=token]]';

var map1 = new mapboxgl.Map(
    [[=XML(map1.root())]]
);
map1.on('load', function () {
    // sources
    [[for k, v in map1.sources.items():]]
    map1.addSource('[[=k]]', [[=XML(v)]]);
    [[pass]]

    // layers
    [[for layer in map1.layers:]]
    map1.addLayer([[=XML(json.dumps(layer))]]);
    [[pass]]

    // toggle layer/legend
    for (layername of [[=XML([layer["id"] for layer in map1.layers])]]) {
    $("#" + layername).change(function (e) {
        map1.setLayoutProperty(e.target.id, 'visibility', e.target.checked ? 'visible' : 'none'
        );
        $("#" + e.target.id + "_legend").toggle()
    });
    // end for
}
var geocoder = new MapboxGeocoder({
    accessToken: mapboxgl.accessToken,
    mapboxgl: mapboxgl
});
document.getElementById('geocoder').appendChild(geocoder.onAdd(map1));
// end map1.on
});


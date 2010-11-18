function create_map(id, lat, lon, points) {
    OpenLayers.Util.getImagesLocation = function() { return '/site-media/openlayers/img/'; };
    var options = {
        projection: new OpenLayers.Projection("EPSG:900913"),
        displayProjection: new OpenLayers.Projection("EPSG:4326"),
        units: "m",
        maxResolution: 156543.0339,
        maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
        numZoomLevels: 20,
    };
    map = new OpenLayers.Map(id, options);
    //map.add    Control(new OpenLayers.Control.iPhoneNavigation());
    var mapnik = new OpenLayers.Layer.TMS(
        "OpenStreetMap (Mapnik)",
        "http://tile.openstreetmap.org/",
        {
            type: 'png', getURL: osm_getTileURL,
            displayOutsideMaxExtent: true,
//            attribution: '<a href="http://www.openstreetmap.org/">OpenStreetMap</a>'
        }
    );
    var size = new OpenLayers.Size(21, 25);
    var icon_red = new OpenLayers.Icon(
        '/beta/site-media/openlayers/img/marker.png',
        size,
        new OpenLayers.Pixel(-(size.w/2), -size.h)
    );
    var icon_blue = new OpenLayers.Icon(
        'http://oucs-alexd:8000/beta/site-media/openlayers/img/marker-blue.png',
        size,
        new OpenLayers.Pixel(-(size.w/2), -size.h)
    );
    
    markers = new OpenLayers.Layer.Markers("Markers");
    
    if (points != null) {
        for (i=0; i<points.length; i++) {
            point = points[i];
            marker = new OpenLayers.Marker(
                new OpenLayers.LonLat(point.lon, point.lat).transform(map.displayProjection, map.projection),
                icon_blue.clone()
            );
            marker.events.register('click', marker, function(evt) {
                alert(marker);
            });
            markers.addMarker(marker);
        }
    }
    
    map.addLayers([markers, mapnik]);
    
    map.setCenter(new OpenLayers.LonLat(lon, lat).transform(map.displayProjection, map.projection), 12);
    
    return map;
}

function osm_getTileURL(bounds) {
    var res = this.map.getResolution();
    var x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
    var y = Math.round((this.maxExtent.top - bounds.top) / (res * this.tileSize.h));
    var z = this.map.getZoom();
    var limit = Math.pow(2, z);

    if (y < 0 || y >= limit) {
        return OpenLayers.Util.getImagesLocation() + "404.png";
    } else {
        x = ((x % limit) + limit) % limit;
        return this.url + z + "/" + x + "/" + y + "." + this.type;
    }
}

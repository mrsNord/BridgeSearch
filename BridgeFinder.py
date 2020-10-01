import overpy

lat = "33.376193"
lng = "-112.151254"
radiusMiles     = 1
radiusMeters    = radiusMiles*1609.34 # convert to meters
osm             = overpy.Overpass(max_retry_count = 5, retry_timeout = 1)
query           = """[out:json];
way[bridge][highway!="footway"](around:{},{},{});
out body;
node(w:1,-1);
out geom;"""

resultsRaw      = osm.query(query.format(radiusMeters, lat, lng))
print(resultsRaw)

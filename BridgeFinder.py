import overpy
import pandas
import math

#Constants
radiusMeters = 100
query           = """[out:json];
(
way[bridge][highway!="pedestrian"][highway!="footway"][highway!="path"][highway!="cycleway"][highway!="service"][!railway](around:{},{},{});
way[bridge][highway!="pedestrian"][highway!="footway"][highway!="path"][highway!="cycleway"][highway!="service"][!railway](around:{},{},{});
);
out body;
node(w:1,-1);
out geom;"""


#Functions
def ATCF(startLat, startLng, endLat, endLng):
    earthR              = 6378137 # earth's approximate radius in meters
    p1Lat               = startLat
    p1Long              = startLng
    p2Lat               = endLat
    p2Long              = endLng
    dLat                = math.radians(p2Lat - p1Lat)
    dLong               = math.radians(p2Long - p1Long)
    a                   = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(math.radians(p1Lat)) * math.cos(math.radians(p2Lat)) * math.sin(dLong / 2) * math.sin(dLong / 2)
    angularDistance     = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    arcLength           = earthR * angularDistance
    return arcLength

dfIn = pandas.read_excel("BridgeTest.xlsx")
dfOut = pandas.DataFrame(columns=["id",'isBridge', 'Name', 'Distance Start', 'Distance End', 'Bridge_Start_Lat', 'Bridge_Start_Lon', 'Bridge_End_Lat', 'Bridge_End_Lon', 'WayID', 'WayLink'] )
osm = overpy.Overpass(max_retry_count = 5, retry_timeout = 1)
total = len(dfIn.index)
count = 0

for index, row in dfIn.iterrows():
    count += 1
    print("Completed {} of {} lookups.".format(count, total))
    osmQuery = query.format(radiusMeters, row['LATITUDE_BEGIN'], row['LONGITUDE_BEGIN'], radiusMeters, row['LATITUDE_END'], row['LONGITUDE_END'])
    resultsRaw = osm.query(osmQuery)
    rowObj = {'id': row['OBJECTID']}

    if not resultsRaw:
        rowObj['isBridge'] = 'no'
        dfOut = dfOut.append(rowObj, ignore_index=True)
        continue

    if len(resultsRaw.ways) <= 0:
        rowObj['isBridge'] = 'no'
        dfOut = dfOut.append(rowObj, ignore_index=True)
        continue
  
    for way in resultsRaw.ways:
        rowObj = {'id': row['OBJECTID'], 'Name': way.tags.get("name", way.tags.get("tiger:name_base","n/a")), 'isBridge': 'yes', 'WayID': way.id,'WayLink': 'https://www.openstreetmap.org/way/' + str(way.id)}
        try:
            if len(way._node_ids) >= 2:
                node0ID = way._node_ids[0]
                node1ID = way._node_ids[len(way._node_ids)-1]
                node0 = resultsRaw.get_node(node0ID,resolve_missing=True)
                node1 = resultsRaw.get_node(node1ID,resolve_missing=True)
                disT1 = ATCF(row['LATITUDE_BEGIN'], row['LONGITUDE_BEGIN'], float(node0.lat), float(node0.lon))
                disT2 = ATCF(row['LATITUDE_END'], row['LONGITUDE_END'], float(node0.lat), float(node0.lon))
                if disT1 < disT2:
                    rowObj['Distance Start'] = disT1
                    rowObj['Bridge_Start_Lat'] = float(node0.lat)
                    rowObj['Bridge_Start_Lon'] = float(node0.lon)
                    rowObj['Bridge_End_Lat'] = float(node1.lat)
                    rowObj['Bridge_End_Lon'] = float(node1.lon)
                    rowObj['Distance End'] = ATCF(row['LATITUDE_END'], row['LONGITUDE_END'], float(node1.lat), float(node1.lon))
                else:
                    rowObj['Distance Start'] = disT2
                    rowObj['Bridge_Start_Lat'] = float(node1.lat)
                    rowObj['Bridge_Start_Lon'] = float(node1.lon)
                    rowObj['Bridge_End_Lat'] = float(node0.lat)
                    rowObj['Bridge_End_Lon'] = float(node0.lon)
                    rowObj['Distance End'] = ATCF(row['LATITUDE_END'], row['LONGITUDE_END'], float(node0.lat), float(node0.lon))
                
            dfOut = dfOut.append(rowObj, ignore_index=True)
        except overpy.exception.DataIncomplete:
            rowObj = {'id': row['OBJECTID'], 'isBridge': 'warning'}
            dfOut = dfOut.append(rowObj, ignore_index=True)

combinedDf = dfIn.set_index('OBJECTID').join(dfOut.set_index('id'))
combinedDf.to_excel("output.xlsx")  





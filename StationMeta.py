# Copyright Andrew.M.G.Reynen
from obspy import read_inventory
import numpy as np
import pyproj

# Convert a station xml file to a numpy array, containing only [StaCode,Lon,Lat,Ele]
def staXml2Loc(staXml):
    # Loop through just to extract the station codes and locations...
    # ...with format [Sta,Lon(deg),Lat(deg),Ele(m)], lon/lat assumed to be in WGS84 datum
    outArr=[]
    for net in staXml:
        for sta in net:
            outArr.append([sta.code,sta.longitude,sta.latitude,sta.elevation])
    # If the file was empty, convert to appropriate shape
    if len(outArr)==0:
        outArr=np.empty((0,4))
    else:
        outArr=np.array(outArr,dtype=str)
    return outArr

# Read in a station xml file given the path name
def readInventory(staFile):
    return read_inventory(staFile,format='stationxml')

# Project the stations from Lon/Lat to desired system   
def projStaLoc(staLoc,projStyle):
    # Generate the projection object to do the conversions...
    # ...Universal Transverse Mercator
    if projStyle=='UTM':
        UTM_Zone=int(np.floor((np.median(staLoc[:,1].astype(float)) + 180.0)/6) % 60) + 1
        wantProj = pyproj.Proj(proj='utm',zone=UTM_Zone,datum='WGS84')
    # ...Albers Equal Area (Conic)
    elif projStyle=='AEA Conic':
        # Use the bounds of the stations for guidelines
        staLons,staLats=staLoc[:,1].astype(float),staLoc[:,2].astype(float)
        minLat,maxLat=np.min(staLats),np.max(staLats)
        minLon,maxLon=np.min(staLons),np.max(staLons)
        # Latitudes where the cone intersects the ellipsoid
        lat1,lat2=(maxLat-minLat)*1.0/6+minLat,(maxLat-minLat)*5.0/6+minLat
        # The origin of the projection
        lat0,lon0=(maxLat-minLat)*1.0/2+minLat,(maxLon-minLon)*1.0/2+minLon
        wantProj = pyproj.Proj(proj='aea',lat_1=lat1,lat_2=lat2,lat_0=lat0,lon_0=lon0,datum='WGS84',ellps='WGS84')
    else:
        print('projStyle '+projStyle+' not yet supported, skipped')
        return staLoc
    # Calculate the new X and Y values
    staLoc[:,1:3]=np.array([wantProj(float(lon),float(lat),inverse=False) for lon,lat in staLoc[:,1:3]],dtype=str)
    # Convert units from m to km
    staLoc[:,1:4]=staLoc[:,1:4].astype(float)/1000.0
    # Make the Z values positive downwards
    staLoc[:,3]=staLoc[:,3].astype(float)*-1.0
    return staLoc
    
    
# Author: Andrew.M.G.Reynen

from obspy import read_inventory
import numpy as np
import pyproj

# Convert a station xml file to a numpy array, containing only [StaCode,Lon,Lat,Ele]
def staXml2Loc(staXml):
    # Loop through just to extract the station codes and locations...
    # ...with format [Net.Sta.Loc,Lon(deg),Lat(deg),Ele(m)], lon/lat assumed to be in WGS84 datum
    outArr=np.empty((0,4),dtype='a32')
    for net in staXml:
        for sta in net:
            if len(sta.channels)==0:
                print(net.code+','+sta.code+' has no channels, could not read location code')
            for cha in sta:
                nsl='.'.join([net.code,sta.code,cha.location_code])
                # Do not add this station id already present
                if len(outArr)>0:
                    if nsl in outArr[:,0]:
                        continue
                entry=np.array([nsl,cha.longitude,cha.latitude,cha.elevation],dtype='a32')
                outArr=np.vstack((outArr,entry))
    # If the file was empty, convert to appropriate shape
    if len(outArr)==0:
        outArr=np.empty((0,4),dtype='a32')
    else:
        outArr=np.array(outArr,dtype=str)
    return outArr

# Read in a station xml file given the path name
def readInventory(staFile):
    return read_inventory(staFile,format='stationxml')

# Conversion factor between meters and given unit
def unitConversionDict():
    return {'m':1.0,
            'km':1000.0,
            'ft':0.3048,
            'yd':0.9144,
            'mi':1609.344}

# Set the projection function
def setProjFunc(mapProj,staLoc,init=False):
    inProj=pyproj.Proj(init='EPSG:4326')
    # Extra key word arguments to be passed to the new projection
    extraKwargs={'axis':mapProj['zDir'],'preserve_units':True}
    if mapProj['units']!='deg':
        extraKwargs['units']=mapProj['units']
    
    # If using a projection defined on station locations...
    if mapProj['type']=='Simple':
        # ...no projection
        if mapProj['simpleType']=='None' or 0 in staLoc.shape:
            outProj=pyproj.Proj(init='EPSG:4326',**extraKwargs)
            if 0 in staLoc.shape and mapProj['simpleType']!='None' and not init:
                print('Cannot determine projection as no stations given, using no projection')
        # ...Universal Transverse Mercator
        elif mapProj['simpleType']=='UTM':
            UTM_Zone=int(np.floor((np.median(staLoc[:,1].astype(float)) + 180.0)/6) % 60) + 1
            outProj = pyproj.Proj(proj='utm',zone=UTM_Zone,
                                  datum='WGS84',**extraKwargs)
        # ...Albers Equal Area (Conic)
        elif mapProj['simpleType']=='AEA Conic':
            # Use the bounds of the stations for guidelines
            staLons,staLats=staLoc[:,1].astype(float),staLoc[:,2].astype(float)
            minLat,maxLat=np.min(staLats),np.max(staLats)
            minLon,maxLon=np.min(staLons),np.max(staLons)
            # Latitudes where the cone intersects the ellipsoid
            lat1,lat2=(maxLat-minLat)*1.0/6+minLat,(maxLat-minLat)*5.0/6+minLat
            # The origin of the projection
            lat0,lon0=(maxLat-minLat)*1.0/2+minLat,(maxLon-minLon)*1.0/2+minLon
            outProj=pyproj.Proj(proj='aea',lat_1=lat1,lat_2=lat2,lat_0=lat0,lon_0=lon0,
                                datum='WGS84',ellps='WGS84',**extraKwargs)
        # ...catch
        else:
            print('Simple projection not defined, how did we get here?')
    # If using a EPSG code
    else:
        outProj=pyproj.Proj(init='EPSG:'+mapProj['epsg'],**extraKwargs)
    mapProj['func']=lambda xyzArr:np.array(pyproj.transform(inProj,outProj,*xyzArr.T)).T
    mapProj['funcInv']=lambda xyzArr:np.array(pyproj.transform(outProj,inProj,*xyzArr.T)).T
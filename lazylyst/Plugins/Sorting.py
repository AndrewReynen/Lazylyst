from __future__ import print_function

import numpy as np

from Plugins.Locate import getVelDelay,getPickData,simpleLocatorFunc
from Plugins.GlobalLocate import sph2xyz,vecsAngle

# Return the stations in alphabetical order
def staSortAlph(staSort):
    return np.sort(staSort)
    
# Return the station based on the current pick ordering
def staSortPickTime(staSort,pickSet,pickMode):
    # Tertiary sorting is alphabetical
    staSort=np.sort(staSort)
    # If no picks, return alphabetical
    if len(pickSet)==0:
        return staSort
    # Secondary sorting is all other pick types (add a large delay)
    maxT=np.max(pickSet[:,2].astype(float))
    offset=maxT-np.min(pickSet[:,2].astype(float))+1
    args=np.where(pickSet[:,1]!=pickMode)
    pickSet[args,2]=(pickSet[args,2].astype(float)+offset).astype(str)
    pos=[]
    for i,sta in enumerate(staSort):
        if sta in pickSet[:,0]:
            pos.append(np.min(pickSet[np.where(pickSet[:,0]==sta),2].astype(float)))
        else:
            pos.append(maxT+offset+i+1)
    return staSort[np.argsort(pos)]

# Return the station based on the distance from the current event
def staSortDist(staSort,staLoc,mapCurEve,mapProj):
    # If no event has been located, do not change anything
    if len(mapCurEve)==0 or len(staLoc)==0:
        return '$pass'
    # Project the station and event locations
    staLoc[:,1:4]=mapProj['func'](staLoc[:,1:4])
    mapCurEve[:,1:4]=mapProj['func'](mapCurEve[:,1:4])
    # Secondary sorting is alphabetical
    staSort=np.sort(staSort)
    # Replace Lons,Lats,Elev with X,Y,Z on sphere if units in degrees...
    # ...also split array into the string and float components
    staNames=list(staLoc[:,0])
    if mapProj['units']=='deg':
        staLoc=sph2xyz(staLoc[:,1:3].astype(float))
        eveLoc=sph2xyz(mapCurEve[:,1:3].astype(float))[0]
    else:
        staLoc=staLoc[:,1:].astype(float)
        eveLoc=mapCurEve[0,1:4]
    # Loop through each station, getting its distance from the current event...  
    pos=[]
    for i,sta in enumerate(staSort):
        if sta in staNames:
            staXyz=staLoc[staNames.index(sta),:]   
            # ...if projected, then calculate euclidean distance
            if mapProj['units']!='deg':
                dist=np.sum((staXyz-eveLoc)**2)**0.5
            # ...otherwise calculate the angle between stations and the event (depth ignored)
            else:
                dist=vecsAngle(staXyz,eveLoc)
            pos.append(dist)
        else:
            pos.append(-1*(i+1))
    # Reassign the "pos" of stations which did not have a station metadata present
    pos=np.array(pos,dtype=float)
    args=np.where(pos<0)
    pos[args]=pos[args]*-1+np.max(pos)
    return staSort[np.argsort(pos)]
   
# Return the station based on the residual (largest first)...
# ...currently works only with SimpleLocator
def staSortResidual(staSort,staLoc,sourceDict,pickSet,mapCurEve,mapProj):
    # Secondary sorting is alphabetical
    staSort=np.sort(staSort)
    # Get the velocity and delay info
    vdInfo=getVelDelay(sourceDict)
    # If there was no vpInfo defined, or no event has been located, return alphabetical
    # Also return if not using a projection (simpleLocator requires it)
    if vdInfo=='$pass' or len(mapCurEve)==0 or mapProj['units']=='deg' or len(staSort)==0:
        return staSort
    # Reproject event and station locations
    staLoc[:,1:4]=mapProj['func'](staLoc[:,1:4])
    mapCurEve[:,1:4]=mapProj['func'](mapCurEve[:,1:4])
    data,stas=getPickData(pickSet,staLoc,vdInfo,mapProj)
    # If there was none of the wanted pick types, return alphabetical
    if len(data)==0:
        return staSort
    x0,y0,z0,t0=mapCurEve[0,1:]
    ti=simpleLocatorFunc(data[:,:5],x0,y0,z0,t0)
    # Get the difference with the actual arrival times
    resids=np.abs(ti-data[:,5])
    offset=np.max(resids)+1
    # Loop through each station, getting its max residual value from all phases   
    pos=[]
    for i,sta in enumerate(staSort):
        if sta in stas:
            pos.append(-1*np.max(resids[np.where(stas==sta)]))
        else:
            pos.append(i+offset)
    return staSort[np.argsort(pos)]
    
# Reverse the current station sorting
def staSortReverse(staSort):
    return staSort[::-1]
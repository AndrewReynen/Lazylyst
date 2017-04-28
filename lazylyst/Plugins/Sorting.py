import numpy as np
import sys
if sys.version_info[0]==2:
    from Locate import getVelDelay,getPickData,simpleLocatorFunc
else:
    from Plugins.Locate import getVelDelay,getPickData,simpleLocatorFunc

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

# Return the station based on the residual (largest first)
def staSortDist(staSort,staLoc,mapCurEve):
    # Secondary sorting is alphabetical
    staSort=np.sort(staSort)
    # If no event has been located, return alphabetical
    if len(mapCurEve)==0:
        return staSort
    eveLoc=mapCurEve[0,1:4]
    # Loop through each station, getting its distance from the current event   
    pos=[]
    for i,sta in enumerate(staSort):
        if sta in staLoc[:,0]:
            staXYZ=staLoc[np.where(staLoc[:,0]==sta)[0][0],1:].astype(float)      
            dist=np.sum((staXYZ-eveLoc)**2)**0.5
            pos.append(dist)
        else:
            pos.append(-1*(i+1))
    pos=np.array(pos,dtype=float)
    args=np.where(pos<0)
    pos[args]=pos[args]*-1+np.max(pos)
    return staSort[np.argsort(pos)]
   
# Return the station based on the residual (largest first)
def staSortResidual(staSort,staLoc,sourceTag,pickSet,mapCurEve):
    # Secondary sorting is alphabetical
    staSort=np.sort(staSort)
    # Get the velocity and delay info
    vdInfo=getVelDelay(sourceTag)
    # If there was no vpInfo defined, or no event has been located, return alphabetical
    if vdInfo=='$pass' or len(mapCurEve)==0:
        return staSort
    data,stas=getPickData(pickSet,staLoc,vdInfo)
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
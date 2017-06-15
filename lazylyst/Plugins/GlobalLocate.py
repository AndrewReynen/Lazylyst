import numpy as np
from scipy.optimize import curve_fit
import pickle

# Reference each pick to a station index
def getPickStaIdxs(pickSet,staNames):
    pickStas,pickIdx=np.unique(pickSet[:,0],return_inverse=True)
    pickStaIdxs=np.ones(len(pickIdx),dtype=int)*-1
    for pos in np.unique(pickIdx):
        sta=pickStas[pos]
        if sta in staNames:
            posArgs=np.where(pickIdx==pos)[0]
            pickStaIdxs[posArgs]=np.where(staNames==sta)[0][0]
    # Remove any picks which did not have station metadata
    keepArgs=np.where(pickStaIdxs!=-1)[0]
    pickStaIdxs=pickStaIdxs[keepArgs]
    pickSet=pickSet[keepArgs]
    return pickSet,pickStaIdxs

# Convert spherical coord numpy array to cartesian
# [[Lon1,Lat1],[Lon2,Lat2],...]
def sph2xyz(p):
    p[:,1]+=90
    # Convert from deg to rad
    p=np.pi*p/180.0
    xyz=[np.sin(p[:,1])*np.cos(p[:,0]),
         np.sin(p[:,1])*np.sin(p[:,0]),
         np.cos(p[:,1])]
    return np.array(xyz).T

# Convert from cartesion to spherical
def xyz2sph(p):
    lat=np.arccos(p[2])
    lon=np.arctan2(p[1],p[0])
    out=np.array([lon,lat])
    # Convert from rad to deg
    out*=180.0/np.pi
    out[1]-=90
    return out

# Get the angle in degrees between two vectors...
# ...assumes both vectors have a length of one (clips for rounding error in dot product)
# ...this is done to ignore speed reduction in repeatedly normalizing the station xyz vectors
def vecsAngle(v1,v2):
    return np.arccos(np.clip(np.dot(v1,v2),-1,1))*180.0/np.pi

# 3rd order polynomial fixed at 0,0
def poly3_Fixed(x,a,b,c):
    return np.clip(a*x**1+b*x**2+c*x**3,0,2000)

# 3rd order polynomial
def poly3(x,a,b,c,d):
    return np.clip(a*x**1+b*x**2+c*x**3+d,0,2000)

# Function to calculate the arrival times vs epicentral location
# ti=function((staX,staY,staZ,isPphase,isSphase,p1,p2,p3,s1,s2,s3),x0,y0,z0,t0)
# ti=t0+travelTime
def globalLocEpiFunc(data,x0,y0,z0,t0):
    eveXyz=np.array([x0,y0,z0])
    eveXyz=eveXyz/np.sqrt(np.sum(eveXyz**2)) # Normalize to length one
    paramP,paramS=data[:,5:8],data[:,8:11]
    degDists=vecsAngle(data[:,:3],eveXyz)
    ttP=poly3_Fixed(degDists,paramP[:,0],paramP[:,1],paramP[:,2])
    ttS=poly3_Fixed(degDists,paramS[:,0],paramS[:,1],paramS[:,2])
    return t0+data[:,3]*ttP+data[:,4]*ttS

# Function to calculate the arrival times vs depth
# ti=function((isPphase,isSphase,p1,p2,p3,p4,s1,s2,s3,s4),z0,t0)
# ti=t0+travelTime
def globalLocDepFunc(data,z0,t0):
    paramP,paramS=data[:,2:6],data[:,6:10]
    ttP=poly3(z0,paramP[:,0],paramP[:,1],paramP[:,2],paramP[:,3])
    ttS=poly3(z0,paramS[:,0],paramS[:,1],paramS[:,2],paramS[:,3])
    return t0+data[:,0]*ttP+data[:,1]*ttS

# Recalculate the current event-station distances with current event location
def recalcDegDists(data,params):
    # Normalize the params, as were not constrained in "curve_fit" to have magnitude of 1
    params[:3]=params[:3]/np.sqrt(np.sum(params[:3]**2))
    degDists=vecsAngle(data[:,:3],params[:3])
    return degDists,params

# Use travel times from the IASP91 model model to estimate the event location
# Gives approximate event location, less appropriate with smaller networks
# Depth is constrained from 0 to 200 km
# Method: A coarse search is done first using a third order polynomial fit, varying epicenter...
# ...a refined epicentral search is done using O(3) polynomials fits about the predicted station-event distances...
# ...a final search vs depth is done using O(3) polynomials at the refined station-event distances
# Special note: the scipy curve_fit function does not constrain variables, thus the length 1 vector...
# ...representing the surface position will not remain length 1; this effect is "ignored" as the...
# ...travel times are related to distance in degrees and so the orientation of this vector is all that matters
def globalLocate(pickSet,staLoc,mainPath,customDict,staProjStyle):
#    import time
#    now=time.time()
    # Nothing to do if no picks, or not in lon,lats
    if 0 in pickSet.shape or staProjStyle!='None':
        return np.empty((0,5)),customDict
    # Load in the model (if not already loaded into the custom dictionary)
    if 'globEpiDict' not in customDict.keys():
        customDict['globEpiDict']=pickle.load(open(mainPath+'/Plugins/epiTTparams.pickle','rb'))
        customDict['globDepDict']=pickle.load(open(mainPath+'/Plugins/depTTparams.pickle','rb'))
    ttEpiDict=customDict['globEpiDict']
    ttDepDict=customDict['globDepDict']
    # Remove anything but P and S picks
    for i,entry in enumerate(pickSet[:,1]):
        pickSet[i,1]=pickSet[i,1][0]
    pickSet=pickSet[np.where((pickSet[:,1]=='P')|(pickSet[:,1]=='S'))]
    # Get only picks which have station metadata
    pickSet,pickStaIdxs=getPickStaIdxs(pickSet,staLoc[:,0])
    
    # Generate the data for the rough global curve fitting...
    # ...(staX,staY,staZ,isPphase,isSphase,p1,p2,p3,s1,s2,s3)
    data=np.zeros((len(pickSet),11),dtype=float)
    # ...set the station locations
    data[:,:3]=sph2xyz(staLoc[pickStaIdxs,1:3].astype(float))
    # ...set phase markers
    data[:,3]=pickSet[:,1]=='P'
    data[:,4]=pickSet[:,1]=='S'
    # ...set the coefficients for the global travel time calculations
    data[:,5:]=np.concatenate((ttEpiDict['globP'],ttEpiDict['globS']))
    # ...get the "y" values to fit the curve to
    Tref=np.min(pickSet[:,2].astype(float))
    pickTimes=pickSet[:,2].astype(float)-Tref
    # Initial guess on origin, uses station location with earliest pick
    testLoc=data[np.argmin(pickTimes),:3] 
    testLoc=np.concatenate((testLoc,[0]))

    # Solve for event origin parameters
    try:
        params, pcov = curve_fit(globalLocEpiFunc,data,pickTimes,testLoc,
                                 bounds=([-1,-1,-1,-2000],[1,1,1,2000]))
    except:
        print('Global locator failed')
        return np.empty((0,5)),customDict
    degDists,params=recalcDegDists(data,params) # Normalize params
    
    # Update the data for the refined global curve fitting...
    # ...figure out which pre-fit parameters should be taken for each pick 
    # (could be by station but likely fast enough)
    bins=np.arange(0-0.5*ttEpiDict['spacing'],
                   180+0.51*ttEpiDict['spacing'],ttEpiDict['spacing'])
    idxs=np.digitize(degDists,bins)-1
    data[:,5:8]=ttEpiDict['pParams'][idxs]
    data[:,8:11]=ttEpiDict['sParams'][idxs]
    # Fit again with refined parameters, use previous location as starting position
    try:
        params, pcov = curve_fit(globalLocEpiFunc,data,pickTimes,params,
                                 bounds=([-1,-1,-1,-2000],[1,1,1,2000]))
    except:
        print('Global locator failed')
        return np.empty((0,5)),customDict
    # Convert back from the xyz to lon,lat
    degDists,params=recalcDegDists(data,params) # Normalize params
    lon,lat=xyz2sph(params[:3])
    
    # Generate the data for the depth curve fitting...
    bins=np.arange(0-0.5*ttDepDict['spacing'],
                   180+0.51*ttDepDict['spacing'],ttDepDict['spacing'])
    idxs=np.digitize(degDists,bins)-1
    dataDep=np.zeros((len(data),10),dtype=float)
    dataDep[:,:2]=data[:,3:5]
    dataDep[:,2:6]=ttDepDict['pParams'][idxs]
    dataDep[:,6:10]=ttDepDict['sParams'][idxs]
    # Fit again with depth parameters, use model starting depth and previous origin time as starting position
    try:
        depParams, pcov = curve_fit(globalLocDepFunc,dataDep,pickTimes,[ttEpiDict['startDep'],params[-1]],
                                 bounds=([0,-2000],[200,2000]))
    except:
        print('Global locator failed')
        return np.empty((0,5)),customDict
#    print time.time()-now,len(pickSet)
#    print lon,lat,depParams[0]
#    print(np.sum(np.abs(pickTimes-globalLocEpiFunc(data,*params)))/len(data),'preAvgResid')
#    print(np.sum(np.abs(pickTimes-globalLocDepFunc(dataDep,*depParams)))/len(data),'postAvgResig')
    return np.array([[0,lon,lat,depParams[0],depParams[1]+Tref]]),customDict

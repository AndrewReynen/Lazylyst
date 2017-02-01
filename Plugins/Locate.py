import numpy as np
import scipy.optimize as optimize

# Function to calculate the arrival times
# ti=function((xi,yi,zi,vi,di),x0,y0,t0)
# ti=t0+(Dist+Vel*Delay)/Vel
def simpleLocatorFunc(data,x0,y0,z0,t0):
    return t0+((((data[:,0]-x0)**2+(data[:,1]-y0)**2+(data[:,2]-z0)**2)**0.5)+data[:,3]*data[:,4])/data[:,3]

# Locate event using a straight ray path, and non-linear least squares curve fitting
def simpleLocator(pickSet,staMeta,Vp=5.0,Vs=2.9,Dp=0,Ds=0):
    if len(pickSet)==0:
        return '$pass'
    # Use only P and S picks
    pickSet=pickSet[np.where((pickSet[:,1]=='P')|(pickSet[:,1]=='S'))]
    if len(pickSet)<4:
        return '$pass'
    # Form array to be able to send to the 0 dimensional travel time function
    Data=[] #[xi,yi,zi,vi,ti]
    # Compute value to take away from the very large travel times (easier on the curve fitting)
    Tref=np.min(pickSet[:,2].astype(float))
    for aPick in pickSet:
        # Ensure that this pick has station metadata present
        idx=np.where(staMeta[:,0]==aPick[0])[0]
        if len(idx)<1:
            continue
        aStaX,aStaY,aStaZ=staMeta[idx[0],1:4].astype(float)
        if aPick[1]=='P':
            aVel=Vp
            aDelay=Dp
        else:
            aVel=Vs
            aDelay=Ds
        aTime=(float(aPick[2])-Tref) ## Give more sig digs?... rough approximation anyways
        Data.append([aStaX,aStaY,aStaZ,aVel,aDelay,aTime])
    Data=np.array(Data)
    # solve for event origin parameters
    try:
        params, pcov = optimize.curve_fit(simpleLocatorFunc, Data[:,:5], Data[:,5],(0,0,0,0))
        x0,y0,z0,t0=params
        t0=Tref+t0
        return np.array([[0,x0,y0,z0,t0]])
    except:
        print 'simpleLocator failed'
        return '$pass'
from __future__ import print_function

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from obspy.taup import TauPyModel
model=TauPyModel(model="iasp91")
import pickle

# 3rd order polynomial fixed at 0,0
def poly3_Fixed(x,a,b,c):
    return np.clip(a*x**1+b*x**2+c*x**3,0,2000)

# 3rd order polynomial
def poly3(x,a,b,c,d):
    return np.clip(a*x**1+b*x**2+c*x**3+d,0,2000)

# Generate the epicentral location tests points
def getEpiPoints():
    degSpc=0.01
    testDegs=np.arange(0,180+0.5*degSpc,degSpc,dtype=float)
    pTimes,sTimes=[],[]
    for deg in testDegs:
        if deg%1==0:
            print(deg)
        # Get the earliest p and s arrival time
        arrivals=model.get_travel_times(source_depth_in_km=5,distance_in_degree=deg,
                                        phase_list=['ttp','tts'])
        pTimes.append(next((entry.time for entry in arrivals if entry.purist_name[0] in ['P','p']),None))
        sTimes.append(next((entry.time for entry in arrivals if entry.purist_name[0] in ['S','s']),None))
    outArr=np.array([testDegs,np.array(pTimes),np.array(sTimes)]).T
    np.save('globalTT',outArr)

# Generate the hypocentral location test points
def getDepthPoints():
    degSpc=0.01
    testDegs=np.arange(0,45+0.5*degSpc,degSpc,dtype=float)
    testDeps=np.arange(0,200.1,5)
    fullArr=[]
    for deg in testDegs:
        print(deg)
        pTimes,sTimes=[],[]
        for dep in testDeps:
            # Get the earliest p and s arrival time
            arrivals=model.get_travel_times(source_depth_in_km=dep,distance_in_degree=deg,
                                            phase_list=['ttp','tts'])
            pTimes.append(next((entry.time for entry in arrivals if entry.purist_name[0] in ['P','p']),None))
            sTimes.append(next((entry.time for entry in arrivals if entry.purist_name[0] in ['S','s']),None))
        fullArr.append(np.array([testDeps,np.array(pTimes),np.array(sTimes)]).T)
    np.save('globalTT_vDep_1',np.array(fullArr,dtype=float))

# Calculate the parameters in TT(EpiDist) to be used at specific degrees
def getEpiParams():
    outArr=np.load('globalTT.npy')
    globP,pcov=curve_fit(poly3_Fixed, outArr[:,0], outArr[:,1])
    globS,pcov=curve_fit(poly3_Fixed, outArr[:,0], outArr[:,2])
    
    # For a suite of small limits, calculate the parameters for refined searching
    buff=2.5
    spacing=1.0
    startDep=5 # Source depth used when calculating epi points
    plt.plot(outArr[:,0],outArr[:,1],'c--',lw=2)
    plt.plot(outArr[:,0],outArr[:,2],'b--',lw=2)
    outDict={'globP':globP, # Parameters for fitting the global TT values of P-wave
             'globS':globS, # Parameters for fitting the global TT values of S-wave
             'buff':buff,   # Buffer about each degree used to fit for the refined parameters 
             'spacing':spacing, # Spacing between degrees for refined parameter calculation
             'startDep':startDep}
    pParams,sParams=[],[]
    for deg in np.arange(0,180.0+0.1*spacing,spacing):
        print(deg)
        aMin=np.max([0,deg-buff])
        aMax=np.min([180,deg+buff])
        wantArgs=np.where((outArr[:,0]>=aMin)&(outArr[:,0]<=aMax))[0]
        paramP,pcov=curve_fit(poly3_Fixed, outArr[wantArgs,0], outArr[wantArgs,1],globP)
        paramS,pcov=curve_fit(poly3_Fixed, outArr[wantArgs,0], outArr[wantArgs,2],globS)
        plt.plot(outArr[wantArgs,0],poly3_Fixed(outArr[wantArgs,0],*paramP),'g',lw=0.5)
        plt.plot(outArr[wantArgs,0],poly3_Fixed(outArr[wantArgs,0],*paramS),'r',lw=0.5)
        pParams.append(paramP)
        sParams.append(paramS)
    
    outDict['pParams']=np.array(pParams)
    outDict['sParams']=np.array(sParams)
    pickle.dump( outDict, open('epiTTparams.pickle','wb'))
    
    plt.plot(outArr[:,0],poly3_Fixed(outArr[:,0],*globP),'k')
    plt.plot(outArr[:,0],poly3_Fixed(outArr[:,0],*globS),'k')
    plt.show()
    
# Calculate the parameters in TT(Depth) to be used at specific degrees
def getDepParams():
    data1=np.load('globalTT_vDep_1.npy')
    data2=np.load('globalTT_vDep_2.npy')
    data3=np.load('globalTT_vDep_3.npy')
    data4=np.load('globalTT_vDep_4.npy')
    
    data2=data2[1:,:,:]
    data3=data3[1:,:,:]
    data4=data4[1:,:,:]
    
    data=np.vstack((data1,data2,data3,data4))
    # Assumes starts at 0 degrees and ends at 180
    outDict={'spacing':0.01}
    
    pParams,sParams=[],[]
    for entry in data:
        paramP,pcov=curve_fit(poly3, entry[:,0], entry[:,1])
        paramS,pcov=curve_fit(poly3, entry[:,0], entry[:,2])
        pParams.append(paramP)
        sParams.append(paramS)
    outDict['pParams']=np.array(pParams)
    outDict['sParams']=np.array(sParams)
    pickle.dump( outDict, open('depTTparams.pickle','wb'))
    
#getDepParams()
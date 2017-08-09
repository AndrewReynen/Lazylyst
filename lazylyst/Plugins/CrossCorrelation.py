import numpy as np
from obspy import UTCDateTime
from scipy import signal

# Calculate the moving sum of an array
def MovingSum(arr, n=3):
    ret = np.cumsum(arr, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:]

# Calculate the cross correlation...
# ...which is (a*b)/(|a||b|) if normalized, just (a*b) otherwise
def calcXCor(template,data,norm=True):
    # Return nothing if the template is longer than the data
    if len(data)<=len(template)+1:
        return []
    Top=signal.fftconvolve(data, template[::-1], mode='valid')
    if norm:
        # Calculate the magnitudes of the data vectors to be used for normalization
        DataMag=np.sqrt(MovingSum(data**2,len(template)))
        Bot=DataMag*np.sqrt(np.sum(template**2))
        # Replace and bottom values of zero with the max of Bot ( the top values will also be affected, so...
        # ... areas near the zeros still won't get very large... just avoiding divide by zero here)
        Bot[Bot==0]=np.max(Bot) # These are always positive values, no need for np.abs()
        XCors=Top/Bot
    else:
        XCors=Top
    return XCors
    
# Gather the offset values, based on a specific template...
# ...assumes template is for a vertical channel
def getVertXCorOffsets(tempTrace,stream):
    stream=stream.select(component='Z')
    stas,offsets,xCors=[],[],[]
    # Taper the stream and template
    stream.taper(0.10,type='hann',max_length=2.0)
    tempTrace.taper(0.10,type='hann',max_length=2.0)
    # Loop through each trace and get their offsets, and max XCor values
    for tr in stream:
        # Skip if the trace in question does not have the same sampling rate
        if tr.stats.delta!=tempTrace.stats.delta:
            continue
        xCorArr=calcXCor(tempTrace.data,tr.data,norm=True)
        # Skip if the normalized cross-correlation values do not exist
        if len(xCorArr)==0:
            continue
        if np.max(xCorArr)<=0:
            continue
        aSta=tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.location
        offset=tr.stats.starttime+tr.stats.delta*np.argmax(xCorArr)-tempTrace.stats.starttime
        xCor=np.max(xCorArr)
        # If another trace had the same station see if larger...
        if aSta in stas:
            idx=stas.index(aSta)
            # ...if so, replace previous values
            if xCor>xCors[idx]:
                xCors[idx]=xCor
                offsets[idx]=offset
        else:
            stas.append(aSta)
            offsets.append(offset)
            xCors.append(xCor)
    return stas,offsets
    
# Returns a stream, where the waveforms have been aligned to a specified reference...
# ...uses a template window length (in seconds) defined by [templatePre,templatePost]
# ...all alignment is based off the vertical channel
# ...the earliest pick of type "phaseType" is used as reference
def xCorAlign(*args,**kwargs):
    # Check to ensure all the wanted kwargs are present
    for kwarg in ['templatePre','templatePost','phaseType']:
        if kwarg not in kwargs.keys():
            print('Ensure that the optionals "templatePre","templatePost", and "phaseType" are defined')
            return '$pass'
    # Read the forced inputs
    pltSt=args[0].detrend('linear') # Have to atleast detrend for cross-correlation to work
    pickSet=args[1]
    phaseType=kwargs['phaseType']
    # If the stream or picks are empty, nothing to do
    if len(pltSt)==0:
        return '$pass'
    if len(pickSet)==0:
        print('No picks have been placed')
        return '$pass'
    # Gather the template to be used, taken from the first station with wanted phase type
    if phaseType not in pickSet[:,1]:
        print('No picks of phase type '+phaseType)
        return '$pass'
    else:
        wantArgs=np.where(pickSet[:,1]==phaseType)[0]
    # Sort by increasing pick time, and select the first station which is present in the stream... 
    # ...and has a vertical component
    stas=np.array([tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.location for tr in pltSt])
    chas=np.array([tr.stats.channel[-1] for tr in pltSt])
    # Check to see that atleast two vertical channels are present
    if len(np.where(chas=='Z')[0])<2:
        print('Atleast two vertical traces are required for alignment')
        return '$pass'
    tempSta=''
    sortArgs=wantArgs[np.argsort(pickSet[wantArgs,2].astype(float))]
    for arg in sortArgs:
        # If station is present
        if pickSet[arg,0] in stas:
            # If channel is present
            if 'Z' in chas[np.where(stas==pickSet[arg,0])]:
                tempSta=pickSet[arg,0]
                pickTime=float(pickSet[arg,2])
                break
    # If no picks with the given phase had data, pass, and let user know
    if tempSta=='':
        print('No stations are present with phase type '+phaseType)
        return '$pass'
    # Gather the template to be used
    foundTemplate=False
    for arg in np.where((stas==tempSta)&(chas=='Z'))[0]:
        tempTr=pltSt[arg].slice(UTCDateTime(pickTime+kwargs['templatePre']),UTCDateTime(pickTime+kwargs['templatePost']))
        if tempTr.stats.npts*tempTr.stats.delta<0.5*(kwargs['templatePost']-kwargs['templatePre']):
            continue
        foundTemplate=True
        break
    # If no trace had alteast half of the wanted template, skip
    if not foundTemplate:
        print('The first pick of type '+phaseType+' which is on station '+tempSta+' did not have half'+
              ' of the desired template length')
        return '$pass'
    # Loop through all stations and get their offsets
    stas,offsets=getVertXCorOffsets(tempTr,pltSt.copy())
    missedStas=[]
    # Apply the offsets to the traces
    for tr in pltSt:
        aSta=tr.stats.network+'.'+tr.stats.station+'.'+tr.stats.location
        if aSta in stas:
            tr.stats.starttime-=offsets[stas.index(aSta)]
        else:
            missedStas.append(aSta)
    if len(missedStas)>0:
        print('The stations: '+str(np.unique(missedStas))+' were not time shifted')
    return pltSt
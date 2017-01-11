import numpy as np
from obspy import read, UTCDateTime
from obspy import Stream as EmptyStream
import os

# Read in all the start and stop times of the files
def getArchiveAvail(archiveDir):
    # Make a list of event times from the folder, for easier searching later
    fileTimes,files=[],sorted(os.listdir(archiveDir))
    for aFile in files:
        acceptFileTypes=['seed','mseed','miniseed']
        # Skip if not the proper file name
        if aFile.split('.')[-1] not in acceptFileTypes:
            continue
        try:
            # Remove the possible file endings
            aFileTimeString=aFile.split('_')[-1]
            for aStr in acceptFileTypes:
                aFileTimeString=aFileTimeString.replace('.'+aStr,'')
            # Add the file time
            fileTimes.append((UTCDateTime().strptime(aFileTimeString,'%Y%m%d.%H%M%S.%f')).timestamp)
        except:
            print aFileTimeString+' does not match the format %Y%m%d.%H%M%S.%f'
            continue
    # Sort the array by time
    fileTimes,files=np.array(fileTimes,dtype=float),np.array(files,dtype=str)
    argSort=np.argsort(fileTimes)
    fileTimes,files=fileTimes[argSort],files[argSort]
    return files,fileTimes

# If the stream was not able to be merged, check to see if multiple sampling rates on the same channel...
# ... and remove the ones with the uncommon sampling rate
def RemoveOddRateTraces(stream):
    unqStaRates=[] # Array to hold rates, per station
    rates,stas=[],[]
    for tr in stream:
        if tr.stats.station+'.'+str(tr.stats.delta) not in unqStaRates:
            unqStaRates.append(tr.stats.station+'.'+str(tr.stats.delta))
            rates.append(tr.stats.delta)
            stas.append(tr.stats.station)
    # ...figure out which station has two rates 
    unqRate,countRate=np.unique(rates,return_counts=True)
    if len(unqRate)==1:
        print 'merge will fail, not issue of multiple sampling rates on same station'
    else:
        # ... and remove the traces with less common rates
        unqSta,countSta=np.unique(stas,return_counts=True)
        rmStas=unqSta[np.where(countSta!=1)]
        rmRates=unqRate[np.where(unqRate!=(unqRate[np.argmax(countRate)]))]
        trimRateStream=EmptyStream()
        for tr in stream:
            if tr.stats.station in rmStas and tr.stats.delta in rmRates:
                continue
            trimRateStream+=tr
        print 'stations:',str(rmStas),'had some traces removed (duplicate rates same channel)'
        stream=trimRateStream
    return stream

# Given two timestamps, extract all information...
# fileTimes represents the start time of the archive files
def extractDataFromArchive(archiveDir,t1,t2,fileNames,fileTimes,
                           archiveFileLen=1800,fillVal=None,wantedStaChas=[['*','*']]):
    # Read the last file to see how long it goes on for
    lastTime=fileTimes[-1]+archiveFileLen
    # Catch the case where this where the asked time range is completely outside the archive data availability
    if t1>lastTime or t2<fileTimes[0]:
        print 'Archive contains data between '+str(UTCDateTime(fileTimes[0]))+' and '+str(UTCDateTime(lastTime)) 
        return EmptyStream()
    # Figure out what set of files are wanted
    firstIdx,secondIdx=np.interp(np.array([t1,t2]),fileTimes,np.arange(len(fileTimes)),
                                 left=0,right=len(fileTimes)-1).astype(int)
    stream=EmptyStream()
    # Read in all of the information
    for aFile in fileNames[firstIdx:secondIdx+1]:
        aStream=read(archiveDir+'/'+aFile)
        for aSta,aCha in wantedStaChas:
            stream+=aStream.select(station=aSta,channel=aCha)
    # Merge traces which are adjacent
    try:
        stream.merge(method=1,fill_value=fillVal)
    except:
        stream=RemoveOddRateTraces(stream)
        stream.merge(method=1,fill_value=fillVal)
    # Trim to wanted times
    stream.trim(UTCDateTime(t1),UTCDateTime(t2))
    return stream

# Return the UTCDateTime from the forced file naming convention
def getTimeFromFileName(fileName):
    timeStr=fileName.split('_')[1].replace('.'+fileName.split('.')[-1],'')
    return UTCDateTime().strptime(timeStr,'%Y%m%d.%H%M%S.%f')
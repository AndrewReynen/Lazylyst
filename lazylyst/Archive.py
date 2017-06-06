# Author: Andrew.M.G.Reynen
from __future__ import print_function, division
import os
import sys
if sys.version_info[0]==2:
    from scandir import scandir
else:
    from os import scandir
    
import numpy as np
from obspy import read, UTCDateTime
from obspy import Stream as EmptyStream
from PyQt5 import QtWidgets, QtCore

# If the stream was not able to be merged, check to see if multiple sampling rates on the same channel...
# ... and remove the ones with the uncommon sampling rate
def RemoveOddRateTraces(stream):
    unqStaRates=[] # Array to hold rates, per channel
    rates,chas=[],[]
    for tr in stream:
        anID=tr.stats.station+'.'+tr.stats.channel+'.'+str(tr.stats.delta)
        if anID not in unqStaRates:
            unqStaRates.append(anID)
            rates.append(tr.stats.delta)
            chas.append(tr.stats.station+'.'+tr.stats.channel)
    # ...figure out which station has two rates 
    unqRate,countRate=np.unique(rates,return_counts=True)
    if len(unqRate)==1:
        print('merge will fail, not issue of multiple sampling rates on same station')
    else:
        # ... and remove the traces with less common rates
        unqCha,countCha=np.unique(chas,return_counts=True)
        rmChas=unqCha[np.where(countCha!=1)]
        rmRates=unqRate[np.where(unqRate!=(unqRate[np.argmax(countRate)]))]
        trimRateStream=EmptyStream()
        for tr in stream:
            if tr.stats.station+'.'+tr.stats.channel in rmChas and tr.stats.delta in rmRates:
                continue
            trimRateStream+=tr
        print('station.channel:',str(rmChas),'had some traces removed (duplicate rates same channel)')
        stream=trimRateStream
    return stream

# Given two timestamps, extract all information...
# fileTimes contains [startTime,endTime] of the archive files
def extractDataFromArchive(t1,t2,fileNames,fileTimes,wantedStaChas=[['*','*']]):
    # Return nothing if there is no data
    if len(fileTimes)==0:
        return EmptyStream()
    # Catch the case where this where the asked time range is completely outside the archive data availability
    if t1>fileTimes[-1,1] or t2<fileTimes[0,0]:
        return EmptyStream()
    # Figure out what set of files are wanted
    collectArgs=np.where((fileTimes[:,0]<=t2)&(fileTimes[:,1]>=t1))[0]
    stream=EmptyStream()
    # Read in all of the information
    for aFile in fileNames[collectArgs]:
        aStream=read(aFile)
        for aSta,aCha in wantedStaChas:
            stream+=aStream.select(station=aSta,channel=aCha)
    # Merge traces which are adjacent
    try:
        stream.merge(method=1)
    except:
        stream=RemoveOddRateTraces(stream)
        stream.merge(method=1)
    # If any trace has masked values, split
    if True in [isinstance(tr.data, np.ma.masked_array) for tr in stream]:
        stream=stream.split()
    # Trim to wanted times
    stream.trim(UTCDateTime(t1),UTCDateTime(t2))
    return stream
    
# Get a list of all files of the accepted extension types, and their metadata
def getDirFiles(mainDir,acceptedExtensions):
    metaData=[] # The returned metadata [path,mtime,ctime,fileSize]
    # Check first to see that the folder exists, return nothing otherwise
    if not os.path.isdir(mainDir):
        return metaData
    # The directories yet to be scanned
    toScanDirs=[mainDir]
#    print('Scanning archive directory for any changes...')
    while len(toScanDirs)!=0:
        toAddToScan=[] # Directories to be found in this iteration
        for aDir in toScanDirs:
            for entry in scandir(aDir):
                # If this is a directory, scan it later
                if entry.is_dir():
                    toAddToScan.append(entry.path)
                    continue
                # Add to the file metadata list if is an accepted file type
                if entry.name.split('.')[-1] in acceptedExtensions:
                    aStat=entry.stat()
                    metaData.append([entry.path,aStat.st_mtime,
                                     aStat.st_ctime,aStat.st_size])
        # Add all of the new directories which were found
        toScanDirs=toAddToScan
#    print('...scan complete')
    return metaData

# Get the previously loaded archives file metadata and start/end times
def getPrevArchive(mainDir):
    try:
        meta=np.load(mainDir+'/lazylystArchiveMeta.npy')
        times=np.load(mainDir+'/lazylystArchiveTimes.npy')
        return meta,times
    except:
        return np.empty((0,4)),np.empty((0,2))
    
# Empty class to be able to pass objects to the progress widget
class ValueObj(object):
    def __init__(self):
        self.value=[]

# Read in all the start and stop times of the files
def getArchiveAvail(archDir,acceptFileTypes=['seed','miniseed','mseed']):
    # Get the currently present files metadata
    curMeta=getDirFiles(archDir,acceptFileTypes)
    curMeta=np.array(curMeta,dtype=str)
    curTimes=np.zeros((len(curMeta),2))
    # If there are no files in archDir
    if len(curMeta)==0:
        return np.array([]),curTimes
    # Get the previous files
    prevMeta,prevTimes=getPrevArchive(archDir)
    # If the arrays are already exactly the same, do not bother updating
    if np.array_equal(prevMeta,curMeta):
        return prevMeta[:,0],prevTimes
    # See which files are common among current and previous metadata (check, which may be added to load)...
    prevFiles=list(prevMeta[:,0])
    if len(prevMeta)!=0:
        checkIdxs=[[i,prevFiles.index(item)] for i, item in enumerate(curMeta[:,0]) if item in set(prevFiles)]
    else:
        checkIdxs=[]
    checkIdxs=np.array(checkIdxs)
    # ...as well as which files were not previously present (load)
    if len(checkIdxs)==0:
        loadIdxs=list(range(len(curMeta)))
    else:
        loadIdxs=[i for i in range(len(curMeta)) if i not in checkIdxs[:,0]]
    # Set the current time to be the previous times (where present) by default
    if len(checkIdxs)!=0:
        curTimes[checkIdxs[:,0]]=prevTimes[checkIdxs[:,1]]
    # See which current files need to be loaded
    loadIdxs+=[i for i,j in checkIdxs if not np.array_equal(curMeta[i],prevMeta[j])]
    loadIdxs=np.array(loadIdxs,dtype=int)
    # Go get all of these times
    holder=ValueObj()
    if len(loadIdxs)!=0:
        bar=ArchLoadProgressBar(holder,curMeta[loadIdxs,0])
        bar.exec_() 
        times=np.array(holder.value)
        # As the new times loading could have been canceled, update just the ones which were updated
        curTimes[loadIdxs[:len(times)]]=times
    # Keep the times which are not still [0,0]
    keepIdxs=np.where((curTimes[:,0]!=0)|(curTimes[:,1]!=0))[0]
    curMeta=curMeta[keepIdxs]
    curTimes=curTimes[keepIdxs]
    
    # Finally save the new metadata and times...
    np.save(archDir+'/lazylystArchiveMeta',curMeta)
    np.save(archDir+'/lazylystArchiveTimes',curTimes)
    # ...and return the file names and times
    return curMeta[:,0],curTimes

# Progress bar for the archive...
class ArchLoadProgressBar(QtWidgets.QDialog):
    def __init__(self,holder,toReadFiles, parent=None, total=100):
        super(ArchLoadProgressBar, self).__init__(parent)
        self.holder=holder
        # Set up values to for scanning file times
        self.files=toReadFiles
        self.nFiles=float(len(self.files))
        self.fileMinMaxs=[]
        self.nextFileIdx=0
        # Set up progress bar size and min/max values
        self.resize(300,40)
        self.progressbar = QtWidgets.QProgressBar()
        self.progressbar.setMinimum(1)
        self.progressbar.setMaximum(total)
        # Add cancel button
        self.button = QtWidgets.QPushButton('Cancel')
        self.button.clicked.connect(self.cancelLoad)
        main_layout = QtWidgets.QVBoxLayout()
        # Add widgets and text to the  layout
        main_layout.addWidget(self.progressbar)
        main_layout.addWidget(self.button)
        self.setLayout(main_layout)
        self.setWindowTitle('Loading archive changes...')
        # Add a timer and start loading
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.getFileLims)
        self.timer.start(5) # 5 millisecond interval
    
    # Stop the timer from loading files
    def cancelLoad(self):
        self.timer.stop()
        self.holder.value=self.fileMinMaxs
        print(len(self.fileMinMaxs),' archive files were updated')
        self.close()

    # If closed, treat as canceled
    def closeEvent(self, event):
        if self.timer.isActive():
            self.cancelLoad()

    # Get the earliest and latest time data exists in the wanted files
    def getFileLims(self):
        # Stop if no more files to load
        if self.nextFileIdx>=self.nFiles:
            self.cancelLoad()
            return
        nextFile=self.files[self.nextFileIdx]
        st=read(nextFile,headonly=True,format='MSEED')
        stats=[tr.stats for tr in st]
        # Get min and max times from file
        minTime=np.min([stat.starttime for stat in stats]).timestamp
        maxTime=np.max([stat.endtime for stat in stats]).timestamp
        # Get a measure of progress and update the GUI
        perc=int(100*(self.nextFileIdx+1)/self.nFiles)
        if perc>self.progressbar.value():
            self.progressbar.setValue(perc)
        # Update the GUI every Xth loop
        if self.nextFileIdx%10==0:
            QtWidgets.qApp.processEvents()
        # Update the index, and add this min/max time
        self.nextFileIdx+=1
        self.fileMinMaxs.append([minTime,maxTime])

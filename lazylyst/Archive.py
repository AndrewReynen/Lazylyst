# Author: Andrew.M.G.Reynen
from __future__ import print_function,division
import os
import sys
import ctypes as C
if sys.version_info[0]==2:
    from scandir import scandir
else:
    from os import scandir
    
import numpy as np
from obspy.core.stream import read
from obspy.core.stream import Stream as EmptyStream
from obspy.core.utcdatetime import UTCDateTime
from obspy.io.mseed.headers import clibmseed,VALID_CONTROL_HEADERS,SEED_CONTROL_HEADERS
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
    # Catch the case where the asked time range is completely outside the archive data availability
    if t1>fileTimes[-1,1] or t2<fileTimes[0,0]:
        return EmptyStream()
    # Figure out what set of files are wanted
    collectArgs=np.where((fileTimes[:,0]<=t2)&(fileTimes[:,1]>=t1))[0]
    stream=EmptyStream()
    flagged=False
    # Read in all of the information
    for aFile in fileNames[collectArgs]:
        # Flag to user if the archive structure has changed
        if not os.path.exists(aFile):
            flagged=True
            continue
        aStream=read(aFile)
        for aSta,aCha in wantedStaChas:
            stream+=aStream.select(station=aSta,channel=aCha)
    if flagged: 
        print('Archive structure as changed, reload the current archive')
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
#    print('Scanning archive directory for changes...')
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
def getArchiveAvail(archDir,acceptFileTypes=['seed','miniseed','mseed'],showBar=True):
    # Get the currently present files metadata
    curMeta=getDirFiles(archDir,acceptFileTypes)
    curMeta=np.array(curMeta,dtype=str)
    curTimes=np.zeros((len(curMeta),2))
    # If there are no files in archDir
    if len(curMeta)==0:
        return np.array([]),curTimes
    # Get the previously loaded archive metadata if it exists
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
    # Go get all of these times ## ##
    holder=ValueObj() 
    if len(loadIdxs)!=0:
        # Have the option to show the progress bar, or run all and now show progress
        bar=ArchLoadProgressBar(holder,curMeta[loadIdxs,0],useTimer=showBar)
        if showBar:
            bar.exec_()
        else:
            while len(holder.value)==0:
                bar.getFileLims()
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
    def __init__(self,holder,toReadFiles,useTimer=True, parent=None):
        super(ArchLoadProgressBar, self).__init__(parent)
        self.holder=holder
        # Set up values to for scanning file times
        self.files=toReadFiles
        self.nFiles=float(len(self.files))
        self.fileMinMaxs=[]
        self.nextFileIdx=0
        # Marker if the quick MSEED reading fails
        self.quickReadFail=False
        # Set up progress bar size and min/max values
        self.resize(300,40)
        self.progressbar = QtWidgets.QProgressBar()
        self.progressbar.setMinimum(1)
        self.progressbar.setMaximum(100)
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
        if useTimer:
            self.timer.timeout.connect(self.getFileLims)
            self.timer.start(5) # 5 millisecond interval
    
    # Stop the timer from loading files
    def cancelLoad(self):
        self.timer.stop()
        self.holder.value=self.fileMinMaxs
        print(len(self.fileMinMaxs),'archive files were updated')
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
        # Try the quick read function
        if not self.quickReadFail:
            try:
                startEnds=getMseedStartEnds(nextFile)
                minTime,maxTime=np.min(startEnds[:,0]),np.max(startEnds[:,1])
            except:
                print('Quick MSEED reading failed on file: '+nextFile)
                self.quickReadFail=True
        if self.quickReadFail:
            try:
                st=read(nextFile,headonly=True,format='MSEED')
                stats=[tr.stats for tr in st]
                # Get min and max times from file
                minTime=np.min([stat.starttime for stat in stats]).timestamp
                maxTime=np.max([stat.endtime for stat in stats]).timestamp
            except:
                print('Regular MSEED reading failed on file: '+nextFile)
                minTime,maxTime=0,0 # Assign 0,0 to be removed later
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

# Functions used for getMseedStartEnds
def passFunc(*args):
    pass
def isdigit(x):
    return True if (x - ord('0')).max() <= 9 else False

# Read the just start and end time from all traces in MSEED
def getMseedStartEnds(aFile):
    # Read file
    bfr_np = np.fromfile(aFile, dtype=np.int8)
 
    # Parameters wanted for reading just the header
    unpack_data,verbose,offset=0,0,0
    details,selections=False,None
    reclen,header_byteorder=-1,-1

    # Check if starting position of data read should change
    while True:
        if (isdigit(bfr_np[offset:offset + 6]) is False) or \
                (bfr_np[offset + 6] not in VALID_CONTROL_HEADERS):
            msg = 'Not a valid (Mini-)SEED file'
            raise Exception(msg)
        elif bfr_np[offset + 6] in SEED_CONTROL_HEADERS:
            # Get the record length
            try:
                record_length = pow(2, int(''.join([chr(_i) for _i in bfr_np[19:21]])))
            except ValueError:
                record_length = 4096
            offset += record_length
            continue
        break
    bfr_np = bfr_np[offset:]
    buflen = len(bfr_np)

    # Make useless functions to accomodate clibmseed.readMSEEDBuffer requirements
    alloc_data = C.CFUNCTYPE(C.c_longlong, C.c_int, C.c_char)(passFunc)
    log_print = C.CFUNCTYPE(C.c_void_p, C.c_char_p)(passFunc)

    # Read the data with C function
    inputs=[bfr_np, buflen, selections, C.c_int8(unpack_data),
            reclen, C.c_int8(verbose), C.c_int8(details), header_byteorder,
            alloc_data,log_print,log_print]
    # Allow for different versions of obspy
    try:
        lil = clibmseed.readMSEEDBuffer(*inputs)
    except:
        lil = clibmseed.readMSEEDBuffer(*inputs[:-2])
        
    
    # Read first section of the miniseed
    current_id = lil.contents
    timeInfo=np.zeros((0,2),dtype=float)
    # Loop over each NSLC
    while True:
        try:
            current_segment = current_id.firstSegment.contents
        except ValueError:
            break
        # Loop over traces for this NSLC
        while True:
            # Get the starttime and duration
            startStr=str(current_segment.starttime)
            startTime,duration=startStr[:-6]+'.'+startStr[-6:],(1./current_segment.samprate)*(current_segment.samplecnt)
            try:
                current_segment = current_segment.next.contents
            except ValueError:
                # Append these values to array
                timeInfo=np.vstack((timeInfo,np.array([startTime,duration],dtype=float)))
                break
        try:
            current_id = current_id.next.contents
        except ValueError:
            break

    # Remove the mseed info from memory
    clibmseed.lil_free(lil)
    del lil
    
    # Return start and end times
    if len(timeInfo)==0:
        return timeInfo
    else:
        # Make the second entry the end time (start time + duration)
        timeInfo[:,1]=np.sum(timeInfo,axis=1)
        return timeInfo
# Copyright Andrew.M.G.Reynen
from obspy import Stream, read_inventory
from obspy.core.inventory import Inventory
from CustomFunctions import getTimeFromFileName
from copy import deepcopy
from future.utils import iteritems
import importlib
import os
import numpy as np
import sys
if sys.version_info.major == 3:
    unicode = str

# Default Hot Variables
def initHotVar():
    hotVar={
    'stream':HotVar(tag='stream',val=Stream(),dataType=type(Stream()),returnable=False,
                    tip='Raw trace data from archive for current event'),
    'pltSt':HotVar(tag='pltSt',val=Stream(),dataType=type(Stream()),
                   funcName='updateTraces',checkName='checkPltSt',
                    tip='Plotted trace data for current event'),
    'staSort':HotVar(tag='staSort',val=[],dataType=type(np.array([''])),
                     funcName='updatePage',checkName='checkStaSort',
                     tip='Station codes, order defines trace data widget ordering'),
    'curPage':HotVar(tag='curPage',val=0,dataType=int,
                     funcName='updateCurPage',
                     tip='Current page index'),
    'timeRange':HotVar(tag='timeRange',val=[0,1],dataType=list,
                       funcName='updateTimeRange',checkName='checkTimeRange',
                       tip='Time limits on the trace time widget'),
    'yTraceRanges':HotVar(tag='yTraceRanges',val=np.empty((0,2)),dataType=type(np.array([0.0])),
                       funcName='updateTraceRangesY',checkName='checkTraceRangesY',
                       tip='Y-limits on the trace data widgets'),
    'sourceTag':HotVar(tag='sourceTag',val='',dataType=str,
                       funcName='updateSource',checkName='checkSourceTag',
                       tip='Tag given to the current source'),
    'pickDir':HotVar(tag='pickDir',val='',dataType=str,
                     funcName='updatePickDir', checkName='checkPickDir',
                     tip='Pick directory path'),
    'pickFiles':HotVar(tag='pickFiles',val=[],dataType=type(np.array(['str'])), 
                       funcName='updatePickFiles',checkName='checkPickFileNames',
                       tip='File names contained within the pick directory'),
    'pickFileTimes':HotVar(tag='pickFileTimes',val=[],dataType=type(np.array([0.0])),returnable=False,
                           tip='Timestamps contained in the pick file names'),   
    'curPickFile':HotVar(tag='curPickFile',val='',dataType=str,
                         funcName='updateCurPickFile',checkName='checkCurPickFile',
                         tip='Filename of the currently selected pick file'),
    'pickSet':HotVar(tag='pickSet',val=np.empty((0,3)),dataType=type(np.array([0.0])),
                     funcName='updatePagePicks',checkName='checkPickSet',
                     tip='Picks assigned to the current pick file'),
    'pickMode':HotVar(tag='pickMode',val='',dataType=str,
                      tip='Current pick phase in use'),
    'tracePenAssign':HotVar(tag='tracePenAssign',val={},dataType=dict,
                            funcName='updateTracePen',checkName='checkTracePenAssign',
                            tip='Pen values assigned to traces data on a channel basis'),
    'traceBgPenAssign':HotVar(tag='traceBgPenAssign',val={},dataType=dict,
                            funcName='updateTraceBackground',checkName='checkStaColAssign',
                            tip='Colors assigned to trace data widget backgrounds, station basis'),
    'mapStaPenAssign':HotVar(tag='mapStaPenAssign',val={},dataType=dict,
                            funcName='updateMapStations',checkName='checkStaColAssign',
                            tip='Colors assigned to stations'),
    'mapCurEve':HotVar(tag='mapCurEve',val=np.empty((0,5)),dataType=type(np.array([0.0])),
                       funcName='updateMapCurEve',checkName='checkEveArr',
                       tip='Events plotted in the foreground of the map widget'),
    'mapPrevEve':HotVar(tag='mapPrevEve',val=np.empty((0,5)),dataType=type(np.array([0.0])),
                       funcName='updateMapPrevEve',checkName='checkEveArr',
                       tip='Events plotted in the background of the map widget'),
    'archDir':HotVar(tag='archDir',val='',dataType=str,
                     funcName='updateArchive',checkName='checkArchDir',
                     tip='Archive directory path'),
    'archFiles':HotVar(tag='archFiles',val=[],dataType=type(np.array([0.0])),returnable=False,
                       tip='File paths contained within the archive directory'),
    'archFileTimes':HotVar(tag='archFileTimes',val=[],dataType=type(np.array([0.0])),returnable=False,
                           tip='Earliest and latest timestamp contained in the archive files'),   
    'curTraceSta':HotVar(tag='curTraceSta',val='',dataType=str,returnable=False,
                         tip='Station code of the currently hovered over trace data widget'),
    'curTracePos':HotVar(tag='curTracePos',val=[0,0],dataType=list,returnable=False,
                         tip='Mouse position [X,Y] of the currently hovered over trace data widget'),
    'staFile':HotVar(tag='staFile',val='',dataType=str,
                     funcName='updateStaMeta',checkName='checkStaFile',
                     tip='Station file path'),
    'staLoc':HotVar(tag='staLoc',val=np.empty((0,4)),dataType=type(np.array([0.0])),returnable=False,
                     tip='Station locations'),
    'staXml':HotVar(tag='staXml',val=Inventory(networks=[],source='Lazylyst'),
                    dataType=type(Inventory(networks=[],source='Lazylyst')),returnable=False,
                     tip='Station metadata'),
    'curMapSta':HotVar(tag='curMapSta',val='',dataType=str,returnable=False,
                       tip='Last double clicked station on the map sta widget'),
    'mainPath':HotVar(tag='mainPath',val='',dataType=str,returnable=False,
                      tip='Path which contains Lazylst'),
    'image':HotVar(tag='image',val={'data':np.zeros((1,1)),'tDelta':1,'t0':0},dataType=dict,
                   funcName='updateImage',checkName='checkImage',
                   tip='Currently plotted image on the image widget'),
    'customDict':HotVar(tag='customDict',val={},dataType=dict,
                        tip='Dictionary to hold arbitrary variables'),
    }
    return hotVar

# Class for hot variables, which have defined update functions
class HotVar(object):
    def __init__(self,tag=None,val=None,
                 dataType=None,func=None,
                 funcName=None,returnable=True,
                 check=None,checkName=None,tip=''):
        self.tag=tag
        self.val=val
        self.dataType=dataType
        self.func=func # Function which is called upon update
        self.funcName=funcName # Name of the function within $main to be called
        self.returnable=returnable # If this hot variable is allowed to be returned for update
        self.check=check # Function used to check the validity of the input data
        self.checkName=checkName # Name of the check function within $main
        self.tip=tip # Short description of the hot variable
    
    # Return a deep copy of the objects value
    def getVal(self):
        # If a list has no entries, return the default (empty list) instead of the deepcopy
        if self.dataType in [list,type(np.array([0.0]))]:
            if len(self.val)==0:
                return initHotVar()[self.tag].val
        # The station xml file can take a while to copy...
        ## Figure out way to pass it without worrying about user edits?? ##
        if self.tag=='staXml':
            return self.val
        elif self.tag=='stream':
            return self.val.copy()
        else:
            return deepcopy(self.val)
        
    # Call the specified function to update the hot variable value
    def update(self):
        if self.func==None:
            return
        self.func()
    
    # Call the check function to ensure the proposed return value makes sense
    def check(self,main):
        if self.check==None:
            return True
        return self.check(main)
    
    # Link a hot variable to its pre-defined update and check functions
    def linkToFunction(self,main):
        # If there is no update function, skip
        if self.funcName==None:
            return
        # Link to the check function first (if present)
        if self.checkName==None:
            linkCheck=True
        else:
            try:
                self.check=getattr(importlib.import_module('HotVariables'),self.checkName)
                linkCheck=True
            except:
                linkCheck=False
                print(self.tag+' check function did not load from $main.'+self.checkName)
        # If the link to the check function passed, link to the update function
        if linkCheck:
            try:
                self.func=getattr(main,self.funcName)
            except:
                print(self.tag+' update function did not load from $main.'+self.funcName)

# Ensure that the new plot stream has the same combination of stations as stream
def checkPltSt(main,pltSt):
    oStas=np.unique([tr.stats.station for tr in main.hotVar['stream'].val])
    nStas=np.unique([tr.stats.station for tr in pltSt])
    if not np.array_equal(np.sort(oStas),np.sort(nStas)):
        print('The return pltSt does not have all and only the stations present in stream')
        return False
    return True
    
# Ensure that the new station sorting doesn't have stations for which there are no traces
def checkStaSort(main,newSort):
    trStas=np.unique([tr.stats.station for tr in main.hotVar['pltSt'].val])
    if not np.array_equal(np.sort(trStas),np.sort(newSort)):
        print('The return staSort does not have all and only the station present in pltSt')
        return False
    return True
    
# Ensure that the limits are in the proper order, can be floats, and just contains two values
def checkTimeRange(main,timeRange):
    try:
        np.array(timeRange,dtype=float)
    except:
        print('timeRange values must be numbers (timestamp (s))')
        return False
    if len(timeRange)!=2:
        print('For timeRange, two values are required to specify the time range, got '+str(len(timeRange)))
        return False
    elif timeRange[0]>=timeRange[1]:
        print('For timeRange, the second (right) limit must be greater than the first limit')
        return False
    return True

# Ensure that limits are in proper order, can be floats, and have as many entries as there are staWidgets
def checkTraceRangesY(main,yRanges):
    try:
        yRanges=np.array(yRanges,dtype=float)
    except:
        print('yTraceRanges values must be numbers')
        return False
    if len(yRanges.shape)!=2 or len(yRanges)!=len(main.staWidgets):
        print('yTraceRanges must be two dimensional, and must have length=staPerPage('+
              str(main.pref['staPerPage'].val)+')')
        return False
    elif np.sum(np.diff(yRanges,axis=1)<=0)!=0:
        print('For yTraceRanges, limits for all trace widgets must increase ie. [low,high]')
        return False
    return True

# Ensure that the specified tag actually exists
def checkSourceTag(main,tag):
    if tag not in main.saveSource.keys():
        print('The sourceTag '+tag+' is not currently a saved source')
        return False
    return True

# Ensure that the supplied pick directory actually exists (make one if it does not)
def checkPickDir(main,pickDir):
    if not os.path.exists(pickDir):
        try:
            print('The pickDir did not exist, folder has been created')
            os.makedirs(pickDir)
        except:
            print('The pickDir did not exist, supplied string not compatible as a directory name')
            return False
    return True

# Ensure that all of the returned pick files conform to the proper name
def checkPickFileNames(main,pickFiles):
    passTest=True
    for i,aFile in enumerate(pickFiles):
        splitFile=aFile.split('_')
        if len(splitFile)!=2 or 'picks'!=aFile.split('.')[-1]:
            print(aFile+' does not match format IntegerID_%Y%m%d.%H%M%S.%f.picks')
            passTest=False
            continue
        try:
            getTimeFromFileName(aFile)
            int(splitFile[0])
            continue
        except:
            print(aFile+' does not match format IntegerID_%Y%m%d.%H%M%S.%f.picks')
            passTest=False
    if len(np.unique(pickFiles))!=len(pickFiles):
        print('Pick file names were non unique')
        passTest=False
    return passTest

# Ensure that the new pick file has the proper naming convention
def checkCurPickFile(main,pickFile):
    # If the pick directory has not been set, don't try
    if main.hotVar['pickDir'].val=='':
        print('The pickDir has not been set')
        return False
    # If the user wants to return to a blank screen, let them
    if pickFile=='':
        return True
    # If not already present, check its name
    if pickFile not in main.hotVar['pickFiles'].val:
        if not checkPickFileNames(main,[pickFile]):
            return False
    return True

# Ensure that the pick set has the proper dimensions and data types [str,str,float] (although held as string)
def checkPickSet(main,pickSet):
    if len(pickSet.shape)!=2:
        print('The pickSet must be 2 dimensional')
        return False
    elif pickSet.shape[1]!=3:
        print('The pickSet must have 3 columns')
        return False
    try:
        pickSet[:,:2].astype(str)
        pickSet[:,2].astype(float)
    except:
        print('The pickSet contains [station,pickType,timestamp(s)]')
        return False
    return True

# Ensure that the returned pen assignment (for traces) dictionary is holding the right data types
def checkTracePenAssign(main,penAssign):
    # Check to see that each returned value is a list
    for key,val in iteritems(penAssign):
        if type(val)!=list:
            print('For all tracePenAssign returned key:value pairs, the value should be a list')
            return False
        # Each entry (channel) in the list should be a string, and <= 3 characters long
        for entry in val:
            if type(entry) not in [str,np.string_,np.str_]:
                print('Returned tracePenAssign, lists should only contain strings, got type '+str(type(entry)))
                return False
            elif len(entry)>3:
                print('Returned tracePenAssign, list entries refer to channels, which are max 3 characters long')
                return False
    return True

# Ensure that the returned pen assignment (for stations) dictionary is holding the right data types
def checkStaColAssign(main,colAssign):
    # Check to see that each returned value is a list
    for key,val in iteritems(colAssign):
        if type(val)!=list:
            print('For all traceBgPenAssign/mapStaPenAssign returned key:value pairs, the value should be a list')
            return False
        # Each entry (station) in the list should be a string, and <= 5 characters long
        for entry in val:
            if type(entry) not in [str,np.string_,np.str_]:
                print('Returned traceBgPenAssign/mapStaPenAssign, lists should only contain strings, got type '+str(type(entry)))
                return False
            elif len(entry)>5:
                print('Returned traceBgPenAssign/mapStaPenAssign, list entries refer to stations, which are max 5 characters long')
                return False
    return True
    
# Ensure that the current/previous event array is of the proper dimensions and datatype
def checkEveArr(main,eveArr):
    if len(eveArr.shape)!=2:
        print('The current/previous event array must be 2 dimensional')
        return False
    elif eveArr.shape[1]!=5:
        print('The current/previous event array must have 5 columns')
        return False
    try:
        eveArr.astype(float)
    except:
        print('The current/previous event array contains [ID,X,Y,Z,Timestamp(s)], which must all be numbers')
        return False
    return True

# Ensure that the archive directory exists  
def checkArchDir(main,archDir):
    if not os.path.isdir(archDir):
        print('Archive directory does not exist')
        return False
    return True
    
# Ensure that the station file exists and is in the proper format
def checkStaFile(main,staFile):
    # First see if the file exists
    if not os.path.isfile(staFile):
        print('Station file does not exist')
        return False
    # Ensure the to-read file is of proper format
    try:
        read_inventory(staFile,format='stationxml')
    except:
        print('Station file was not in xml format')
        return False
    return True

# Ensure that the image contains proper key words, and are in correct format
def checkImage(main,image):
    # Let user know if they gave useless keys
    acceptKeys=['data','t0','y0','tDelta','yDelta','label','cmapPos','cmapRGBA']
    givenKeys=image.keys()
    for key in givenKeys:
        if key not in acceptKeys:
            print('Image dict contained key '+key+' which is not used, accepted keys: '+str(acceptKeys))
    # Check to see that the forced key words are present
    keyFail=False
    for key in ['data','t0','tDelta']:
        if key not in givenKeys:
            print('Image key '+key+' was not contained in image dictionary')
            keyFail=True
    if keyFail:
        return False
    npArrType=type(np.array([0.0]))
    # Check to see that all arguments are of the proper type and dimensions
    for key,dtypes in [['data',[npArrType]],['t0',[float,np.float_,int,np.int_]],['y0',[float,np.float_,int,np.int_]],
                      ['tDelta',[float,np.float_,int,np.int_]],['yDelta',[float,np.float_,int,np.int_]],
                      ['label',[str,np.string_,np.str_,unicode]],['cmapPos',[npArrType]],['cmapRGBA',[npArrType]]]:
        if key in givenKeys:
            if type(image[key]) not in dtypes:
                print('Image key '+key+' has the expected '+str(dtypes[0])+' but was '+str(type(image[key])))
                keyFail=True
    if keyFail:
        return False
    # Check that the delta values are positive values
    for key in ['tDelta','yDelta']:
        if key in givenKeys:
            if image[key]<=0:
                keyFail=True
    if keyFail:
        print('Image delta values must be positive numbers')
        return False
    # Check the dimensions and contents of the numpy arrays
    if len(image['data'].shape)!=2 or 0 in image['data'].shape:
        print('Image data was not 2-dimensional, or had 0 length in at least one axis')
        keyFail=True
    if 'cmapPos' in givenKeys:
        if len(image['cmapPos'].shape)!=1 or image['data'].shape[0]<2:
            print('Image cmapPos was not 1-dimensional, or had length less than 2')
            keyFail=True
    if 'cmapRGBA' in givenKeys:
        if len(image['cmapRGBA'].shape)!=2 or image['data'].shape[0]<2:
            print('Image cmapRGBA was not 2-dimensional, or had length less than 2')
            keyFail=True
        elif image['cmapRGBA'].shape[1]!=4:
            print('Image cmapRGBA rows should contain length-4 arrays of the RGBA values')
            keyFail=True
        elif np.min(image['cmapRGBA'])<0 or np.max(image['cmapRGBA'])>255:
            print('Image cmapRGBA values should all be within the bounds [0,255]')
            keyFail=True
    if 'cmapRGBA' in givenKeys and 'cmapPos' in givenKeys:
        if image['cmapPos'].shape[0]!=image['cmapRGBA'].shape[0]:
            print('cmapPos and cmapRGBA must contain the same number of rows')
            keyFail=True
    if keyFail:
        return False
    return True
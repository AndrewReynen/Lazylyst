from obspy import Stream as emptyStream
from Archive import getTimeFromFileName
import importlib
import os
import numpy as np

# Default Hot Variables
def initHotVar():
    hotVar={
    'stream':HotVar(tag='stream',val=emptyStream(),dataType=type(emptyStream()),returnable=False),
    'pltSt':HotVar(tag='pltSt',val=emptyStream(),dataType=type(emptyStream()),
                   funcName='updateTraces',checkName='checkPltSt'),
    'staSort':HotVar(tag='staSort',val=[],dataType=type(np.array([''])),
                     funcName='updatePage',checkName='checkStaSort'),
    'curPage':HotVar(tag='curPage',val=0,dataType=int,
                     funcName='updateCurPage'),
    'timeRange':HotVar(tag='timeRange',val=[0,1],dataType=list,
                       funcName='updateTimeRange',checkName='checkTimeRange'),
    'sourceTag':HotVar(tag='sourceTag',val='',dataType=str,
                       funcName='updateSource',checkName='checkSourceTag'),
    'pickDir':HotVar(tag='pickDir',val='',dataType=str,
                     funcName='updatePickDir', checkName='checkPickDir'),
    'pickFiles':HotVar(tag='pickFiles',val=[],dataType=type(np.array(['str'])), 
                       funcName='updatePickFiles',checkName='checkPickFileNames'),
    'pickFileTimes':HotVar(tag='pickFileTimes',val=[],dataType=type(np.array([0.0])),returnable=False),   
    'curPickFile':HotVar(tag='curPickFile',val='',dataType=str,
                         funcName='updateCurPickFile',checkName='checkCurPickFile'),
    'pickSet':HotVar(tag='pickSet',val=np.empty((0,3)),dataType=type(np.array([0.0])),
                     funcName='updatePagePicks',checkName='checkPickSet'),
    'pickMode':HotVar(tag='pickMode',val='',dataType=str),
    'tracePenAssign':HotVar(tag='tracePenAssign',val={},dataType=dict,
                            funcName='updateTracePen',checkName='checkTracePenAssign'),
    'traceBgPenAssign':HotVar(tag='traceBgPenAssign',val={},dataType=dict,
                            funcName='updateTraceBackground',checkName='checkStaColAssign'),
    'mapStaPenAssign':HotVar(tag='mapStaPenAssign',val={},dataType=dict,
                            funcName='updateMapStations',checkName='checkStaColAssign'),
    'mapCurEve':HotVar(tag='mapCurEve',val=np.empty((0,5)),dataType=type(np.array([0.0])),
                       funcName='updateMapCurEve',checkName='checkEveArr'),
    'mapPrevEve':HotVar(tag='mapPrevEve',val=np.empty((0,5)),dataType=type(np.array([0.0])),
                       funcName='updateMapPrevEve',checkName='checkEveArr'),
    'archDir':HotVar(tag='archDir',val='',dataType=str,
                     funcName='updateArchive'),
    'archFiles':HotVar(tag='archFiles',val=[],dataType=list,returnable=False),
    'archFileTimes':HotVar(tag='archFileTimes',val=[],dataType=list,returnable=False),   
    'curTraceSta':HotVar(tag='curTraceSta',val='',dataType=str,returnable=False),
    'staFile':HotVar(tag='staFile',val='',dataType=str,
                     funcName='updateStaMeta'),  ## Add Check
    'staMeta':HotVar(tag='staMeta',val=np.empty((0,4)),dataType=type(np.array([0.0])),returnable=False),
    'curMapSta':HotVar(tag='curMapSta',val='',dataType=str,returnable=False),
    'mainPath':HotVar(tag='mainPath',val='',dataType=str,returnable=False),
    }
    return hotVar

# Class for hot variables, which have defined update functions
class HotVar(object):
    def __init__(self,tag=None,val=None,
                 dataType=None,func=None,
                 funcName=None,returnable=True,
                 check=None,checkName=None):
        self.tag=tag
        self.val=val
        self.dataType=dataType
        self.func=func # Function which is called upon update
        self.funcName=funcName # Name of the function within $main to be called
        self.returnable=returnable # If this hot variable is allowed to be returned for update
        self.check=check # Function used to check the validity of the input data
        self.checkName=checkName # Name of the check function within $main
        
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
                print self.tag+' check function did not load from $main.'+self.checkName
        # If the link to the check function passed, link to the update function
        if linkCheck:
            try:
                self.func=getattr(main,self.funcName)
            except:
                print self.tag+' update function did not load from $main.'+self.funcName

# Ensure that the new plot stream has the same combination of stations as stream
def checkPltSt(main,pltSt):
    oStas=np.unique([tr.stats.station for tr in main.hotVar['stream'].val])
    nStas=np.unique([tr.stats.station for tr in pltSt])
    if not np.array_equal(np.sort(oStas),np.sort(nStas)):
        print 'The return pltSt does not have all and only the station present in stream'
        return False
    return True
    
# Ensure that the new station sorting doesn't have stations for which there are no traces
def checkStaSort(main,newSort):
    trStas=np.unique([tr.stats.station for tr in main.hotVar['pltSt'].val])
    if not np.array_equal(np.sort(trStas),np.sort(newSort)):
        print 'The return staSort does not have all and only the station present in pltSt'
        return False
    return True
    
# Ensure that the limits are in the proper order, can be floats, and just contains two values
def checkTimeRange(main,timeRange):
    try:
        np.array(timeRange,dtype=float)
    except:
        print 'timeRange values must be numbers (timestamp (s))'
        return False
    if len(timeRange)!=2:
        print 'For timeRange, two values are required to specify the time range, got '+str(len(timeRange))
        return False
    elif timeRange[0]>=timeRange[1]:
        print 'For timeRange, the second (right) limit must be greater than the first limit'
        return False
    return True

# Ensure that the specified tag actually exists
def checkSourceTag(main,tag):
    if tag not in main.saveSource.keys():
        print 'The sourceTag '+tag+' is not currently a saved source'
        return False
    return True

# Ensure that the supplied pick directory actually exists (make one if it does not)
def checkPickDir(main,pickDir):
    if not os.path.exists(pickDir):
        try:
            print 'The pickDir did not exist, folder has been created'
            os.makedirs(pickDir)
        except:
            print 'The pickDir did not exist, supplied string not compatible as a directory name'
            return False
    return True

# Ensure that all of the returned pick files conform to the proper name
def checkPickFileNames(main,pickFiles):
    passTest=True
    for i,aFile in enumerate(pickFiles):
        splitFile=aFile.split('_')
        if len(splitFile)!=2 or 'picks'!=aFile.split('.')[-1]:
            print aFile+' does not match format IntegerID_%Y%m%d.%H%M%S.%f.picks'
            passTest=False
            continue
        try:
            getTimeFromFileName(aFile)
            pickFiles[i]=str(int(splitFile[0])).zfill(10)+'_'+splitFile[1]
            continue
        except:
            print aFile+' does not match format IntegerID_%Y%m%d.%H%M%S.%f.picks'
            passTest=False
    if len(np.unique(pickFiles))!=len(pickFiles):
        print 'Pick file names were non unique'
        passTest=False
    return passTest

# Ensure that the new pick file has the proper naming convention
def checkCurPickFile(main,pickFile):
    # If the pick directory has not been set, don't try
    if main.hotVar['pickDir'].val=='':
        print 'The pickDir has not been set'
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
        print 'The pickSet must be 2 dimensional'
        return False
    elif pickSet.shape[1]!=3:
        print 'The pickSet must have 3 columns'
        return False
    try:
        pickSet[:,:2].astype(str)
        pickSet[:,2].astype(float)
    except:
        print 'The pickSet contains [station,pickType,timestamp(s)]'
        return False
    return True

# Ensure that the returned pen assignment (for traces) dictionary is holding the right data types
def checkTracePenAssign(main,penAssign):
    # Check to see that each returned value is a list
    for key,val in penAssign.iteritems():
        if type(val)!=list:
            print 'For all tracePenAssign returned key:value pairs, the value should be a list'
            return False
        # Each entry (channel) in the list should be a string, and <= 3 characters long
        for entry in val:
            if type(entry) not in [str,np.string_]:
                print 'Returned tracePenAssign, lists should only contain strings, got type '+str(type(entry))
                return False
            elif len(entry)>3:
                print 'Returned tracePenAssign, list entries refer to channels, which are max 3 characters long'
                return False
    return True

# Ensure that the returned pen assignment (for stations) dictionary is holding the right data types
def checkStaColAssign(main,colAssign):
    # Check to see that each returned value is a list
    for key,val in colAssign.iteritems():
        if type(val)!=list:
            print 'For all traceBgPenAssign/mapStaPenAssign returned key:value pairs, the value should be a list'
            return False
        # Each entry (station) in the list should be a string, and <= 5 characters long
        for entry in val:
            if type(entry) not in [str,np.string_]:
                print 'Returned traceBgPenAssign/mapStaPenAssign, lists should only contain strings, got type '+str(type(entry))
                return False
            elif len(entry)>5:
                print 'Returned traceBgPenAssign/mapStaPenAssign, list entries refer to stations, which are max 5 characters long'
                return False
    return True
    
# Ensure that the current/previous event array is of the proper dimensions and datatype
def checkEveArr(main,eveArr):
    if len(eveArr.shape)!=2:
        print 'The current/previous event array must be 2 dimensional'
        return False
    elif eveArr.shape[1]!=5:
        print 'The current/previous event array must have 5 columns'
        return False
    try:
        eveArr.astype(float)
    except:
        print 'The current/previous event array contains [ID,X,Y,Z,Timestamp(s)], which must all be numbers'
        return False
    return True
    
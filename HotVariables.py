from obspy import Stream as emptyStream
import importlib
import numpy as np

# Default Hot Variables
def initHotVar():
    hotVar={
    'stream':HotVar(tag='stream',val=emptyStream(),dataType=type(emptyStream()),returnable=False),
    'pltSt':HotVar(tag='pltSt',val=emptyStream(),dataType=type(emptyStream()),
                   funcName='updateTraces'),
    'staSort':HotVar(tag='staSort',val=[],dataType=list,
                     funcName='updatePage',checkName='checkStaSort'),
    'curPage':HotVar(tag='curPage',val=0,dataType=int,
                     funcName='updateCurPage'),
    'sourceTag':HotVar(tag='sourceTag',val='',dataType=str,returnable=False),
    'pickDir':HotVar(tag='pickDir',val='',dataType=str,
                     funcName='updatePickDir'),
    'pickFiles':HotVar(tag='pickFiles',val=[],dataType=list,
                       funcName='updatePickFiles'),
    'pickFileTimes':HotVar(tag='pickFileTimes',val=[],dataType=list,returnable=False,
                           funcName='updatePickFileTimes'),   
    'curPickFile':HotVar(tag='curPickFile',val='',dataType=str,
                         funcName='updateEvent'),
    'pickSet':HotVar(tag='pickSet',val=np.empty((0,3)),dataType=np.array,
                     funcName='updatePagePicks'), # Must be in string format, row=[Sta,Type,TimeStamp]
    'pickMode':HotVar(tag='pickMode',val='',dataType=str),
    'tracePenAssign':HotVar(tag='tracePenAssign',val={},dataType=dict,
                            funcName='updateTracePen'),
    'archDir':HotVar(tag='archDir',val='',dataType=str,
                     funcName='updateArchive'),
    'archFiles':HotVar(tag='archFiles',val=[],dataType=list,returnable=False),
    'archFileTimes':HotVar(tag='archFileTimes',val=[],dataType=list,returnable=False),   
    'curSta':HotVar(tag='curSta',val='',dataType=str,returnable=False),
    'staFile':HotVar(tag='staFile',val='',dataType=str),
    'staMeta':HotVar(tag='staMeta',val=[],dataType=np.array,returnable=False)
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

# Ensure that the new station sorting doesn't have stations for which there are no traces
def checkStaSort(main,newSort):
    trStas=np.unique([tr.stats.station for tr in main.hotVar['pltSt'].val])
    if not np.array_equal(np.sort(trStas),np.sort(newSort)):
        print 'The return staSort does not have all and only the station present in pltSt'
        return False
    return True
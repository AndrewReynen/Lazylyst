from obspy import Stream as emptyStream
import numpy as np

# Default Hot Variables
def initHotVar():
    hotVar={
    'stream':HotVar(tag='stream',val=emptyStream(),dataType=type(emptyStream()),returnable=False),
    'pltSt':HotVar(tag='pltSt',val=emptyStream(),dataType=type(emptyStream()),
                   funcName='updatePage'),
    'staSort':HotVar(tag='staSort',val=[],dataType=list),
    'curPage':HotVar(tag='curPage',val=0,dataType=int,
                     funcName='updateCurPage'),
    'sourceTag':HotVar(tag='sourceTag',val='',dataType=str),
    'pickDir':HotVar(tag='pickDir',val='',dataType=str,
                     funcName='updatePickDir'),
    'pickFiles':HotVar(tag='pickFiles',val=[],dataType=list,
                       funcName='updatePickFiles'),
    'curPickFile':HotVar(tag='curPickFile',val='',dataType=str,
                         funcName='updateEvent'),
    'pickSet':HotVar(tag='pickSet',val=np.empty((0,3)),dataType=np.array,
                     funcName='updatePagePicks'), # Must be in string format, row=[Sta,Type,TimeStamp]
    'pickMode':HotVar(tag='pickMode',val='',dataType=str),
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
    def __init__(self,tag=None,val=None,preVal=None,
                 dataType=None,func=None,
                 funcName=None,returnable=True):
        self.tag=tag
        self.val=val
        self.preVal=preVal # Allows to call back the most recent action
        self.dataType=dataType
        self.func=func # Function which is called upon update
        self.funcName=funcName # Name of the function within $main to be called
        self.returnable=returnable # If this hot variable is allowed to be returned for update
        
    def update(self):
        if self.func==None:
            return
        self.func()
    
    # Link a hot variable to its pre-defined function
    def linkToFunction(self,main):
        if self.funcName==None:
            return
        try:
            self.func=getattr(main,self.funcName)
        except:
            print self.tag+' did not load from $main.'+self.funcName
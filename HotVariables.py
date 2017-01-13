from obspy import Stream as emptyStream
import numpy as np

# Default Hot Variables
def initHotVar():
    hotVar={
    'stream':HotVar(tag='stream',val=emptyStream(),dataType=type(emptyStream())),
    'pltSt':HotVar(tag='pltSt',val=emptyStream(),dataType=type(emptyStream()),
                   funcName='updatePage'),
    'staSort':HotVar(tag='staSort',val=[],dataType=list),
    'curPage':HotVar(tag='curPage',val=0,dataType=int),
    'sourceTag':HotVar(tag='sourceTag',val='',dataType=str),
    'pickDir':HotVar(tag='pickDir',val='',dataType=str,
                     funcName='updatePickFileList'),
    'pickFiles':HotVar(tag='pickFiles',val=[],dataType=list,returnable=False),
    'archDir':HotVar(tag='archDir',val='',dataType=str,
                     funcName='updateArchive'),
    'archFiles':HotVar(tag='archFiles',val=[],dataType=list,returnable=False),
    'archFileTimes':HotVar(tag='archFileTimes',val=[],dataType=list,returnable=False),   
    'staFile':HotVar(tag='staFile',val='',dataType=str),
    'staMeta':HotVar(tag='staMeta',val=[],dataType=np.array,returnable=False)
    }
    return hotVar

## Load in the archive and picks
#self.updateArchive()
#self.updatePickFileList()

# Class for hot variables, which have defined update functions
class HotVar(object):
    def __init__(self,tag=None,val=None,
                 dataType=None,func=None,
                 funcName=None,returnable=True):
        self.tag=tag
        self.val=val
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
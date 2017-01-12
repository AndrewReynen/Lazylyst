from obspy import Stream as emptyStream
import numpy as np

# Default Hot Variables
def initHotVar(main):
    hotVar={
    'stream':HotVar(tag='stream',val=emptyStream(),dataType=type(emptyStream())),
    'pltSt':HotVar(tag='pltSt',val=emptyStream(),dataType=type(emptyStream())),
    'staSort':HotVar(tag='staSort',val=[],dataType=list),
    'curPage':HotVar(tag='curPage',val=0,dataType=int),
    'pickDir':HotVar(tag='pickDir',val='',dataType=str),
    'pickFiles':HotVar(tag='pickFiles',val=[],dataType=list),
    'archDir':HotVar(tag='archDir',val='',dataType=str),
    'archFiles':HotVar(tag='archFiles',val=[],dataType=list,
                       linkKeys=['archiveFileTimes']),
    'archFileTimes':HotVar(tag='archFileTimes',val=[],dataType=list,
                       linkKeys=['archiveFiles']),   
    'staMeta':HotVar(tag='staMeta',val=[],dataType=np.array)
    }
    return hotVar

# Class for hot variables, which have defined update functions
class HotVar(object):
    def __init__(self,tag=None,val=None,
                 dataType=None,func=None,
                 linkKeys=[]):
        self.tag=tag
        self.val=val
        self.dataType=dataType
        self.func=func # Function which is called upon update
        self.linkKeys=linkKeys # Any other hot variable which must always update at same time
        
    def update(self):
        print self.tag
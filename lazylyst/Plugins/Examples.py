import numpy as np        
import time

# Go to the next pick type (in alphabetical order)
def togglePickMode(*args,**kwargs):
    curMode=args[0]
    availPickModes=sorted([str(key) for key in args[1].keys()])
    if curMode in availPickModes:
        idx=availPickModes.index(curMode)
    else:
        idx=0
    idx=(idx+1)%len(availPickModes)
    print 'Picking mode: '+availPickModes[idx]
    return availPickModes[idx]
    
# Go to the first or last page
def goToPage(*args,**kwargs):
    if kwargs['goToPage']=='last':
        pageNumber=99999
    else:
        pageNumber=0
    return pageNumber
        
# Toggle trace coloring between channels
def toggleTraceColor(curAssign):
    if 'lowlight' not in curAssign.keys():
        return {'lowlight':['*Z'],'highlight':['*1','*2','*E','*N']}
    if '*Z' in curAssign['lowlight']:
        return {'highlight':['*Z'],'lowlight':['*1','*2','*E','*N']}
    else:
        return {'lowlight':['*Z'],'highlight':['*1','*2','*E','*N']}
        
# Alternate the three components colors
def alternateTraceColor(curAssign):
    # If nothing assigned, gib
    if 'alt1' not in [key for key in curAssign.keys()]:
        return {'alt1':['*Z'],'alt2':['*2','*N'],'alt3':['*1','*E']}
    elif '*Z' in curAssign['alt1']:
        return {'alt2':['*Z'],'alt3':['*2','*N'],'alt1':['*1','*E']}
    elif '*Z' in curAssign['alt2']:
        return {'alt3':['*Z'],'alt1':['*2','*N'],'alt2':['*1','*E']}
    elif '*Z' in curAssign['alt3']:
        return {'alt1':['*Z'],'alt2':['*2','*N'],'alt3':['*1','*E']}

# Alternate the colors of the station color assignment
def alternateStaColorAssign(curAssign,staSort):
    # Do nothing if no stations to color
    if len(staSort)==0:
        return '$pass'
    # If given the staMeta instead of the staSort
    if len(staSort.shape)==2:
        staSort=staSort[:,0]
    # If nothing assigned, make one
    num=0
    if curAssign=={}:
        pass
    elif staSort[0] in curAssign['alt1']:
        num=1
    curAssign={'alt1':[],'alt2':[]}
    # Add all the new stations to the coloring assignment
    for i in np.arange(len(staSort)):
        if i%2==num:
            curAssign['alt1'].append(staSort[i])
        else:
            curAssign['alt2'].append(staSort[i])          
    return curAssign
    
# Make new pick dir
def newPickDir(mainPath):
    return mainPath+'/NewPickDir!'

# Go this pick file
def goToPickFile():
    return '2_20150907.051000.000000.picks'
    
# Toggle between sources
def toggleTestSources(curTag):
    if curTag=='testing':
        return 'testing2'
    else:
        return 'testing'
        
# Move forward in time by a portion of current range
def panPercent(*args,**kwargs):
    timeRange=args[0]
    delta=timeRange[1]-timeRange[0]
    if kwargs['direct']=='backward':
        delta*=-1.0
    timeRange[0]+=kwargs['percent']/100.0*delta
    timeRange[1]+=kwargs['percent']/100.0*delta
    return timeRange
    
# Zoom in/out by a certain percent, centered over current position
def zoomTraceY(yTraceRanges,percent=100):
    avg=np.mean(yTraceRanges,axis=1)
    halfWidth=(np.diff(yTraceRanges,axis=1)/2.0)[:,0]
    yTraceRanges[:,0]=avg-halfWidth*percent/100.0
    yTraceRanges[:,1]=avg+halfWidth*percent/100.0
    return yTraceRanges
        
# Return some random set of current and previous events
def randomEves(staLoc):
    # Do nothing if no stations have been added
    if len(staLoc)==0:
        return '$pass','$pass'
    staLoc=staLoc[:,1:].astype(float)
    # Make a random distribution of events bounded by the station limits
    xmin,xmax=np.min(staLoc[:,0]),np.max(staLoc[:,0])
    ymin,ymax=np.min(staLoc[:,1]),np.max(staLoc[:,1])
    xArr=np.random.rand(100)*(xmax-xmin)+xmin
    yArr=np.random.rand(100)*(ymax-ymin)+ymin
    zArr=np.ones(100)
    prevArr=np.vstack((zArr,xArr,yArr,zArr,zArr)).T
    curArr=prevArr[:3,:]
    return curArr,prevArr     

# Test for the image hot variable
def randImage(timeRange):
    tDelta=0.2
    xLen=int((timeRange[1]-timeRange[0])/tDelta)
    data=np.random.rand(xLen,10)
    if 0 in data.shape:
        return '$pass'
    return {'data':data,'t0':timeRange[0],'tDelta':tDelta}

# To print out a specific variable (Testing)
def printMe(arg):
    print(arg)
    
# To test passing of the custom dictionary variable
def testCustDict(custDict):
    if 'test123' not in custDict.keys():
        custDict['test123']=0
    else:
        custDict['test123']=(custDict['test123']+1)%5
    print(custDict)
    return custDict

# Threading test   
def waitAction(waitTime=1):
    time.sleep(waitTime)
    
# Matplotlib external plot test
def testMatplotlib():
    import matplotlib.pyplot as plt
    plt.ion()
    plt.plot([1,2],[1,2])
    plt.show()
    
# Edit the source dictionary
def editSourceDict(sourceDict):
    sourceDict['aGroup']={'newVal':np.array([0,0,99,99.999]),
                          'aaa':'haha'}
    return sourceDict
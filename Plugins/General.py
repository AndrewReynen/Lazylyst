import numpy as np

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

# Function to change picking mode to "P"    
def pickModeP(*args,**kwargs):
    curMode=args[0]
    availPickModes=sorted([str(key) for key in args[1].keys()])
    if 'P' in availPickModes:
        return 'P'
    else:
        print 'Could not change to P-picking, as mode is not defined'
        return curMode
        
# Function to change picking mode to "S" 
def pickModeS(*args,**kwargs):
    curMode=args[0]
    availPickModes=sorted([str(key) for key in args[1].keys()])
    if 'S' in availPickModes:
        return 'S'
    else:
        print 'Could not change to S-picking, as mode is not defined'
        return curMode
    
# Go to the first or last page
def goToPage(*args,**kwargs):
    if kwargs['goToPage']=='last':
        pageNumber=99999
    else:
        pageNumber=0
    return pageNumber
    
# Set the current pick file
def setCurPickFile(curPickFile,pickFiles,nextFile=False,prevFile=False):
    maxFileIdx=len(pickFiles)-1
    # Return nothing if no pick files to choose from...
    # ...or if the current pick file is not set
    if maxFileIdx==-1 or curPickFile=='':
        return ''
    curIdx=np.where(pickFiles==curPickFile)[0][0]
    # If the next or previous page, ensure still in bounds
    if nextFile and curIdx+1<=maxFileIdx:
        curPickFile=pickFiles[curIdx+1]
    elif prevFile and curIdx-1>=0:
        curPickFile=pickFiles[curIdx-1]
    return str(curPickFile)
    
# Delete the hovered stations, with current pick type
def delPick(pickSet,pickMode,curSta):
    if len(pickSet)==0:
        return np.empty((0,3))
    pickSet=pickSet[np.where((pickSet[:,0]!=curSta)|(pickSet[:,1]!=pickMode))]
    return pickSet
    
# Reverse the station sorting
def reverseStaSort(staSort):
    return staSort[::-1]
    
# Toggle trace coloring between channels
def toggleTraceColor(curAssign):
    if 'lowlight' not in [key for key in curAssign.keys()]:
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

# Remove the current pick file
def removeCurPickFile(curPickFile,pickFiles):
    if curPickFile in pickFiles:
        pickFiles=pickFiles[np.where(pickFiles!=curPickFile)]
    return pickFiles
    
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

# Go to the last double clicked station on the map 
def goToStaPage(curMapSta,staSort,staPerPage,curPage):
    if curMapSta not in staSort:
        return '$pass'
    goToPage=np.where(staSort==curMapSta)[0][0]/staPerPage
    if goToPage==curPage:
        return '$pass'
    else:
        return int(goToPage)
        
# Return some random set of current and previous events
def randomEves(staMeta):
    # Do nothing if no stations have been added
    if len(staMeta)==0:
        return '$pass','$pass'
    staMeta=staMeta[:,1:].astype(float)
    # Make a random distribution of events bounded by the station limits
    xmin,xmax=np.min(staMeta[:,0]),np.max(staMeta[:,0])
    ymin,ymax=np.min(staMeta[:,1]),np.max(staMeta[:,1])
    xArr=np.random.rand(100)*(xmax-xmin)+xmin
    yArr=np.random.rand(100)*(ymax-ymin)+ymin
    zArr=np.ones(100)
    prevArr=np.vstack((xArr,yArr,zArr)).T
    curArr=prevArr[:3,:]
    return curArr,prevArr     
        
    
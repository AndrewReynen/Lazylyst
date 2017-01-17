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
    # Return nothing, if no pick files to choose from
    if maxFileIdx==-1:
        return ''
    curIdx=pickFiles.index(curPickFile)
    # If the next or previous page, ensure still in bounds
    if nextFile and curIdx+1<=maxFileIdx:
        curPickFile=pickFiles[curIdx+1]
    elif prevFile and curIdx-1>=0:
        curPickFile=pickFiles[curIdx-1]
    return curPickFile
    
# Delete the hovered stations, with current pick type
def delPick(pickSet,pickMode,curSta):
    pickSet=pickSet[np.where((pickSet[:,0]!=curSta)|(pickSet[:,1]!=pickMode))]
    return pickSet
    
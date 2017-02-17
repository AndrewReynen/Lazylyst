import numpy as np

# Function to change picking mode to the wanted mode...
# ... Return the original mode if the wanted mode is not defined  
def setPickMode(*args,**kwargs):
    curMode=args[0]
    availPickModes=sorted([str(key) for key in args[1].keys()])
    if 'P' in availPickModes and kwargs['wantMode']=='P':
        return 'P'
    elif 'S' in availPickModes and kwargs['wantMode']=='S':
        return 'S'
    else:
        print('Could not change to wanted mode as it is not in "pickTypesMaxCountPerSta"')
        return curMode

# Swap between highlightint the vertical (P-picking mode) or horizontals (S-picking mode)
def setTracePenAssign(curMode,curAssign):
    # If highlight not defined, define it
    if 'highlight' not in curAssign.keys():
        curAssign={'highlight':['*Z'],'lowlight':['*1','*2','*E','*N']}
    # If pickMode is P, highlight vertical (also do this by default with no picking mode)
    if curMode in ['P','']:
        return {'highlight':['*Z'],'lowlight':['*1','*2','*E','*N']}
    # If pickMode is S, highlight the horizontal (toggle between horizontals if already highlighted)
    elif curMode=='S':
        if '*1' in curAssign['highlight']:
            return {'lowlight':['*1','*E','*Z'],'highlight':['*2','*N']}
        else:
            return {'lowlight':['*2','*N','*Z'],'highlight':['*1','*E']}
    # If not picking P or S, use default
    else:
        return {}
        
# Delete the hovered stations, with current pick type
def delPick(pickSet,pickMode,curSta):
    if len(pickSet)==0:
        return np.empty((0,3))
    pickSet=pickSet[np.where((pickSet[:,0]!=curSta)|(pickSet[:,1]!=pickMode))]
    return pickSet
        
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
    
# Remove the current pick file
def removeCurPickFile(curPickFile,pickFiles):
    if curPickFile in pickFiles:
        pickFiles=pickFiles[np.where(pickFiles!=curPickFile)]
    return pickFiles
    
# Go to the last double clicked station on the map 
def goToStaPage(curMapSta,staSort,staPerPage,curPage):
    if curMapSta not in staSort:
        return '$pass'
    goToPage=np.where(staSort==curMapSta)[0][0]/staPerPage
    if goToPage==curPage:
        return '$pass'
    else:
        return int(goToPage)
    
import logging
import sip
import sys,os
import numpy as np
sip.setapi('QVariant', 2)
from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import QSettings
from MainWindow import Ui_MainWindow
from CustomWidgets import TraceWidget, keyPressToString
from HotVariables import initHotVar
from Preferences import defaultPreferences, Pref
from Actions import defaultActions, defaultPassiveOrder
from Archive import getArchiveAvail, getTimeFromFileName, extractDataFromArchive
from ConfigurationDialog import ConfDialog
from SaveSource import CsDialog

# Main window class
class LazylystMain(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.loadSettings()
        self.applyPreferences()
        self.setFunctionality()
        self.introduction()
    
    # Go through all preferences, and call their update functions
    def applyPreferences(self):
        # The pick color preferences are generated here if not already present...
        # ...so iterate through static version of prefs
        curPrefs=[aPref for key, aPref in self.pref.iteritems()]
        for aPref in curPrefs:
            aPref.update(self,init=True)
        
    # Start setting up some functionality to the UI
    def setFunctionality(self):
        # Give ability to the archive displays
        self.archiveList.graph=self.archiveWidget
        self.archiveList.graph.addNewEventSignal.connect(self.addPickFile)
        self.archiveList.clicked.connect(self.setFocus) # Do not let it steal focus from keybinds
        self.archiveList.doubleClicked.connect(self.archiveListDoubleClickEvent)
        # Allow stdout to be sent to the Trace Log
        XStream.stdout().messageWritten.connect(self.textOutBrowser.insertPlainText)
        XStream.stderr().messageWritten.connect(self.textOutBrowser.insertPlainText)
        self.textOutBrowser.textChanged.connect(self.scrollTextOut)
        
    # Scroll the trace log to the bottom if an error occurs
    def scrollTextOut(self):
        scrollBar=self.textOutBrowser.verticalScrollBar()
        scrollBar.setValue(scrollBar.maximum())
    
    # Report the current keybinds for the configuration and change source actions
    def introduction(self):
        print 'Press: '+self.act['ChangeSource'].trigger.toString()+' to change source (archive/picks/station metadata)'
        print 'Press: '+self.act['OpenOptions'].trigger.toString()+' to open the configuration dialog'
    
    # Function to handle key board input from user
    def keyPressEvent(self, ev):
        super(LazylystMain, self).keyPressEvent(ev)
        keyname=keyPressToString(ev)
        if keyname==None:
            return
        # Loop through all actions and see if one is activated...
        # ... use the original set (an action may be added part way through, so can mess with the loop)
        actions=[action for key,action in self.act.iteritems() if action.trigger!='DoubleClick']
        for action in actions:
            if not action.passive and action.trigger.toString()==keyname:
                self.processAction(action)

    # Function to handle double click events from trace widgets
    def traceDoubleClickEvent(self):
        action=self.act['PickAdd']
        self.processAction(action)
    
    # Function to handle double clicks from the archive widget
    def archiveListDoubleClickEvent(self):
        action=self.act['PickFileSetToClick']
        self.processAction(action)
    
    # Create and activate the queue of actions following the initiation of an active action
    def processAction(self,action):
        # If this action was triggered over top of a trace widget, get the current station
        self.setCurSta()
        # First check to see if there are any (passive) actions which relate
        actQueue=self.collectActQueue(action)   
        for oAct in actQueue:
            self.executeAction(oAct)
                
    # Get the appropriate order of passive functions before and after their triggered active action
    def collectActQueue(self,action):
        beforeActive=[] # Passive actions with beforeTrigger
        afterActive=[] # Passive actions without beforeTrigger
        # Collect all the passive actions which have this active action as the trigger...
        # ...in the order specified within the configuration list
        for actTag in self.actPassiveOrder:
            if self.act[actTag].trigger!=action.tag:
                continue
            if self.act[actTag].beforeTrigger:
                beforeActive.append(self.act[actTag])
            else:
                afterActive.append(self.act[actTag])
        return beforeActive+[action]+afterActive

    # Function to handle the execution of an action already queued
    def executeAction(self,action):
        # If the actions function wasn't initialized, skip
        if action.func==None:
            return
        # Collect the required inputs
        inputs=[]
        hotVarKeys=[aKey for aKey in self.hotVar.keys()]
        for key in action.inputs:
            if key=='stream':
                inputs.append(self.hotVar[key].val.copy())
            elif key in hotVarKeys:
                inputs.append(self.hotVar[key].val)
            else:
                inputs.append(self.pref[key].val)
        # Call the function with args and kwargs
        returnVals=action.func(*inputs,**action.optionals)
        # Update all return (hot variable) values...
        # ... if no returns, but got something, let user know
        if len(action.returns)==0:
            if str(returnVals)!=str(None):
                print 'Action '+action.tag+' expected no returns, but received some'
            return
        # ...if just one return, convert to list to treat the same as multiple
        elif len(action.returns)==1:
            returnVals=[returnVals]
        # Go through each of the returns in order, and update
        # ...check first to see the number of returns are correct
        # ...and that the previous/new types match
        if len(action.returns)==len(returnVals):
            skipUpdates=False
            # Ensure all the variable types match before updating any hot variables...
            # ...also ensure that the hot variables ("sanity") check function passes
            for i,aReturnKey in enumerate(action.returns):
                if type(self.hotVar[aReturnKey].val)!=type(returnVals[i]):
                    print ('Action '+action.tag+' expected variable '+str(type(self.hotVar[aReturnKey].val))+
                           ' for hot variable '+aReturnKey+', got '+str(type(returnVals[i])))
                    skipUpdates=True
                    # If the type is wrong, no point in the longer check
                    continue
                if self.hotVar[aReturnKey].check==None:
                    continue
                elif not self.hotVar[aReturnKey].check(self,returnVals[i]):
                    skipUpdates=True
            if skipUpdates: 
                return
            # Process the return keys in order 
            for i,aReturnKey in enumerate(action.returns):
                self.hotVar[aReturnKey].val=returnVals[i]
                self.hotVar[aReturnKey].update()
        else:
            print ('For action '+action.tag+' got '+str(len(returnVals))+
                   ' return values, expected '+str(len(action.returns)))
    
    # Open the configuration window
    def openConfiguration(self):
        self.dialog=ConfDialog(actions=self.act,main=self,
                               pref=self.pref,hotVar=self.hotVar)
        self.dialog.exec_()
        
    # Open the change source window
    def openChangeSource(self):
        self.dialog=CsDialog(self.hotVar,self.saveSource)
        # Extract the wanted source
        if self.dialog.exec_():
            source=self.dialog.returnSource()
            # If the files exist, update the hot variables
            if source.pathExist():
                for key,val in [['sourceTag',source.tag],
                                ['archDir',source.archDir],
                                ['pickDir',source.pickDir],
                                ['staFile',source.staFile]]:
                    # Do not bother updating a hot variable if it is the same as before
                    if self.hotVar[key].val==val:
                        continue
                    self.hotVar[key].val=val
                    self.hotVar[key].update()
                ## Must now also get the staMeta np.array, and update() ##
            else:
                print 'Source update skipped'

    # Add an empty pick file to the pick directory, also add to GUI list
    def addPickFile(self):
        aTimeStr=self.archiveList.graph.newEveStr
        # Assign an ID to the new event
        seenIDs=[int(aFile.split('_')[0]) for aFile in os.listdir(self.hotVar['pickDir'].val)]
        ## Currently assigning ID where one is missing
        i=0
        while i in seenIDs:
            i+=1
        newPickFile=str(i).zfill(10)+'_'+aTimeStr+'.picks'
        # Add to the picks directory
        newFile=open(self.hotVar['pickDir'].val+'/'+newPickFile,'w')
        newFile.close()
        # Add to GUI list, and internal list
        self.archiveList.addItem(newPickFile)
        self.hotVar['pickFiles'].val=self.archiveList.visualListOrder()
        
    # Load a specific pick file from the pick directory (inter-event pick loading)
    def loadPickFile(self):
        path=self.hotVar['pickDir'].val+'/'+self.hotVar['curPickFile'].val
        # Check that the path exists
        if not os.path.exists(path):
            print 'Pick file at '+path+' no longer exists'
            return
        # Check that the file has some content
        elif os.path.getsize(path)==0:
            return
        pickSet=np.genfromtxt(path,delimiter=',',dtype=str)
        # Put into proper dimensions if only one pick was present
        if len(pickSet.shape)==1:
            pickSet=pickSet.reshape((1,3))
        pickSet=self.remUnknownPickTypes(pickSet)
        # Update the pickset
        self.hotVar['pickSet'].val=pickSet
        
    # Save the current picks
    def savePickSet(self):
        # If the current pick file was not yet initiated, nothing to save
        if self.hotVar['curPickFile'].val=='':
            return
        np.savetxt(self.hotVar['pickDir'].val+'/'+self.hotVar['curPickFile'].val,
                   self.hotVar['pickSet'].val,fmt='%s',delimiter=',')
    
    # Remove any lines which have pick types that are not currently defined
    def remUnknownPickTypes(self,pickSet):
        knownTypes=[key for key in self.pref['pickTypesMaxCountPerSta'].val]
        seenTypes=np.unique(pickSet[:,1])
        for aType in seenTypes:
            if aType not in knownTypes:
                print ('Pick type: '+aType+' is not currently defined in "pickTypesMaxCountPerSta"'+
                       ', add this pick type and redo the action - otherwise it will be removed upon saving')
                pickSet=pickSet[np.where(pickSet[:,1]!=aType)]
        return pickSet
        
    # Set the current pick file, called from double click an event in the archive list
    def setCurPickFileOnClick(self):
        return str(self.archiveList.currentItem().text())
        
    # Load the event related information
    def updateEvent(self):
        # Clear away the previous set of picks
        self.hotVar['pickSet'].val=np.empty((0,3))
        # Go back to the first page
        self.hotVar['curPage'].val=0
        # Set the title of the event
        self.timeWidget.getPlotItem().setLabels(title=self.hotVar['curPickFile'].val)
        # Load the picks from given pick file, if it has been initialized...
        if self.hotVar['curPickFile'].val!='':
            self.loadPickFile()
            # Get the wanted time, and query for the data
            aTime=getTimeFromFileName(self.hotVar['curPickFile'].val).timestamp
            t1,t2=aTime+self.pref['evePreTime'].val,aTime+self.pref['evePostTime'].val
            self.hotVar['stream'].val=extractDataFromArchive(self.hotVar['archDir'].val,t1,t2,self.hotVar['archFiles'].val,
                                                             self.hotVar['archFileTimes'].val,
                                                             archiveFileLen=self.pref['archiveFileLen'].val)
            # Make a copy for any filtering to be applied
            self.hotVar['pltSt'].val=self.hotVar['stream'].val.copy()
            # Sort traces by channel so they are added in same order (relative other stations)
            self.hotVar['pltSt'].val.sort(keys=['channel'])
            # Alphabetical sorting by default
            self.hotVar['staSort'].val=np.sort(np.unique([tr.stats.station for tr in self.hotVar['stream'].val]))
            # Move the axis time limit to the appropriate position
            minTime=np.min([tr.stats.starttime.timestamp for tr in self.hotVar['stream'].val])
            maxTime=np.max([tr.stats.endtime.timestamp for tr in self.hotVar['stream'].val])
            self.timeWidget.plotItem.setXRange(minTime,maxTime)
        # ...Otherwise load the default hot variables values, and reset values relating to curPickFile
        else:
            defaultHot=initHotVar()
            for key in ['stream','pltSt','staSort','pickSet','curSta']:
                self.hotVar[key].val=defaultHot[key].val
        # Add data, and picks to the trace widgets
        self.updatePage()
    
    # Update the data and picks on the current page
    def updatePage(self,init=False):
        # Clear away all previous lines and references to the station
        for i in range(len(self.staWidgets)):
            self.staWidgets[i].clear()
            self.staWidgets[i].pickLines=[]
            self.staWidgets[i].sta=''
            self.staWidgets[i].pltItem.setLabel(axis='left',text='empty')
        # Add in the trace data for the current page
        i=0
        stas=np.array([tr.stats.station for tr in self.hotVar['pltSt'].val])
        numStas=len(np.unique(stas))
        while self.hotVar['curPage'].val*self.pref['staPerPage'].val+i<numStas:
            if i==self.pref['staPerPage'].val:
                break
            # Figure out which traces are associated with the next station in staSort
            thisSta=self.hotVar['staSort'].val[self.hotVar['curPage'].val*self.pref['staPerPage'].val+i]
            wantIdxs=np.where(stas==thisSta)[0]
            # Also set the y-limits
            ymin=np.min([np.min(self.hotVar['pltSt'].val[idx].data) for idx in wantIdxs])
            ymax=np.max([np.max(self.hotVar['pltSt'].val[idx].data) for idx in wantIdxs])
            self.staWidgets[i].setYRange(ymin,ymax)
            # Assign the widget a station code
            self.staWidgets[i].sta=thisSta
            self.staWidgets[i].pltItem.setLabel(axis='left',text=thisSta)
            # Plot the data
            for idx in wantIdxs:
                self.staWidgets[i].addCurve(y=self.hotVar['pltSt'].val[idx].data,
                                            x=self.hotVar['pltSt'].val[idx].times()+
                                            self.hotVar['pltSt'].val[idx].stats.starttime.timestamp)
            # Get the picks that are associated with this station...
            if len(self.hotVar['pickSet'].val)>0:
                pickIdxs=np.where(self.hotVar['pickSet'].val[:,0]==thisSta)[0]
                # ... and plot them, while adding them to pltLines in the same index position
                for idx in pickIdxs:
                    aType,aTime=self.hotVar['pickSet'].val[idx,1:3]
                    self.staWidgets[i].addPick(aTime,aType,pen=self.getPickPen(aType))
            i+=1
    
    # Function to handle updates of the hot variable curPage
    def updateCurPage(self):
        # Clip to the max/minimum if outside the accepted range
        maxPageNum=(len(self.hotVar['staSort'].val)-1)/self.pref['staPerPage'].val
        if maxPageNum==-1:
            return
        if self.hotVar['curPage'].val>maxPageNum:
            self.hotVar['curPage'].val=maxPageNum
        elif self.hotVar['curPage'].val<0:
            self.hotVar['curPage'].val=0
        self.updatePage()
        
    # Built in function to tab to the next or previous page number
    def tabCurPage(self,nextPage=False,prevPage=False,pageNum=0):
        maxPageNum=(len(self.hotVar['staSort'].val)-1)/self.pref['staPerPage'].val
        # If the next or previous page, ensure still in bounds
        if nextPage and self.hotVar['curPage'].val+1<=maxPageNum:
            self.hotVar['curPage'].val+=1
        elif prevPage and self.hotVar['curPage'].val-1>=0:
            self.hotVar['curPage'].val-=1
        else:
            return
        # If got to the end, the page number must have changed, update the page
        self.updatePage()
        
    # Set which station is currently being hovered over
    def setCurSta(self):
        for widget in self.staWidgets:
            if widget.hasFocus():
                self.hotVar['curSta'].val=widget.sta
                return
        self.hotVar['curSta'].val=''
        
    # Add a pick to the double-clicked station (single-pick addition)
    def addClickPick(self):
        # Return if no pick mode selected
        if self.hotVar['pickMode'].val=='':
            print 'No pick mode selected'
            return
        # Figure out which widget was picked on
        aList=[aWidget for aWidget in self.staWidgets if aWidget.hasFocus()]
        if len(aList)!=1:
            print 'Picking is out of focus, skipped'
            return
        widget=aList[0]
        curMode=self.hotVar['pickMode'].val
        # Append this pick to the pick set, and plotted lines
        self.hotVar['pickSet'].val=np.vstack((self.hotVar['pickSet'].val,
                                              [widget.sta,curMode,widget.clickPos]))
        widget.addPick(widget.clickPos,curMode,self.getPickPen(curMode))
        # Remove picks from the plot and pickSet, where there are too many
        self.remExcessPicks(checkStas=[widget.sta],checkTypes=[curMode])

    # Remove older picks, which occurs when a given pick type has more than "X"...
    # ...number of picks on a given station (see pref['pickTypesMaxCountPerSta'])
    def remExcessPicks(self,checkStas=None,checkTypes=None):
        # If sta or types is present, check only to delete those pickTypes on given stations
        if checkStas==None:
            checkStas=self.hotVar['staSort'].val
        if checkTypes==None:
            checkTypes=[key for key in self.pref['pickTypesMaxCountPerSta']]
        delIdxs=[]
        visStas=[widget.sta for widget in self.staWidgets]
        # Gather all indicies to be removed from pickSet and pltLines
        for pickType in checkTypes:
            for sta in checkStas:
                potIdxs=np.where((self.hotVar['pickSet'].val[:,0]==sta)&
                                 (self.hotVar['pickSet'].val[:,1]==pickType))[0]
                pickCountMax=self.pref['pickTypesMaxCountPerSta'].val[pickType]
                # If there are more picks than allowed, add to delete indices
                if len(potIdxs)>pickCountMax:
                    delIdxs+=list(np.sort(potIdxs)[:-pickCountMax])
                    # Delete the excess lines from the widget (if currently shown)
                    if sta in visStas:
                        self.staWidgets[visStas.index(sta)].removePicks(pickType,len(potIdxs)-pickCountMax)
        # Remove the picks from the hot variable pickSet
        keepIdxs=np.array([i for i in range(len(self.hotVar['pickSet'].val)) if i not in delIdxs])
        self.hotVar['pickSet'].val=self.hotVar['pickSet'].val[keepIdxs]
        
    # Function to handle updates to the hot variable pickSet (assumes all picks have changed)
    # ... adding and remove picks on the current page (does not remove excess)
    def updatePagePicks(self):
        # Find out which of these values are unique (to remove duplicate picks)
        curList=[a[0]+a[1]+a[2] for a in self.hotVar['pickSet'].val]
        unqCur,unqCurIdx=np.unique(curList,return_index=True)
        # Update the new set with only the unique picks
        self.hotVar['pickSet'].val=self.hotVar['pickSet'].val[unqCurIdx]
        # Remove any old plot lines
        for widget in self.staWidgets:
            for line in widget.pickLines:
                widget.pltItem.removeItem(line)
            widget.pickLines=[]
        # Add in the new lines
        stas=[widget.sta for widget in self.staWidgets]
        for sta,aType,aTime in self.hotVar['pickSet'].val:
            if sta not in stas:
                continue
            self.staWidgets[stas.index(sta)].addPick(aTime,aType,self.getPickPen(aType))
            
    
    # Return the wanted pick types pen, in RGB
    def getPickPen(self,aType):
        col=QtGui.QColor(self.pref['pickColor_'+aType].val)
        return (col.red(), col.green(), col.blue())
    
    # Change the color of the traces
    def updateTraceBackground(self,init=False):
        col=QtGui.QColor(self.pref['backgroundColorTrace'].val)
        for aWidget in self.staWidgets:
            aWidget.setBackground(col)
    
    # Change the color of time time axis
    def updateTimeBackground(self,init=False):
        col=QtGui.QColor(self.pref['backgroundColorTime'].val)
        self.timeWidget.setBackground(col)
    
    # Change the color of the archive axis
    def updateArchiveBackground(self,init=False):
        col=QtGui.QColor(self.pref['backgroundColorArchive'].val)
        self.archiveWidget.setBackground(col)
        
    # Update how many widgets are on the main page
    def updateStaPerPage(self,init=False):
        # First remove the previous staWidgets
        for aWidget in self.staWidgets:
            aWidget.setParent(None)
            self.traceLayout.removeWidget(aWidget)
            self.staWidgets=[]
        # Add the desired number of staWidgets
        while len(self.staWidgets)<self.pref['staPerPage'].val:
            self.staWidgets.append(TraceWidget(self.mainLayout))
            self.staWidgets[-1].setXLink('timeAxis')
            self.traceLayout.addWidget(self.staWidgets[-1])
            # Connect the double click signal to the add pick signal
            self.staWidgets[-1].doubleClickSignal.connect(self.traceDoubleClickEvent)
        self.updateTraceBackground()
        self.updatePage()
        
    # Set the archive availability
    def updateArchive(self):
        # Load in all of the start times of the archive
        archiveFiles,archiveTimes=getArchiveAvail(self.hotVar['archDir'].val)
        self.hotVar['archFiles'].val=archiveFiles
        self.hotVar['archFileTimes'].val=archiveTimes
        if len(archiveFiles)==0:
            print 'No miniseed files in '+self.hotVar['archDir'].val
            return
        # Update the time boxes
        if self.pref['archiveLoadMethod'].val=='fast':
            ranges=[[t,t+self.pref['archiveFileLen'].val] for t in archiveTimes]
            self.archiveWidget.updateBoxes(ranges)
        else:
            print 'Unsupported archive load method'
            return
        # Show the boundaries
        self.archiveWidget.t1=archiveTimes[0]
        self.archiveWidget.t2=archiveTimes[-1]+self.pref['archiveFileLen'].val
        self.archiveWidget.updateBoundaries()
        
    # Load the pick file list for display, given completly new pick directory
    def updatePickDir(self):
        # Clear the old list
        self.archiveList.clear()
        self.hotVar['pickFiles'].val=[]
        # Reset the current pick file
        self.hotVar['curPickFile'].val=''
        self.hotVar['curPickFile'].update()
        # Only accept files with proper naming convention
        for aFile in sorted(os.listdir(self.hotVar['pickDir'].val)):
            aFile=str(aFile)
            splitFile=aFile.split('_')
            # Make sure has the proper extension '.picks'
            if len(splitFile)!=2 or aFile.split('.')[-1]!='picks':
                continue
            try:
                int(splitFile[0])
                getTimeFromFileName(aFile)
            except:
                continue
            self.hotVar['pickFiles'].val.append(aFile)
            self.archiveList.addItem(aFile)
    
    # With the same pick directory, force an update on the pick files...
    # ...this allows for addition of empty pick files and deletion of pick files
    def updatePickFiles(self):
        # Clear the old GUI list, and add the new items
        self.archiveList.clear()
        self.archiveList.addItems(self.hotVar['pickFiles'].val)
        # See which files were present prior to the update
        prevFiles=sorted(os.listdir(self.hotVar['pickDir'].val))
        # Delete events which are no longer present
        for aFile in prevFiles:
            path=self.hotVar['pickDir'].val+'/'+aFile
            if (aFile not in self.hotVar['pickFiles'].val) and os.path.exists(path):
                os.remove(path)
        # Add blank pick files which were not present before
        for aFile in self.hotVar['pickFiles'].val:
            if aFile not in prevFiles:
                newFile=open(self.hotVar['pickDir'].val+'/'+aFile,'w')
                newFile.close()
        # If the current pick file no longer exists, update it
        if self.hotVar['curPickFile'].val not in self.hotVar['pickFiles'].val:
            self.hotVar['curPickFile'].val=''
            self.hotVar['curPickFile'].update()
    
    # As the number of pick types can change in the settings...
    # ...show less/more pick type color preferences
    def updatePickColorPrefs(self,init=False):
        curPickTypes=[key for key in self.pref['pickTypesMaxCountPerSta'].val]
        curPickColors=[key for key in self.pref.keys() if
                       ('pickColor_' in str(key) and self.pref[key].dialog=='ColorDialog')]
        # Add the pick color preferences
        for aType in curPickTypes:
            # Do not overwrite if already present
            tag='pickColor_'+aType
            if tag in curPickColors:
                continue
            # Otherwise add the color
            self.pref[tag]=Pref(tag=tag,val=4294967295,dataType=int,
                            dialog='ColorDialog',func=self.updatePage)
            # If Lazylyst is starting, still have to load in the previous pick colors (if set already)
            if init:
                prefVals=self.setPref.value('prefVals', {})
                if tag in [key for key in prefVals.keys()]:
                    self.pref[tag].val=prefVals[tag]
        # Remove any entries which may have been taken away from curPickTypes
        for tag in curPickColors:
            if tag.split('_')[1] not in curPickTypes:
                self.pref.pop(tag)
        # Update the configuration dialogs preference list
        if not init:
            self.dialog.confPrefList.clear()
            self.dialog.confPrefList.addItems([key for key in self.pref.keys()])          
    
    # Load setting from previous run, and initialize base variables
    def loadSettings(self):
        # Get this scripts path, as functions will be relative to this
        self.path=os.path.dirname(__file__)
        # Load the hot variables
        self.hotVar=initHotVar()
        for key,hotVar in self.hotVar.iteritems():
            hotVar.linkToFunction(self)
        # Get all values from settings
        self.setGen=QSettings('setGen.ini', QSettings.IniFormat)
        self.setAct= QSettings('setAct.ini', QSettings.IniFormat)
        self.setPref=QSettings('setPref.ini', QSettings.IniFormat)
        self.setSource=QSettings('setSource.ini', QSettings.IniFormat)
        # UI size
        self.resize(self.setGen.value('size', QtCore.QSize(1300, 700)))
        # Actions...
        self.act=self.setAct.value('actions', defaultActions())
        self.actPassiveOrder=self.setAct.value('actPassiveOrder', defaultPassiveOrder(self.act))
        if self.actPassiveOrder==None:
            self.actPassiveOrder=[]
        # ...link all actions to their appropriate functions
        for key,action in self.act.iteritems():
            action.linkToFunction(self)
        # Preferences
        self.pref=defaultPreferences(self)
        prefVals=self.setPref.value('prefVals', {})
        for aKey in prefVals.keys():
            # Skip any preferences which are generated a bit later
            if 'pickColor_' in aKey:
                continue
            self.pref[aKey].val=prefVals[aKey]
        # Saved sources
        self.saveSource=self.setSource.value('savedSources', {})
        # Create empty variables
        self.staWidgets=[]
        
    # Save all settings from current run
    def saveSettings(self):
        # UI size
        self.setGen.setValue('size', self.size())
        # Actions, cannot save functions (will be linked again upon loading)
        for key in self.act.keys():
            self.act[key].func=None
        self.setAct.setValue('actions',self.act)
        self.setAct.setValue('actPassiveOrder',self.actPassiveOrder)
        # Preferences
        prefVals={}
        for aKey in self.pref.keys():
            prefVals[self.pref[aKey].tag]=self.pref[aKey].val
        self.setPref.setValue('prefVals',prefVals)
        # Saved sources
        self.setSource.setValue('savedSources',self.saveSource)

    # When the GUI closes, will save to settings
    def closeEvent(self,ev):
        self.saveSettings()
        ev.accept()
        
# Class for logging
class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
    def emit(self, record):
        record = self.format(record)
        if record: XStream.stdout().write('%s\n'%record)
    
class XStream(QtCore.QObject):
    _stdout = None
    _stderr = None
    messageWritten = QtCore.pyqtSignal(str)
    def flush( self ):
        pass
    def fileno( self ):
        return -1
    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            self.messageWritten.emit(unicode(msg))
    @staticmethod
    def stdout():
        if ( not XStream._stdout ):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout
    @staticmethod
    def stderr():
        if ( not XStream._stderr ):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr

# Start up the logging and UI
if __name__ == '__main__':
    # For sending stdout to the trace log
    logger = logging.getLogger(__name__)
    handler = QtHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    # Start up the UI
    app = QtGui.QApplication(sys.argv)
    window = LazylystMain()
    window.show()
    sys.exit(app.exec_())
# -*- coding: utf-8 -*-
import sys
import logging
import sip
import os
import numpy as np
sip.setapi('QVariant', 2)
sip.setapi('QString', 2)
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
from fnmatch import fnmatch
from pyqtgraph import mkPen,mkBrush

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
        # Connect the zoomed in and zoomed out views of the event files
        self.archiveSpan.span.sigRegionChanged.connect(lambda: self.archiveEvent.updateXRange(self.archiveSpan.span))
        self.archiveSpan.span.sigRegionChangeFinished.connect(self.updateArchiveSpanList)
        # Give ability to the archive displays
        self.archiveList.graph=self.archiveEvent
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
        # Collect all the passive actions which have this active action as a trigger...
        # ...in the order specified within the configuration list
        for actTag in self.actPassiveOrder:
            if action.tag not in self.act[actTag].trigger:
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
        # Go through each of the returns in order, and update...
        # ...check first to see the number of returns are correct
        # ...and that the previous/new types match
        if len(action.returns)==len(returnVals):
            skipUpdates=False
            # Ensure all the variable types match before updating any hot variables...
            # ...also ensure that the hot variables ("sanity") check function passes
            for i,aReturnKey in enumerate(action.returns):
                if self.hotVar[aReturnKey].dataType!=type(returnVals[i]):
                    print ('Action '+action.tag+' expected variable '+str(self.hotVar[aReturnKey].dataType)+
                           ' for hot variable '+aReturnKey+', got '+str(type(returnVals[i])))
                    skipUpdates=True
                    # If the type is wrong, no point in the longer check
                    continue
                if self.hotVar[aReturnKey].check==None:
                    continue
                elif not self.hotVar[aReturnKey].check(self,returnVals[i]):
                    print 'Action '+action.tag+' failed '+aReturnKey+' check'
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
                    self.hotVar[key].val=val
                    self.hotVar[key].update()
                ## Must now also get the staMeta np.array, and update() ##
            else:
                print 'Source update skipped'

    # Add an empty pick file to the pick directory, also add to GUI list
    def addPickFile(self):
        # Ignore if no archive is currently set
        if self.hotVar['archDir'].val=='':
            return
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
        self.hotVar['pickFiles'].val=[str(aFile) for aFile in sorted(os.listdir(self.hotVar['pickDir'].val))]
        self.hotVar['pickFileTimes'].update()
        self.archiveEvent.updateEveLines([getTimeFromFileName(newPickFile).timestamp],
                                         self.pref['archiveColorEve'].val,'add')
        self.updateArchiveSpanList()
    
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
                print ('Pick type: '+aType+' is not currently defined in preference pickTypesMaxCountPerSta'+
                       ' and has been removed from the hot variable pickSet')
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
            # Ensure that the archive span and list includes this file
            self.checkArchiveSpan()
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
        # Add data, and picks to the station widgets
        self.updatePage()
        # Update the highlighted event on the archive visual
        self.updateArchiveEveColor()
    
    # Update the data and picks on the current page
    def updatePage(self,init=False):
        # Update the trace curves
        self.updateTraces()
        # Update the picks
        self.updatePagePicks()
    
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
    
    # If the current pick file moved outside of the selected range...
    # ...increase the range to include the pick file
    def checkArchiveSpan(self):
        fileTime=getTimeFromFileName(self.hotVar['curPickFile'].val).timestamp
        t1,t2=self.archiveSpan.span.getRegion()
        reset=False
        if fileTime<t1:
            t1=fileTime-0.02*(t2-t1)
            reset=True
        if fileTime>t2:
            t2=fileTime+0.02*(t2-t1)
            reset=True
        if reset:
            self.archiveSpan.span.setRegion((t1,t2))
        
    # Set which station is currently being hovered over
    def setCurSta(self):
        for widget in self.staWidgets:
            if widget.hasFocus():
                self.hotVar['curSta'].val=widget.sta
                return
        self.hotVar['curSta'].val=''
        
    # Add a pick to the double-clicked station (single-pick addition)
    def addClickPick(self):
        if self.hotVar['curPickFile'].val=='':
            return
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
        curList=[str(a[0])+str(a[1])+str(a[2]) for a in self.hotVar['pickSet'].val]
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
    
    # Match all streams channels to its appropriate pen
    def getStreamPens(self):
        penRef={} # Dictionary to return with all unique channels pens
        acceptKeys=[key for key in self.pref['tracePen'].val.keys()]
        unqChas=np.unique([tr.stats.channel for tr in self.hotVar['stream'].val])
        # First check what tracePenAssign keys are actually accepted
        useKeys=[]
        for key in self.hotVar['tracePenAssign'].val.keys():
            # If the user returned default, let them know it is used if others do not exist
            if key=='default':
                print 'tracePen tag default is used as a catch all, ignored so does not overwrite other trace pens'
            elif key in acceptKeys:
                useKeys.append(key)
            else:
                print 'tracePen tag '+key+ 'is not currently defined in preference tracePen, applying default'
        # Loop through each unique channel and add its pen to penRef
        for cha in unqChas:
            colorInt,width=None,None
            matched=False
            # Check each of the entries for this key for a match
            for key,aList in [[aKey,self.hotVar['tracePenAssign'].val[aKey]] for aKey in useKeys]:
                for entry in aList:
                    if fnmatch(cha,entry):
                        colorInt,width,depth=self.pref['tracePen'].val[key]
                        matched=True
                        break
                if matched:
                    break
            # If there was no match, apply default
            if colorInt==None:
                colorInt,width,depth=self.pref['tracePen'].val['default']
            pen=mkPen(QtGui.QColor(colorInt),width=width)
            penRef[cha]=[pen,depth]
        return penRef
    
    # Update the trace curves on the current page
    def updateTraces(self):
        # As new channels could have been added, update the pen reference
        self.chaPenRef=self.getStreamPens()
        # Clear away all previous curves, and references to this station
        for i in range(len(self.staWidgets)):
            for curve in self.staWidgets[i].traceCurves:
                self.staWidgets[i].removeItem(curve)
            self.staWidgets[i].traceCurves=[]
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
                trace=self.hotVar['pltSt'].val[idx]
                pen,depth=self.chaPenRef[trace.stats.channel]
                self.staWidgets[i].addTrace(trace.times()+trace.stats.starttime.timestamp,trace.data,
                                            trace.stats.channel,pen,depth)
            i+=1
        
    # Update just the trace pens on the current page
    def updateTracePen(self,init=False):
        self.chaPenRef=self.getStreamPens()
        for widget in self.staWidgets:
            for curve in widget.traceCurves:
                pen,depth=self.chaPenRef[curve.cha]
                curve.setPen(pen)
                curve.setZValue(depth)
    
    # Change the color of the trace background
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
        self.archiveSpan.setBackground(col)
        self.archiveEvent.setBackground(col)
        
    # Change the color of the archive availability boxes
    def updateArchiveAvailColor(self,init=False):
        col=QtGui.QColor(self.pref['archiveColorAvail'].val)
        for box in self.archiveSpan.boxes:
            box.setPen(col)
    
    # Change the color of the archive span select
    def updateArchiveSpanColor(self,init=False):
        col=QtGui.QColor(self.pref['archiveColorSpan'].val)
        rgba=(col.red(),col.green(),col.blue(),65)
        self.archiveSpan.span.setBrush(mkBrush(rgba))
        for line in self.archiveSpan.span.lines:
            line.setPen(col)
        
    # Change the color of the events in the archive visual...
    # ...selected, not selected, use same color as selected for archive span line hover
    def updateArchiveEveColor(self,init=False):
        col1=QtGui.QColor(self.pref['archiveColorSelect'].val)
        col2=QtGui.QColor(self.pref['archiveColorEve'].val)
        # See what the time of the current pick file is
        curFile=self.hotVar['curPickFile'].val
        if curFile=='':
            t='NAN'
        else:
            t=getTimeFromFileName(curFile)
        # Set the event line colors
        for line in self.archiveEvent.eveLines:
            if line.value()==t:
                line.setPen(col1)
                line.setZValue(10)
            else:
                line.setPen(col2)
                line.setZValue(0)
        # Use the select for highlighting the span when hovered
        for line in self.archiveSpan.span.lines:
            line.setHoverPen(col1)
        
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
            self.archiveSpan.updateBoxes(ranges,self.pref['archiveColorAvail'].val)
        else:
            print 'Unsupported archive load method'
            return
        # Set the initial span boundaries, and x-limits
        t1,t2=archiveTimes[0],archiveTimes[-1]+self.pref['archiveFileLen'].val
        buff=(t2-t1)*0.05
        self.archiveSpan.pltItem.setXRange(t1-buff,t2+buff)
        self.archiveSpan.span.setRegion((t1,t2))
    
    # Update the pick list with events only in the selected span
    # ...this is done after both pickFiles and pickFileTimes are updated
    def updateArchiveSpanList(self):
        files=np.array(self.hotVar['pickFiles'].val)
        times=np.array(self.hotVar['pickFileTimes'].val)
        t1,t2=self.archiveSpan.span.getRegion()
        # See which files should be listed
        toListFiles=files[np.where((times>=t1)&(times<=t2))]
        # Reload the pick file list
        self.archiveList.clear()
        self.archiveList.addItems(toListFiles)
        
    # Load the pick file list for display, given completly new pick directory
    def updatePickDir(self):
        # Clear the old list
        self.archiveList.clear()
        self.hotVar['pickFiles'].val=[]
        # Reset the current pick file
        self.hotVar['curPickFile'].val=''
        self.hotVar['curPickFile'].update()
        eveFileTimes=[]
        # Only accept files with proper naming convention
        for aFile in sorted(os.listdir(self.hotVar['pickDir'].val)):
            aFile=str(aFile)
            splitFile=aFile.split('_')
            # Make sure has the proper extension '.picks'
            if len(splitFile)!=2 or aFile.split('.')[-1]!='picks':
                continue
            try:
                int(splitFile[0])
                eveFileTimes.append(getTimeFromFileName(aFile).timestamp)
            except:
                continue
            self.hotVar['pickFiles'].val.append(aFile)
        # Update the pick file times hot variable
        self.hotVar['pickFileTimes'].update()
        self.archiveEvent.updateEveLines(self.hotVar['pickFileTimes'].val,
                                         self.pref['archiveColorEve'].val,'reset')
        # Finally update the pick list
        self.updateArchiveSpanList()
    
    # With the same pick directory, force an update on the pick files...
    # ...this allows for addition of empty pick files and deletion of pick files
    def updatePickFiles(self):
        # Resort the pick files
        self.hotVar['pickFiles'].val=sorted(self.hotVar['pickFiles'].val)
        # Update th pick file times, and reset their line in archiveEvent
        self.hotVar['pickFileTimes'].update()
        self.archiveEvent.updateEveLines(self.hotVar['pickFileTimes'].val,
                                         self.pref['archiveColorEve'].val,'reset')
        # Clear the old GUI list, and add the new items
        self.updateArchiveSpanList()
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
        # Update the current pick file (no entry) if it is no longer in the pick files
        if self.hotVar['curPickFile'].val not in self.hotVar['pickFiles'].val:
            self.hotVar['curPickFile'].val=''
            self.hotVar['curPickFile'].update()
    
    # With the same source information, go to the current pick file
    def updateCurPickFile(self):
        if self.hotVar['curPickFile'].val!='':
            # Ensure that the ID has the same length
            splitFile=self.hotVar['curPickFile'].val.split('_')
            self.hotVar['curPickFile'].val=splitFile[0].zfill(10)+'_'+splitFile[1]
            # If the file does not exist, create it
            if self.hotVar['curPickFile'].val not in self.hotVar['pickFiles'].val:
                newFile=open(self.hotVar['pickDir'].val+'/'+self.hotVar['curPickFile'].val,'w')
                newFile.close()
                # Add this event to pickFiles
                self.hotVar['pickFiles'].val.append(self.hotVar['curPickFile'].val)
                self.hotVar['pickFiles'].update()
        self.updateEvent()
    
    # Update the pick file times, given a new set of pick files
    def updatePickFileTimes(self):
        self.hotVar['pickFileTimes'].val=[getTimeFromFileName(aFile).timestamp for aFile in self.hotVar['pickFiles'].val]  
    
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
        # If the user deleted a pick type with them already present on screen, remove them
        for aType in np.unique(self.hotVar['pickSet'].val[:,1]):
            if aType not in curPickTypes:
                self.hotVar['pickSet'].val=self.remUnknownPickTypes(self.hotVar['pickSet'].val)
                self.hotVar['pickSet'].update()
                break
    
    # Load setting from previous run, and initialize base variables
    def loadSettings(self):
        # Load the hot variables
        self.hotVar=initHotVar()
        # Get this scripts path, as functions will be relative to this
        mainPath=os.path.dirname(os.path.realpath(__file__))
        self.hotVar['mainPath'].val=mainPath
        for key,hotVar in self.hotVar.iteritems():
            hotVar.linkToFunction(self)
        # Get all values from settings
        self.setGen=QSettings(mainPath+'/setGen.ini', QSettings.IniFormat)
        self.setAct= QSettings(mainPath+'/setAct.ini', QSettings.IniFormat)
        self.setPref=QSettings(mainPath+'/setPref.ini', QSettings.IniFormat)
        self.setSource=QSettings(mainPath+'/setSource.ini', QSettings.IniFormat)
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
        # Preferences (start)
        self.pref=defaultPreferences(self)
        prefVals=self.setPref.value('prefVals', {})
        # Preferences (finish)
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
            prefVals[str(self.pref[aKey].tag)]=self.pref[aKey].val
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
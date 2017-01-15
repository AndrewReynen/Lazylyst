import logging
import sip
import sys,os
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
import numpy as np

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
        action=self.act['AddPick']
        self.processAction(action)
    
    # Function to handle double clicks from the archive widget
    def archiveListDoubleClickEvent(self):
        action=self.act['LoadEvent']
        self.processAction(action)
    
    # Create and activate the queue of actions following the initiation of an active action
    def processAction(self,action):
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
        # If nothing was returned, but was expected - let user know
        if returnVals==None and len(action.returns)!=0:
            print 'For action '+action.tag+' got 0 return values, expected '+len(action.returns)
            return
        # Skip if no returns
        if returnVals==None:
            return
        # Update all return (hot variable) values...
        # ...if just one return, convert to list to treat the same as multiple
        if len(action.returns)==1:
            returnVals=[returnVals]
        # Go through each of the returns in order, and update
        # ...check first to see the number of returns are correct
        # ...and that the previous/new types match
        if len(action.returns)==len(returnVals):
            skipUpdates=False
            # Ensure all the variable types match before updating any hot variables
            for i,aReturnKey in enumerate(action.returns):
                if type(self.hotVar[aReturnKey].val)!=type(returnVals[i]):
                    print ('Action '+action.tag+' expected variable '+str(type(self.hotVar[aReturnKey].val))+
                           ' for hot variable '+aReturnKey+', got '+str(type(returnVals[i])))
                    skipUpdates=True
            if skipUpdates: return
            # Process the return keys in order 
            for i,aReturnKey in enumerate(action.returns):
                self.hotVar[aReturnKey].val=returnVals[i]
                self.hotVar[aReturnKey].update()
        else:
            print ('For action '+action.tag+' got '+str(len(returnVals))+
                   ' return values, expected '+len(action.returns))
    
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
        # Add to GUI list
        self.archiveList.addItem(newPickFile)
        # Add to the picks directory
        newFile=open(self.hotVar['pickDir'].val+'/'+newPickFile,'w')
        newFile.close()
        
    # Load a specific pick file
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
        self.hotVar['pickSet'].val=pickSet
        self.pltLines=[None]*len(pickSet)
        
    # Save the current picks
    def savePickFile(self):
        # If the current pick file was not yet initiated, nothing to save
        if self.hotVar['curPickFile'].val=='':
            return
        path=self.hotVar['pickDir'].val+'/'+self.hotVar['curPickFile'].val
        np.savetxt(path,self.hotVar['pickSet'].val,fmt='%s',delimiter=',')

    # Load the current event
    def loadEvent(self):
        self.hotVar['curPickFile'].val=self.archiveList.currentItem().text() ## Have to change how this is updated ##
                                                                             ## Maybe a optional input to say where from? ##
        curPickFile=self.hotVar['curPickFile'].val
        # Clear away the previous set of picks
        self.hotVar['pickSet'].val=np.empty((0,3))
        self.pltLines=[]
        # Load the picks from given pick file
        self.loadPickFile()
        # Get the wanted time, and query for the data
        aTime=getTimeFromFileName(curPickFile).timestamp
        t1,t2=aTime+self.pref['evePreTime'].val,aTime+self.pref['evePostTime'].val
        self.hotVar['stream'].val=extractDataFromArchive(self.hotVar['archDir'].val,t1,t2,self.hotVar['archFiles'].val,
                                                         self.hotVar['archFileTimes'].val,
                                                         archiveFileLen=self.pref['archiveFileLen'].val)
        # Make a copy for any filtering to be applied
        self.hotVar['pltSt'].val=self.hotVar['stream'].val.copy()
        # Sort traces by channel so they are added in same order (relative other stations)
        self.hotVar['pltSt'].val.sort(keys=['channel'])
        ## Alphabetical sorting for now ##
        self.hotVar['staSort'].val=np.sort(np.unique([tr.stats.station for tr in self.hotVar['stream'].val]))
        # Move the axis time limit to the appropriate position
        minTime=np.min([tr.stats.starttime.timestamp for tr in self.hotVar['stream'].val])
        maxTime=np.max([tr.stats.endtime.timestamp for tr in self.hotVar['stream'].val])
        self.timeWidget.plotItem.setXRange(minTime,maxTime)
        # Add data to the trace widgets
        self.updatePage()
    
    # Update the entire page which includes data, picks, and sorting
    def updatePage(self):
        # Clear away all previous lines and references to the station
        for i in range(len(self.staWidgets)):
            self.staWidgets[i].clear()
            self.staWidgets[i].sta=None
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
                self.staWidgets[i].plot(y=self.hotVar['pltSt'].val[idx].data,
                                        x=self.hotVar['pltSt'].val[idx].times()+
                                        self.hotVar['pltSt'].val[idx].stats.starttime.timestamp)
            # Get the picks that are associated with this station...
            if len(self.hotVar['pickSet'].val)>0:
                pickIdxs=np.where(self.hotVar['pickSet'].val[:,0]==thisSta)[0]
                # ... and plot them, while adding them to pltLines in the same index position
                for idx in pickIdxs:
                    aType,aTime=self.hotVar['pickSet'].val[idx,1:3]
                    self.pltLines[idx]=self.staWidgets[i].pltItem.addLine(x=aTime,pen=self.getPickPen(aType))
            i+=1
    
    # Set the current page number
    def setCurPage(self,nextPage=False,prevPage=False,pageNum=0):
        maxPageNum=(len(self.hotVar['staSort'].val)-1)/self.pref['staPerPage'].val
        # If the next or previous page, ensure still in bounds
        if nextPage and self.hotVar['curPage'].val+1<=maxPageNum:
            self.hotVar['curPage'].val+=1
        elif prevPage and self.hotVar['curPage'].val-1>=0:
            self.hotVar['curPage'].val-=1
        # If neither next nor previous page, set the specific if in bounds
        elif (not nextPage and not prevPage and pageNum!=self.hotVar['curPage'].val and
              pageNum>=0 and pageNum<=maxPageNum):
            self.hotVar['curPage'].val=pageNum
        else:
            return
        # If got to the end, the page number must have changed, update the page
        self.updatePage()
        
    # Add a pick to the double-clicked station
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
        # Append this pick to the pick set, and plotted lines
        self.hotVar['pickSet'].val=np.vstack((self.hotVar['pickSet'].val,
                                              [widget.sta,self.hotVar['pickMode'].val,widget.clickPos]))
                                              #        curMode=
        self.pltLines.append(widget.pltItem.addLine(x=widget.clickPos,
                                                    pen=self.getPickPen(self.hotVar['pickMode'].val)))
        # Remove any older picks (each pick type has a limited number per station)
        self.remOldPicks(checkStas=[widget.sta],checkTypes=[self.hotVar['pickMode'].val])

    # Remove previously place picks, which occurs when a given pick type has more than "X"...
    # ...number of picks on a given station (see pref['pickTypesMaxCountPerSta'])
    def remOldPicks(self,checkStas=None,checkTypes=None):
        # If sta or types is present, check only to delete those pickTypes on given stations
        if checkStas==None:
            checkStas=self.hotVar['staSort'].val
        if checkTypes==None:
            checkTypes=[key for key in self.pref['pickTypesMaxCountPerSta']]
        delIdxs=[]
        # Gather all indicies to be removed from pickSet and pltLines
        for pickType in checkTypes:
            for sta in checkStas:
                potIdxs=np.where((self.hotVar['pickSet'].val[:,0]==sta)&
                                 (self.hotVar['pickSet'].val[:,1]==pickType))[0]
                pickCountMax=self.pref['pickTypesMaxCountPerSta'].val[pickType]
                # If there are more picks than allowed, add to delete indices
                if len(potIdxs)>pickCountMax:
                    delIdxs+=list(np.sort(potIdxs)[:-pickCountMax])
        # Reverse sorting of indicies, so lower value indicies do not change when pop()ing
        delIdxs=sorted(delIdxs)[::-1]
        pageStas=[widget.sta for widget in self.staWidgets]
        # Remove picks from pltLines (to keep ordering the same as pickSet)
        for idx in delIdxs:
            aLine=self.pltLines.pop(idx)
            # Remove the picks from the plot (if the station is currently plotted)
            sta=self.hotVar['pickSet'].val[idx][0]
            if sta in pageStas:
                self.staWidgets[pageStas.index(sta)].pltItem.removeItem(aLine)
        # Remove the picks from the hot variable pickSet
        keepIdxs=np.array([i for i in range(len(self.hotVar['pickSet'].val)) if i not in delIdxs])
        self.hotVar['pickSet'].val=self.hotVar['pickSet'].val[keepIdxs]
    
    # Return the wanted pick types pen, in RGB
    def getPickPen(self,aType):
        col=QtGui.QColor(self.pref['pickColor_'+aType].val)
        return (col.red(), col.green(), col.blue())
        
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
        
    # Load the pick file list for display
    def updatePickFileList(self):
        # Clear the old list
        self.archiveList.clear()
        self.hotVar['pickFiles'].val=[]
        # Only accept files with proper naming convention
        for aFile in sorted(os.listdir(self.hotVar['pickDir'].val)):
            splitFile=aFile.split('_')
            if len(splitFile)!=2 or aFile.split('.')[-1]!='picks':
                continue
            try:
                int(splitFile[0])
                getTimeFromFileName(aFile)
            except:
                continue
            self.hotVar['pickFiles'].val.append(aFile)
            self.archiveList.addItem(aFile)
    
    # As the number of pick types can change in the settings...
    # ...show less/more pick type color preferences
    def updatePickColorPrefs(self,init=False):
        curPickTypes=[key for key in self.pref['pickTypesMaxCountPerSta'].val]
        curPickColors=[key for key in self.pref.iteritems() if
                       ('pickColor_' in key and self.pref[key].dialog=='ColorDialog')]
        # Add the pick color preferences
        for aType in curPickTypes:
            # Do not overwrite if already present
            tag='pickColor_'+aType
            if tag in curPickColors:
                continue
            # Otherwise add the color
            self.pref[tag]=Pref(tag=tag,val=4294967295,dataType=int,dialog='ColorDialog')
            # If Lazylyst is starting, still have to load in the previous pick colors
            if init:
                prefVals=self.setPref.value('prefVals', {})
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
        self.pltLines=[] # To hold the vertical line objects on staWidgets
        
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
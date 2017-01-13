import logging
import sip
import sys,os
sip.setapi('QVariant', 2)
from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt,QSettings
from MainWindow import Ui_MainWindow
from Configuration import Ui_ConfDialog
from CustomWidgets import TraceWidget, keyPressToString
from HotVariables import initHotVar
from Preferences import defaultPreferences
from Actions import defaultActions, Action, ActionSetupDialog
from Archive import getArchiveAvail, getTimeFromFileName, extractDataFromArchive
from SaveSource import CsDialog
import numpy as np

# Main window class
class WaveViewer000(QtGui.QMainWindow, Ui_MainWindow):
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
        for key, aPref in self.pref.iteritems():
            aPref.update(self,init=True)
        
    # Start setting up some functionality to the UI
    def setFunctionality(self):
        # Give ability to the archive displays
        self.archiveList.graph=self.archiveWidget
        self.archiveList.graph.addNewEventSignal.connect(self.addPickFile)
        self.archiveList.clicked.connect(self.setFocus) # Do not let it steal focus from keybinds
        self.archiveList.doubleClicked.connect(self.loadEvent)
        # Allow stdout to be sent to the Trace Log
        XStream.stdout().messageWritten.connect(self.textOutBrowser.insertPlainText)
        XStream.stderr().messageWritten.connect(self.textOutBrowser.insertPlainText)
        self.textOutBrowser.textChanged.connect(self.scrollTextOut)
    
    # Report the current keybinds for the configuration and change source actions
    def introduction(self):
        print 'Press: '+self.act['ChangeSource'].trigger.toString()+' to change source (archive/picks/station metadata)'
        print 'Press: '+self.act['OpenOptions'].trigger.toString()+' to open the configuration dialog'
    
    # Function to handle key board input from user
    def keyPressEvent(self, ev):
        super(WaveViewer000, self).keyPressEvent(ev)
        keyname=keyPressToString(ev)
        if keyname==None:
            return
        # Loop through all actions and see if one is activated...
        # ... use the original set (an action may be added part way through, so can mess with the loop)
        actions=[action for key,action in self.act.iteritems()]
        for action in actions:
            if not action.passive and action.trigger.toString()==keyname:
                action.func(**action.optionals)
    
    # Open the configuration window
    def openConfiguration(self):
        self.dialog=ConfDialog(actions=self.act,pref=self.pref)
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
            
    # Load the current event
    def loadEvent(self):
        # Get the wanted time, and query for the data
        newPickFile=self.archiveList.currentItem().text()
        aTime=getTimeFromFileName(newPickFile).timestamp
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
                                        x=self.hotVar['pltSt'].val[idx].times()+self.hotVar['pltSt'].val[idx].stats.starttime.timestamp)
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
        
    # Update how many widgets are on the main page
    def updateStaPerPage(self):
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
        
    # Scroll the trace log to the bottom if an error occurs
    def scrollTextOut(self):
        scrollBar=self.textOutBrowser.verticalScrollBar()
        scrollBar.setValue(scrollBar.maximum())
    
    # Load setting from previous run, and initialize base variables
    def loadSettings(self):
        # Get this scripts path, as functions will be relative to this
        self.path=os.path.dirname(__file__)
        # Load the hot variables
        self.hotVar=initHotVar(self)
        for key,hotVar in self.hotVar.iteritems():
            hotVar.linkToFunction(self)
        # Get all values from settings
        self.settings = QSettings('settings.ini', QSettings.IniFormat)
        # ...UI size
        self.resize(self.settings.value('size', QtCore.QSize(1300, 700)))
        # ...Actions
        self.act=self.settings.value('actions', defaultActions())
        # Link all actions to their appropriate functions
        for key,action in self.act.iteritems():
            action.linkToFunction(self)
        # ...Preferences
        self.pref=defaultPreferences(self)
        prefVals=self.settings.value('prefVals', {})
        for aKey in prefVals.keys():
            self.pref[aKey].val=prefVals[aKey]
        # ...Saved sources
        self.saveSource=self.settings.value('savedSources', {})
        # Create empty variables
        self.staWidgets=[]
        
    # Save all settings from current run...
    def saveSettings(self):
        # ...UI size
        self.settings.setValue('size', self.size())
        # ...Actions, cannot save functions (will be linked again upon loading)
        for key in self.act.keys():
            self.act[key].func=None
        self.settings.setValue('actions',self.act)
        # ...Preferences
        prefVals={}
        for aKey in self.pref.keys():
            prefVals[self.pref[aKey].tag]=self.pref[aKey].val
        self.settings.setValue('prefVals',prefVals)
        # ...Saved sources
        self.settings.setValue('savedSources',self.saveSource)

    # When the GUI closes, will save to settings
    def closeEvent(self,ev):
        self.saveSettings()
        ev.accept()
        
# Configuration dialog
class ConfDialog(QtGui.QDialog, Ui_ConfDialog):
    def __init__(self,parent=None,actions={},pref={}):
        QtGui.QDialog.__init__(self,parent)
        self.setupUi(self)
        self.pref=pref
        self.act=actions
        # Give the dialog some functionaly
        self.setFunctionality()
        # Load in the previous lists of preferences and actions
        self.loadLists()
        
    # Set up some functionality to the configuration dialog
    def setFunctionality(self):
        self.confPrefList.keyPressedSignal.connect(self.listCalled)
        self.confActiveList.keyPressedSignal.connect(self.listCalled)
        self.confPassiveList.keyPressedSignal.connect(self.listCalled)
        self.confActiveList.setSortingEnabled(True)
    
    # Load in all of the lists from previous state
    def loadLists(self):
        self.confPrefList.loadList(sorted([key for key in self.pref.keys()]))
        self.confActiveList.loadList([key for key in self.act.keys() if not self.act[key].passive])
        self.confPassiveList.loadList([key for key in self.act.keys() if self.act[key].passive])
        
    # Function to handle calls to the configuration lists
    def listCalled(self):
        # If either of the action lists had focus
        action=None
        if self.confActiveList.hasFocus() or self.confPassiveList.hasFocus():
            curList=self.confActiveList if self.confActiveList.hasFocus() else self.confPassiveList
            startList='active' if self.confActiveList.hasFocus() else 'passive'
            # Skip if no accepted keys were passed
            if curList.key not in [Qt.Key_Insert,Qt.Key_Backspace,Qt.Key_Delete]:
                return
            # Creating a new action (Insert Key)
            elif curList.key==Qt.Key_Insert:
                if self.confActiveList.hasFocus():
                    action=self.openActionSetup(Action(passive=False,trigger=Qt.Key_questiondown))
                else:
                    action=self.openActionSetup(Action(passive=True))
            # Skip if no action was selected
            elif curList.currentItem()==None:
                print 'No action was selected'
            # Updating an action (Backspace Key)
            elif curList.key==Qt.Key_Backspace:
                action=self.openActionSetup(self.act[curList.currentItem().text()])   
            # Delete an action (Delete Key)
            elif curList.key==Qt.Key_Delete:
                actTag=curList.currentItem().text()
                # If this is a locked action, the user cannot delete it
                if self.act[actTag].locked:
                    print actTag+' is a built-in action, it cannot be deleted'
                    return
                # Remove from the list
                curList.takeItem(curList.currentRow())
                # As well as from the action dictionary
                self.act.pop(actTag)
        if action!=None:
            # If a new action was added, add the item to the appropriate list
            if curList.key==Qt.Key_Insert:
                if action.passive:
                    self.confPassiveList.addItem(action.tag)
                else:
                    self.confActiveList.addItem(action.tag)
            # ...otherwise, update the name of the new action
            else:
                # Remove the old action
                self.act.pop(curList.currentItem().text())
                # Check to see if the edit made it swap lists...
                # ...going from active to passive
                if (startList=='active' and action.passive):
                    curList.takeItem(curList.currentRow())
                    self.confPassiveList.addItem(action.tag)
                # ...going from passive to active
                elif (startList=='passive' and not action.passive):
                    curList.takeItem(curList.currentRow())
                    self.confActiveList.addItem(action.tag)
                # ...updating the original list
                else:
                    curList.currentItem().setText(action.tag)
            # Finally add to the action dictionary
            self.act[action.tag]=action
            
        # If the preference list had focus
        if self.confPrefList.hasFocus() and self.confPrefList.key==Qt.Key_Backspace:
            # Grab the key, and update if possible
            curKey=self.confPrefList.currentItem().text()
            self.pref[curKey].update(self)
                
    # Open the setup action dialog
    def openActionSetup(self,action):
        self.dialog=ActionSetupDialog(action,self.act)
        if self.dialog.exec_():
            action=self.dialog.returnAction()
            return action
            
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
    window = WaveViewer000()
    window.show()
    sys.exit(app.exec_())
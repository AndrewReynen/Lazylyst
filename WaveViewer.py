import logging
import sip
import sys,os
sip.setapi('QVariant', 2)
from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt,QSettings
from MainWindow import Ui_MainWindow
from Configuration import Ui_confDialog
from CustomWidgets import TraceWidget
from Preferences import defaultPreferences
from Actions import defaultActions, Action, ActionSetupDialog
from Archive import getArchiveAvail, getTimeFromFileName, extractDataFromArchive
import numpy as np

# Main window class
class WaveViewer000(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.loadSettings()
        self.applyPreferences()
        self.loadTest() ## Load values used for testing ##
        self.setFunctionality()
    
    # Go through all preferences, and call their update functions
    def applyPreferences(self):
        for key, aPref in self.pref.iteritems():
            aPref.update(self,init=True)
        
    # Start setting up some functionality to the UI
    def setFunctionality(self):
        # Load in the archive
        self.setArchive()
        self.updatePickFileList()
        # Give ability to the archive displays
        self.archiveList.graph=self.archiveWidget
        self.archiveList.graph.addNewEventSignal.connect(self.addPickFile)
        self.archiveList.doubleClicked.connect(self.loadEvent)
        # Allow stdout to be sent to the Trace Log
        XStream.stdout().messageWritten.connect(self.textOutBrowser.insertPlainText)
        XStream.stderr().messageWritten.connect(self.textOutBrowser.insertPlainText)
        self.textOutBrowser.textChanged.connect(self.scrollTextOut)
        
    def keyPressEvent(self, ev):
        super(WaveViewer000, self).keyPressEvent(ev)
        # Set up the forced key-bindings
        if ev.key()==Qt.Key_O:
            self.openConfiguration()
        else:
            return
    
    # Open the configuration window
    def openConfiguration(self):
        self.dialog=ConfDialog(actions=self.act,pref=self.pref)
        self.dialog.exec_()
    
    # Add an empty pick file to the pick directory, also add to GUI list
    def addPickFile(self):
        aTimeStr=self.archiveList.graph.newEveStr
        # Assign an ID to the new event
        seenIDs=[int(aFile.split('_')[0]) for aFile in os.listdir(self.picks['dir'])]
        i=0
        while i in seenIDs:
            i+=1
        newPickFile=str(i).zfill(10)+'_'+aTimeStr+'.picks'
        # Add to GUI list
        self.archiveList.addItem(newPickFile)
        # Add to the picks directory
        newFile=open(self.picks['dir']+'/'+newPickFile,'w')
        newFile.close()
        
    # Load the pick file list for display
    def updatePickFileList(self):
        # Clear the old list
        self.archiveList.clear()
        # Only accept files with proper naming convention
        for aFile in sorted(os.listdir(self.picks['dir'])):
            splitFile=aFile.split('_')
            if len(splitFile)!=2 or aFile.split('.')[-1]!='picks':
                continue
            try:
                int(splitFile[0])
                getTimeFromFileName(aFile)
            except:
                continue
            self.archiveList.addItem(aFile)
            
    # Load the current event
    def loadEvent(self):
        # Get the wanted time, and query for the data
        newPickFile=self.archiveList.currentItem().text()
        aTime=getTimeFromFileName(newPickFile).timestamp
        t1,t2=aTime+self.pref['evePreTime'].val,aTime+self.pref['evePostTime'].val
        self.stream=extractDataFromArchive(self.archive['dir'],t1,t2,self.archive['fileNames'],
                                           self.archive['fileTimes'],archiveFileLen=self.archive['fileLen'])
        # Make a copy for any filtering to be applied
        self.actVar['pltSt']=self.stream.copy()
        # Sort traces by channel so they are added in same order (relative other stations)
        self.actVar['pltSt'].sort(keys=['channel'])
        ## Alphabetical sorting for now ##
        self.actVar['staSort']=np.sort(np.unique([tr.stats.station for tr in self.stream]))
        # Move the axis time limit to the appropriate position
        minTime=np.min([tr.stats.starttime.timestamp for tr in self.stream])
        maxTime=np.max([tr.stats.endtime.timestamp for tr in self.stream])
        self.timeWidget.plotItem.setXRange(minTime,maxTime)
        # Add data to the trace widgets
        self.updatePage()
    
    # Update the entire page which includes data, picks, and sorting
    def updatePage(self):
        # Clear away all previous lines, and set the limits to the data
        for i in range(len(self.staWidgets)):
            self.staWidgets[i].clear()
        # Add in the trace data for the current page
        i=0
        stas=np.array([tr.stats.station for tr in self.actVar['pltSt']])
        numStas=len(np.unique(stas))
        while self.actVar['curPage']*self.pref['staPerPage'].val+i<numStas:
            if i==self.pref['staPerPage'].val:
                break
            # Figure out which traces are associated with the next station in staSort
            wantIdxs=np.where(stas==self.actVar['staSort'][self.actVar['curPage']*self.pref['staPerPage'].val+i])[0]
            # Also set the y-limits
            ymin=np.min([np.min(self.actVar['pltSt'][idx].data) for idx in wantIdxs])
            ymax=np.max([np.max(self.actVar['pltSt'][idx].data) for idx in wantIdxs])
            self.staWidgets[i].setYRange(ymin,ymax)
            # Plot the data
            for idx in wantIdxs:
                self.staWidgets[i].plot(y=self.actVar['pltSt'][idx].data,
                                        x=self.actVar['pltSt'][idx].times()+self.actVar['pltSt'][idx].stats.starttime.timestamp)
            i+=1
    
#    def setCurPage(self,nextPage=False,prevPage=False,pageNum=0):
        
    
    # Set the archive availability
    def setArchive(self):
        if not os.path.exists(self.archive['dir']):
            return
        # Load in all of the start times of the archive
        archiveFiles,archiveTimes=getArchiveAvail(self.archive['dir'])
        self.archive['fileNames']=archiveFiles
        self.archive['fileTimes']=archiveTimes
        if len(archiveFiles)==0:
            return
        # Update the time boxes
        if self.archive['loadMethod']=='fast':
            ranges=[[t,t+self.archive['fileLen']] for t in archiveTimes]
            self.archiveWidget.updateBoxes(ranges)
        else:
            print 'unsupported archive load method'
            return
        # Show the boundaries
        self.archiveWidget.t1=archiveTimes[0]
        self.archiveWidget.t2=archiveTimes[-1]+self.archive['fileLen']
        self.archiveWidget.updateBoundaries()
        
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
        # Finally reset the data on the page
        if self.stream!=None:
            self.updatePage()
        
    # Scroll the trace log to the bottom if an error occurs
    def scrollTextOut(self):
        scrollBar=self.textOutBrowser.verticalScrollBar()
        scrollBar.setValue(scrollBar.maximum())
        
    # Initialize variables which can be updated through actions ("hot variables")
    def initActVar(self):
        actVar={'staSort':[],'curPage':0,'pltSt':None}
        return actVar
        
    # If no previous archive was set, use these defaults
    def defaultArchive(self):
        archive={'dir':'','fileLen':1800,'loadMethod':'fast',
                 'fileNames':[],'fileTimes':[]}
        return archive
        
    # If no previous picks were set, use these defaults
    def defaultPicks(self):
        picks={'dir':'','files':[]}
        return picks
    
    # Load setting from previous run, and initialize base variables
    def loadSettings(self):
        # Load the hot variables
        self.actVar=self.initActVar()
        # Get all values from settings
        self.settings = QSettings('settings.ini', QSettings.IniFormat)
        # ...UI size
        self.resize(self.settings.value('size', QtCore.QSize(1300, 700)))
        # ...Actions, load in the custom actions enuring default actions are still present,
        self.act=self.settings.value('actions', {})
        origActions=defaultActions()
        for key,action in origActions.iteritems():
            if key not in self.act.keys():
                self.act[key]=action
        # then link all actions to their appropriate functions
        for key,action in self.act.iteritems():
            action.linkToFunction(self)
        # ...Preferences
        self.pref=defaultPreferences(self)
        prefVals=self.settings.value('prefVals', {})
        for aKey in prefVals.keys():
            self.pref[aKey].val=prefVals[aKey]
        # ...Archive information
        self.archive=self.settings.value('archive', self.defaultArchive())
        # ...Picks information
        self.picks=self.settings.value('picks', self.defaultPicks())
        # Create empty variables
        self.stream=None
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
        # ...Archive information
        self.settings.setValue('archive',self.archive)
        # ...Picks information
        self.settings.setValue('picks',self.picks)

    # When the GUI closes, will save to settings
    def closeEvent(self,event):
        self.saveSettings()
        event.accept()
        
    ## Test values ##
    def loadTest(self):
        self.archive['dir']='../../Archive'
        self.picks['dir']='./Picks'
        
# Configuration dialog
class ConfDialog(QtGui.QDialog, Ui_confDialog):
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
    
    # Load in all of the lists from previous state
    def loadLists(self):
        self.confPrefList.loadList(sorted([key for key in self.pref.keys()]))
        self.confActiveList.loadList([key for key in self.act.keys() if not self.act[key].passive])
        self.confPassiveList.loadList([key for key in self.act.keys() if self.act[key].passive])
        
    # Open the setup action dialog
    def listCalled(self):
        # If either of the action lists had focus
        action=None
        if self.confActiveList.hasFocus() or self.confPassiveList.hasFocus():
            curList=self.confActiveList if self.confActiveList.hasFocus() else self.confPassiveList
            # Skip if no accepted keys were passed
            if curList.key not in [Qt.Key_Insert,Qt.Key_Backspace,Qt.Key_Delete]:
                pass
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
                # Remove from the list
                curList.takeItem(curList.currentRow())
                # As well as from the action dictionary
                self.act.pop(actTag)
        if action!=None:
            # If a new action was added, add the item to list...
            if curList.key==Qt.Key_Insert:
                curList.addItem(action.tag)
            # ...otherwise, update the name of the new action
            else:
                self.act.pop(curList.currentItem().text())
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
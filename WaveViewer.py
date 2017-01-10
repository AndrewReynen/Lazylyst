import logging
import sip
import sys,os
sip.setapi('QVariant', 2)
from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt,QSettings
from MainWindow import Ui_MainWindow
from Configuration import Ui_confDialog
from ActionSetup import Ui_actionDialog
from CustomWidgets import TraceWidget
from archive import getArchiveAvail,getTimeFromFileName,extractDataFromArchive
import numpy as np

# Main window class
class WaveViewer000(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.loadSettings()
        self.loadTest() ## Load values used for testing ##
        self.setFunctionality()
        
    # Start setting up some functionality to the UI
    def setFunctionality(self):
        # Load in the archive
        self.setArchive()
        self.loadPickFileList()
        # Give ability to the archive displays
        self.archiveList.graph=self.archiveWidget
        self.archiveList.graph.addNewEventSignal.connect(self.addPickFile)
        self.archiveList.doubleClicked.connect(self.loadEvent)
        # Set up the key-bindings for the main window
        # Create the desired number of station widgets
        self.staWidgets=[]
        self.setStaPerPage()
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
        self.dialog=ConfDialog()
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
    def loadPickFileList(self):
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
        t1,t2=aTime+self.pref['evePreTime'],aTime+self.pref['evePostTime']
        self.stream=extractDataFromArchive(self.archive['dir'],t1,t2,self.archive['fileNames'],
                                           self.archive['fileTimes'],archiveFileLen=self.archive['fileLen'])
        # Make a copy for any filtering to be applied
        self.pltSt=self.stream.copy()
        ## Alphabetical sorting for now ##
        self.baseVar['staSort']=np.sort(np.unique([tr.stats.station for tr in self.stream]))
        # Move the axis time limit to the appropriate position
        minTime=np.min([tr.stats.starttime.timestamp for tr in self.stream])
        maxTime=np.max([tr.stats.endtime.timestamp for tr in self.stream])
        self.timeWidget.plotItem.setXRange(minTime,maxTime)
        # Add data to the trace widgets
        self.loadPage()
    
    # Given the current page number, data, and sorting
    def loadPage(self):
        # Sort traces by channel so they are added in same order (relative other stations)
        self.pltSt.sort(keys=['channel'])
        # Clear away all previous lines, and set the limits to the data
        for i in range(len(self.staWidgets)):
            self.staWidgets[i].clear()
        # Add in the trace data for the current page
        i=0
        stas=np.array([tr.stats.station for tr in self.pltSt])
        numStas=len(np.unique(stas))
        while self.baseVar['curPage']*self.pref['staPerPage']+i<numStas:
            if i==self.pref['staPerPage']:
                break
            # Figure out which traces are associated with the 
            wantIdxs=np.where(stas==self.baseVar['staSort'][self.baseVar['curPage']*self.pref['staPerPage']+i])[0]
            for idx in wantIdxs:
                self.staWidgets[i].plot(y=self.pltSt[idx].data,
                                        x=self.pltSt[idx].times()+self.pltSt[idx].stats.starttime.timestamp)
            i+=1
    
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
        
    # Set how many widgets are on the main page
    def setStaPerPage(self):
        while len(self.staWidgets)<self.pref['staPerPage']:
            self.staWidgets.append(TraceWidget(self.mainLayout))
            self.staWidgets[-1].setXLink('timeAxis')
            self.traceLayout.addWidget(self.staWidgets[-1])
        
    # Scroll the trace log to the bottom if an error occurs
    def scrollTextOut(self):
        scrollBar=self.textOutBrowser.verticalScrollBar()
        scrollBar.setValue(scrollBar.maximum())
        
    # Initialize some base variables
    def baseVar(self):
        baseVar={'staSort':[],'curPage':0}
        return baseVar
    
    # If no preferences were available, use these defaults
    def defaultPreferences(self):
        pref={'staPerPage':8,'evePreTime':-60,'evePostTime':120}
        return pref
        
    # If no previous archive was set, use these defaults
    def defaultArchive(self):
        archive={'dir':'','fileLen':1800,'loadMethod':'fast',
                 'fileNames':[],'fileTimes':[]}
        return archive
        
    # If no previous archive was set, use these defaults
    def defaultPicks(self):
        picks={'dir':'','files':[]}
        return picks
    
    # Load setting from previous run, and initialize base variables
    def loadSettings(self):
        # Base variables
        self.baseVar=self.baseVar()
        # Get all values from settings
        self.settings = QSettings('settings.ini', QSettings.IniFormat)
        # ...UI size
        self.resize(self.settings.value('size', QtCore.QSize(1300, 700)))
        # ...Preferences
        self.pref=self.settings.value('pref', self.defaultPreferences())
        # ...Archive information
        self.archive=self.settings.value('archive', self.defaultArchive())
        # ...Picks information
        self.picks=self.settings.value('picks', self.defaultPicks())
        
    # Save all settings from current run...
    def saveSettings(self):
        # ...UI size
        self.settings.setValue('size', self.size())
        # ...Preferences
        self.settings.setValue('pref',self.pref)
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
        self.archive['dir']='./Archive'
        self.picks['dir']='./Picks'
        
# Configuration dialog
class ConfDialog(QtGui.QDialog, Ui_confDialog):
    def __init__(self,parent=None):
        QtGui.QDialog.__init__(self,parent)
        self.setupUi(self)
        # Give the dialog some functionaly
        self.setFunctionality()
        
    # Set up some functionality to the configuration dialog
    def setFunctionality(self):
        self.confPrefList.keyPressedSignal.connect(self.listCalled)
        self.confActiveList.keyPressedSignal.connect(self.listCalled)
        self.confPassiveList.keyPressedSignal.connect(self.listCalled)
        
    # Open the setup action dialog
    def listCalled(self):
        # First check to see which list was called
        if self.confActiveList.hasFocus(): self.openActionSetup()
        if self.confPassiveList.hasFocus(): self.openActionSetup()
    
    # Open the setup action dialog
    def openActionSetup(self):
        self.dialog=ActionSetupDialog()
        self.dialog.exec_()
        
# Action setup dialog
class ActionSetupDialog(QtGui.QDialog, Ui_actionDialog):
    def __init__(self,parent=None):
        QtGui.QDialog.__init__(self,parent)
        self.setupUi(self)

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
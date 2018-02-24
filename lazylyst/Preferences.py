# Author: Andrew.M.G.Reynen
from __future__ import print_function
from copy import deepcopy
from future.utils import iteritems

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
import pyproj

from CustomFunctions import dict2Text, text2Dict
from CustomPen import Ui_customPenDialog
from BasePen import Ui_basePenDialog
from ComboDialog import Ui_comboBoxDialog
from MapProjDialog import Ui_mapProjDialog
from ListEntryDialog import Ui_listEntryDialog

# Default Preferences
def defaultPreferences(main):
    pref={
    'staPerPage':Pref(tag='staPerPage',val=6,dataType=int,
                      func=main.updateStaPerPage,condition={'bound':[1,30]},
                      tip='Number of stations (trace widgets) to display on each page'),
    'evePreTime':Pref(tag='evePreTime',val=-30,dataType=float,
                      tip='Time in seconds prior to the selected pick file names time to grab data'),
    'evePostTime':Pref(tag='evePostTime',val=60,dataType=float,
                      tip='Time in seconds after to the selected pick file names time to grab data'),
    'eveIdGenStyle':Pref(tag='eveIdGenStyle',val='next',dataType=str,
                         dialog='ComboBoxDialog',condition={'isOneOf':['fill','next']},
                         tip='Style used to generate a new empty pick files ID (when double clicking the archive event widget)'),
    'eveSortStyle':Pref(tag='eveSortStyle',val='time',dataType=str,
                        dialog='ComboBoxDialog',func=main.updateEveSort,condition={'isOneOf':['id','time']},
                        tip='How the archive list widget is sorted, also sorts hot variable pickFiles and pickTimes'),
    'cursorStyle':Pref(tag='cursorStyle',val='arrow',dataType=str,
                        dialog='ComboBoxDialog',func=main.updateCursor,condition={'isOneOf':['arrow','cross']},
                        tip='Cursor icon to use while hovering over plots'),
    'remExcessPicksStyle':Pref(tag='remExcessPicksStyle',val='oldest',dataType=str,
                        dialog='ComboBoxDialog',condition={'isOneOf':['oldest','closest','furthest']},
                        tip='Which excess pick(s) will be deleted when manually adding picks'),
    'mapProj':Pref(tag='mapProj',
                   val={'type':'Simple',
                        'epsg':'4326',
                        'simpleType':'AEA Conic',
                        'zDir':'end',
                        'units':'km',
                        'func':None,#lambda x:x,
                        'funcInv':None},#lambda x:x},
                    dataType=dict,
                    dialog='MapProjDialog',func=main.updateMapProj,
                    tip='Projection to be applied when converting Lat,Lon,Ele to X,Y,Z',
                    loadOrder=0),
    'pythonPathAdditions':Pref(tag='pythonPathAdditions',val=[],dataType=list,
                               dialog='ListEntryDialog',tip='Directories to add to the python path',
                               func=main.updatePythonPath),
    'pickTypesMaxCountPerSta':Pref(tag='pickTypesMaxCountPerSta',val={'P':1,'S':1},dataType=dict,
                                   func=main.updatePagePicks,condition={'bound':[1,999]},
                                   tip='Max number of picks of a given phase type allowed on any individual trace widget'),
    'basePen':Pref(tag='basePen',val={'widgetText':[14474460,1.0,0.0,False], # [Color,Width,Depth,UpdateMe]
                                      'traceBackground':[0,1.0,0.0,False],
                                      'timeBackground':[0,1.0,0.0,False],
                                      'imageBackground':[0,1.0,0.0,False],
                                      'imageBorder':[16777215,2.0,-1.0,False],
                                      'mapBackground':[0,1.0,0.0,False],
                                      'mapStaDefault':[16777215,4.0,0.0,False],
                                      'mapCurEve':[16776960,3.0,2.0,False],
                                      'mapPrevEve':[13107400,2.0,1.0,False],
                                      'mapPolygon':[3289800,1.0,10.0,False],
                                      'archiveBackground':[0,1.0,0.0,False],
                                      'archiveAvailability':[65280,1.0,0.0,False],
                                      'archiveSpanSelect':[3289800,1.0,0.0,False],
                                      'archiveCurEve':[16711680,3.0,1.0,False],
                                      'archivePrevEve':[48865,1.0,0.0,False],},
                    dataType=dict,dialog='BasePenDialog',func=main.updateBaseColors,
                    tip='Defines the base pen values for the main widgets'),
    'customPen':Pref(tag='customPen',val={'default':[16777215,1.0,0.0], # [Color,Width,Depth]
                                          'noStaData':[3289650,1.0,0.0],
                                          'noTraceData':[8224125,1.0,0.0],
                                          'goodMap':[65280,1.0,0.0],
                                          'poorMap':[16711680,1.0,0.0],
                                          'highlight':[255,1.0,2.0],
                                          'lowlight':[13158600,0.3,1.0],},dataType=dict,
                    dialog='CustomPenDialog',func=main.updateCustomPen,
                    tip='Defines the custom pen values referenced by PenAssign hot variables'),
    'pickPen':Pref(tag='pickPen',val={'default':[16777215,1.0,4.0],
                                      'P':[65280,1.0,5.0],
                                      'S':[16776960,1.0,5.0],},dataType=dict,
                    dialog='CustomPenDialog',func=main.updatePagePicks,
                    tip='Defines the pen values for the pick lines'),
    }
    return pref

# Capabilities for preferences
class Pref(object):
    def __init__(self,tag=None,val=None,dataType=str,
                 dialog='LineEditDialog',
                 func=None,condition={},tip='',loadOrder=999):
        self.tag=tag # The preference key, and user visible name
        self.val=val # The preference value
        self.dataType=dataType # What kind of data is expected upon update
        self.dialog=dialog # The dialog which will pop up to return a value
        self.func=func # Function which is called on successful updates
        self.condition=condition # Key-word conditionals (see "LineEditDialog" in this file) 
        self.tip=tip # Short description of the preference
        self.loadOrder=loadOrder # Priority in loading the preferencing (lower value loaded first)
    
    # Return a deep copy of the objects value
    def getVal(self):
        val=deepcopy(self.val)
        return val
    
    # If the key was asked to be updated
    def update(self,hostWidget,init=False):
        # If this is the original initalization, don't ask for new value
        if not init:
            # Use the correct dialog...
            # ...text entry dialog
            if self.dialog=='LineEditDialog':
                if self.dataType==dict:
                    initText=dict2Text(self.val)
                else:
                    initText=str(self.val)
                val,ok=LineEditDialog.returnValue(tag=self.tag,initText=initText,
                                                  condition=self.condition,
                                                  dataType=self.dataType)
            # ...selecting from a list
            elif self.dialog=='ComboBoxDialog':
                val,ok=ComboBoxDialog.returnValue(self.val,self.condition['isOneOf'],self.tag)                    
            # ...default widget colors
            elif self.dialog=='BasePenDialog':
                BasePenDialog(self.val).exec_()
                # The checks and updates to the preference value are done within the dialog
                val,ok=self.val,True
            # ...custom colors and widths
            elif self.dialog=='CustomPenDialog':
                CustomPenDialog(self.val,self.tag).exec_()
                # The checks and updates to the preference value are done within the dialog
                val,ok=self.val,True
            # ...defining the map projection
            elif self.dialog=='MapProjDialog':
                val,ok=ProjDialog.returnValue(self.val)
            # ...editing items on a list
            elif self.dialog=='ListEntryDialog':
                val,ok=ListDialog.returnValue(self.tag,self.val)
            else:
                print('New dialog?')
                val,ok=None,False
            # If the dialog was canceled, skip
            if not ok:
                return
            # If the no value was returned, skip
            if val==None:
                print('Value did not conform to '+str(self.dataType)+' and conditionals '+str(self.condition))
                return
            # Update the preference value
            self.val=val
        # If the value was updated, queue off its function
        if self.func!=None: 
            self.func(init=init)
            
# Dialog with line edit, allows for some initial text, and forced data type and condition
class LineEditDialog(QtWidgets.QDialog):
    def __init__(self,parent,tag,initText,condition,dataType):
        super(LineEditDialog, self).__init__(parent)
        self.setWindowTitle(tag)
        self.cond=condition
        self.dataType=dataType
        
        # Set up the layout and line edit
        layout = QtWidgets.QVBoxLayout(self)
        self.le = QtWidgets.QLineEdit(self)
        self.le.setText(initText)
        layout.addWidget(self.le)
        
        # OK and Cancel buttons
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
    # Get the text from the line edit
    def lineEditValue(self):
        val=self.le.text()
        # See first that the data type conforms
        try:
            # Allow user to type in the dictionary a bit easier
            if self.dataType==dict:
                val=text2Dict(val)
                if val=={}:
                    print('No keys are present in the dictionary')
                    return None
            else:
                val=self.dataType(val)
        except:
            return None
        # Loop through all values (usually just one, can be more for dictionary)
        if self.dataType==dict:
            vals=[aVal for key,aVal in iteritems(val)]
        else:
            vals=[val]
        # ...and check against the built in conditionals
        keys=[key for key in self.cond.keys()]
        for aVal in vals:
            if 'bound' in keys:
                if aVal<self.cond['bound'][0] or aVal>self.cond['bound'][1]:
                    return None
        return val

    # Static method to create the dialog and return value
    @staticmethod
    def returnValue(parent=None,tag='',initText='',condition={},dataType=str):
        dialog = LineEditDialog(parent,tag,initText,condition,dataType)
        result = dialog.exec_()
        return dialog.lineEditValue(), result==QtWidgets.QDialog.Accepted


# Dialog window for editing the basic widget colors
class BasePenDialog(QtWidgets.QDialog, Ui_basePenDialog):
    def __init__(self,tpDict,parent=None):
        QtWidgets.QDialog.__init__(self,parent)
        self.setupUi(self)
        self.tpDict=tpDict
        self.keyOrder=sorted(self.tpDict.keys()) # Used to reference back before the last user change
        # Fill in the current customPen information (before setting functionality, as functionality has a "onChanged" signal)
        self.fillDialog()
        # Give the dialog some functionaly
        self.setFunctionality()
        
    # Set up some functionality to the custom pen dialog
    def setFunctionality(self):
        self.tpTable.itemDoubleClicked.connect(self.updatePenColor)
        self.tpTable.itemChanged.connect(self.updateItemText)

    # Fill the dialog with info relating to the current customPen dictionary
    def fillDialog(self):
        # Make the table large enough to hold all current information
        self.tpTable.setRowCount(len(self.tpDict))
        self.tpTable.setColumnCount(4)
        # Set the headers
        self.tpTable.setHorizontalHeaderLabels(['Tag','Color','Width','Depth'])     
        # Enter data onto Table
        for m,key in enumerate(sorted(self.tpDict.keys())):
            # Generate the table items...
            tagItem=QtWidgets.QTableWidgetItem(key)
            tagItem.setFlags(Qt.ItemIsEnabled)
            penItem=QtWidgets.QTableWidgetItem('')
            penItem.setFlags(Qt.ItemIsEnabled)
            penItem.setBackground(QtGui.QColor(self.tpDict[key][0]))
            widItem=QtWidgets.QTableWidgetItem(str(self.tpDict[key][1]))
            depItem=QtWidgets.QTableWidgetItem(str(self.tpDict[key][2]))
            # Put items in wanted position
            self.tpTable.setItem(m,0,tagItem)
            self.tpTable.setItem(m,1,penItem)
            self.tpTable.setItem(m,2,widItem)
            self.tpTable.setItem(m,3,depItem)
        # Resize the dialog
        self.tpTable.resizeColumnsToContents()
            
    # Update the pen color for a given tag
    def updatePenColor(self,item):
        if item.column()!=1:
            return
        itemKey=self.keyOrder[item.row()]
        # Go get a new color
        colorDialog=QtWidgets.QColorDialog()
        val=colorDialog.getColor(QtGui.QColor(self.tpDict[itemKey][0]),self)
        # Set the new color (if the dialog was not canceled)
        if val.isValid():
            val=val.rgba()
            item.setBackground(QtGui.QColor(val))
            self.tpDict[itemKey][0]=val
            # Mark that this item was edited
            self.tpDict[itemKey][3]=True
            
    # Update the text values, if changed
    def updateItemText(self,item):
        if item.column()in [0,1]:
            return
        # The key, prior to changes
        itemKey=self.keyOrder[item.row()]
        # Updating the width or depth values
        if item.column() in [2,3]:
            prefIdx=item.column()-1
            try:
                val=float(item.text())
            except:
                val=-99999
            # Ensure the width value is reasonable, if not change back the original
            if prefIdx==1 and (val<0 or val>10):
                print('Width should be in the range [0,10]')
                item.setText(str(self.tpDict[itemKey][prefIdx]))
            elif prefIdx==2 and (val<-10 or val>=10):
                print('Depth should be in the range [-10,10)')
                item.setText(str(self.tpDict[itemKey][prefIdx]))
            # If passed checks, update the tpDict with the new width or depth
            else:
                self.tpDict[itemKey][prefIdx]=float(item.text())
                # Mark that this item was edited
                self.tpDict[itemKey][3]=True

# Dialog window for editing the custom colors and widths
class CustomPenDialog(QtWidgets.QDialog, Ui_customPenDialog):
    def __init__(self,tpDict,tag,parent=None):
        QtWidgets.QDialog.__init__(self,parent)
        self.setupUi(self)
        self.setWindowTitle(tag)
        self.tpDict=tpDict
        self.keyOrder=sorted(self.tpDict.keys()) # Used to reference back before the last user change
        # Fill in the current customPen information (before setting functionality, as functionality has a "onChanged" signal)
        self.fillDialog()
        # Give the dialog some functionaly
        self.setFunctionality()
        
    # Set up some functionality to the custom pen dialog
    def setFunctionality(self):
        self.tpTable.itemDoubleClicked.connect(self.updatePenColor)
        self.tpTable.itemChanged.connect(self.updateItemText)
        self.tpInsertButton.clicked.connect(self.insertPen)
        self.tpDeleteButton.clicked.connect(self.deletePen)

    # Fill the dialog with info relating to the current customPen dictionary
    def fillDialog(self):
        # Make the table large enough to hold all current information
        self.tpTable.setRowCount(len(self.tpDict))
        self.tpTable.setColumnCount(4)
        # Set the headers
        self.tpTable.setHorizontalHeaderLabels(['Tag','Color','Width','Depth'])     
        # Enter data onto Table
        for m,key in enumerate(sorted(self.tpDict.keys())):
            # Generate the table items...
            tagItem=QtWidgets.QTableWidgetItem(key)
            if key=='default':
                tagItem.setFlags(Qt.ItemIsEnabled)
            penItem=QtWidgets.QTableWidgetItem('')
            penItem.setFlags(Qt.ItemIsEnabled)
            penItem.setBackground(QtGui.QColor(self.tpDict[key][0]))
            widItem=QtWidgets.QTableWidgetItem(str(self.tpDict[key][1]))
            depItem=QtWidgets.QTableWidgetItem(str(self.tpDict[key][2]))
            # Put items in wanted position
            self.tpTable.setItem(m,0,tagItem)
            self.tpTable.setItem(m,1,penItem)
            self.tpTable.setItem(m,2,widItem)
            self.tpTable.setItem(m,3,depItem)
    
    # Update the pen color for a given tag
    def updatePenColor(self,item):
        if item.column()!=1:
            return
        itemKey=self.keyOrder[item.row()]
        # Go get a new color
        colorDialog=QtWidgets.QColorDialog()
        val=colorDialog.getColor(QtGui.QColor(self.tpDict[itemKey][0]),self)
        # Set the new color (if the dialog was not canceled)
        if val.isValid():
            val=val.rgba()
            item.setBackground(QtGui.QColor(val))
            self.tpDict[itemKey][0]=val
    
    # Update the text values, if changed
    def updateItemText(self,item):
        if item.column()==1:
            return
        # Disconnect itself, changes occur here weird looping otherwise
        self.tpTable.itemChanged.disconnect(self.updateItemText)
        # The key, prior to changes
        itemKey=self.keyOrder[item.row()]
        # Updating the width or depth values
        if item.column() in [2,3]:
            prefIdx=item.column()-1
            try:
                val=float(item.text())
            except:
                val=-99999
            # Ensure the width value is reasonable, if not change back the original
            if prefIdx==1 and (val<0 or val>10):
                print('Width should be in the range [0,10]')
                item.setText(str(self.tpDict[itemKey][prefIdx]))
            elif prefIdx==2 and (val<-10 or val>=10):
                print('Depth should be in the range [-10,10)')
                item.setText(str(self.tpDict[itemKey][prefIdx]))
            # If passed checks, update the tpDict with the new width or depth
            else:
                self.tpDict[itemKey][prefIdx]=float(item.text())
        # Updating the tag
        elif item.column()==0:
            # If the same, do nothing
            if item.text()==itemKey:
                pass
            # Do not allow duplicate tags
            elif item.text() in [key for key in self.tpDict.keys() if key!=itemKey]:
                print('This tag is already present, update denied')
                item.setText(itemKey)
            else:
                # If passed checks, update the tpDict with the new tag
                self.tpDict[str(item.text())]=self.tpDict[itemKey]
                self.tpDict.pop(itemKey)
                # Update the key order, so can reference back before changes
                self.keyOrder[item.row()]=str(item.text())
        # Reconnect to OnChanged signal
        self.tpTable.itemChanged.connect(self.updateItemText)
            
    # Insert a new pen
    def insertPen(self):        
        # If the "NewPen" key is still present, ask to change it...
        if 'NewPen' in [key for key in self.tpDict.keys()]:
            print('Change the tag "NewPen", to be able to add another custom pen"')
            return
        # Disconnect the OnChanged signal (as this would trigger it)
        self.tpTable.itemChanged.disconnect(self.updateItemText)
        # Add a row with the default parameters
        m=self.tpTable.rowCount()
        self.tpTable.setRowCount(m+1)
        self.tpTable.setItem(m,0,QtWidgets.QTableWidgetItem('NewPen'))
        penItem=QtWidgets.QTableWidgetItem('')
        penItem.setFlags(Qt.ItemIsEnabled)
        self.tpTable.setItem(m,1,penItem)
        self.tpTable.setItem(m,2,QtWidgets.QTableWidgetItem('1.0'))
        self.tpTable.setItem(m,3,QtWidgets.QTableWidgetItem('0.0'))
        # Add it also to the dictionary
        self.tpDict['NewPen']=[4294967295,1.0,0.0]
        # Update the keyOrder
        self.keyOrder.append('NewPen')
        # Reconnect to OnChanged signal
        self.tpTable.itemChanged.connect(self.updateItemText)
        
    # Delete the currently selected pen
    def deletePen(self):
        idx=self.tpTable.currentRow()
        key=str(self.tpTable.item(idx,0).text())
        # Not allowed to delete default
        if key=='default':
            print('Cannot delete the pen tagged default')
            return
        # Disconnect the OnChanged signal (as this would trigger it)
        self.tpTable.itemChanged.disconnect(self.updateItemText)
        self.tpTable.removeRow(idx)
        self.keyOrder.pop(idx)
        self.tpDict.pop(key)
        # Reconnect to OnChanged signal
        self.tpTable.itemChanged.connect(self.updateItemText)
        
# Dialog to get a specific date time back
class DateDialog(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super(DateDialog, self).__init__(parent)
        
        # Give a window title
        self.setWindowTitle('Date Time Select')

        layout = QtWidgets.QVBoxLayout(self)
        # Widget for editing the date
        self.datetime = QtWidgets.QDateTimeEdit(self)
        self.datetime.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        layout.addWidget(self.datetime)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # Get current date and time from the dialog
    def dateTime(self):
        return self.datetime.dateTime()

    # Static method to create the dialog and return [timestamp, accepted]
    @staticmethod
    def getDateTime(bound,parent = None):
        # Start dialog
        dialog = DateDialog(parent)
        # Set the previous string value
        prevDateTime=QtCore.QDateTime()
        prevDateTime.setTimeSpec(Qt.UTC)
        prevDateTime.setTime_t(int(bound))
        dialog.datetime.setDateTime(prevDateTime)
        # Get and return value
        result = dialog.exec_()
        dateTime=dialog.dateTime()
        dateTime.setTimeSpec(Qt.UTC)
        newBound = dateTime.toTime_t()
        return newBound, result == QtWidgets.QDialog.Accepted
        
# Dialog window for selecting one of a few options
class ComboBoxDialog(QtWidgets.QDialog, Ui_comboBoxDialog):
    def __init__(self,parent,curVal,acceptVals,tag):
        QtWidgets.QDialog.__init__(self,parent)
        self.setupUi(self)
        self.setWindowTitle(tag)
        # Fill in the combo dialog box
        self.comboBox.addItems(acceptVals)
        # Set the current text to be the current preference value
        index = self.comboBox.findText(curVal)
        if index >= 0:
            self.comboBox.setCurrentIndex(index)
        
    # Static method to create the dialog and return the selected value
    @staticmethod
    def returnValue(curVal,acceptVals,tag,parent=None):
        dialog=ComboBoxDialog(parent,curVal,acceptVals,tag)
        result=dialog.exec_()
        return dialog.comboBox.currentText(), result==QtWidgets.QDialog.Accepted

# Dialog to hold a list of strings
class ListDialog(QtWidgets.QDialog, Ui_listEntryDialog):
    def __init__(self,tag,initList,parent=None):
        QtWidgets.QDialog.__init__(self,parent)
        self.setupUi(self)
        # Set name of the preference being changed
        self.setWindowTitle(tag)
        self.setFunctionality()
        self.fillDialog(initList)
        
    # Set up some functionality to the list entry dialog
    def setFunctionality(self):
        self.entryAddButton.clicked.connect(lambda x:self.addEntry())
        self.entryDelButton.clicked.connect(self.removeEntry)
        self.entryListWidget.keyPressedSignal.connect(self.doKeyPress)
        
    # Fill the list with current preference entries
    def fillDialog(self,initList):
        for entry in initList:
            self.addEntry(entry)
        
    # Handle the keys given by the list widget
    def doKeyPress(self):
        if self.entryListWidget.key==Qt.Key_Insert:
            self.addEntry()
        elif self.entryListWidget.key==Qt.Key_Delete:
            self.removeEntry()
        elif self.entryListWidget.key==Qt.Key_Backspace:
            self.editEntry()
        
    # Remove an entry from the list
    def removeEntry(self):
        try:
            if not self.entryListWidget.currentItem().isSelected():
                return
            self.entryListWidget.takeItem(self.entryListWidget.currentRow())
        except:
            pass
    
    # Add an item to the list
    def addEntry(self,text='#NewEntry'):
        if text in self.entryListWidget.visualListOrder():
            return
        item=QtWidgets.QListWidgetItem()
        item.setText(text)
        # Allow the item to be edited by clicking on it
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.entryListWidget.addItem(item)
    
    # Edit an entry in the list
    def editEntry(self):
        index = self.entryListWidget.currentIndex()
        if index.isValid():
            item = self.entryListWidget.itemFromIndex(index)
            if not item.isSelected():
                item.setSelected(True)
            self.entryListWidget.edit(index)
    
    # Return the lists unique entries
    @staticmethod
    def returnValue(tag,initList):
        dialog=ListDialog(tag,initList)
        result=dialog.exec_()
        return list(set(dialog.entryListWidget.visualListOrder())),result==QtWidgets.QDialog.Accepted
    
# Dialog window for selecting the projection to be used on the map
class ProjDialog(QtWidgets.QDialog,Ui_mapProjDialog):
    def __init__(self,projDict,parent=None):
        QtWidgets.QDialog.__init__(self,parent)
        self.setupUi(self)
        self.projDict=projDict
        # Fill the dialog with current values
        self.fillDialog()
        # Give the dialog some functionality
        self.setFunctionality()
    
    # Set up some functionality to the action set up dialog
    def setFunctionality(self):
        self.epsgLineEdit.editingFinished.connect(self.checkValidEpsg)
        self.simpleProjComboBox.currentIndexChanged.connect(self.toggleUnitCombo)
        self.simpleProjRadio.clicked.connect(self.toggleProjType)
        self.customProjRadio.clicked.connect(self.toggleProjType)
        
    # Fill the dialog with info relating to the current map projection
    def fillDialog(self):
        # Fill combo boxes
        self.simpleProjComboBox.addItems(['None','AEA Conic','UTM'])
        # Set values with current projection...
        # ...current epsg code
        self.epsgLineEdit.setText(str(self.projDict['epsg']))
        # ...type of the projection (simple/custom)
        if self.projDict['type']=='Simple':
            self.simpleProjRadio.setChecked(True)
        else:
            self.customProjRadio.setChecked(True)
        self.setComboValue(self.simpleProjComboBox,self.projDict['simpleType'])
        # ...direction of the z-axis (positive up/down)
        self.zDirCheckBox.setChecked(self.projDict['zDir']=='end')
        # ...projection type and units
        self.toggleProjType()
        self.setComboValue(self.unitsComboBox,self.projDict['units'])
    
    # Set a combo lists value
    def setComboValue(self,comboBox,value):
        # Set the current text to be the current preference value
        index = comboBox.findText(value)
        if index >= 0:
            comboBox.setCurrentIndex(index)
        else:
            comboBox.setCurrentIndex(0)
    
    # Ensure EPSG code is valid
    def checkValidEpsg(self):
        if not self.epsgLineEdit.isEnabled():
            return
        curText=str(self.epsgLineEdit.text())
        # Ensure the code is an integer value
        try:
            int(curText)
            # Check if the EPSG code exists
            try:
                self.getProjFunc(curText)
                # If possible to get the code, toggle the units
                self.toggleUnitCombo()
                return
            except:
                print('The EPSG code was not valid')
        except:
            print('The EPSG code must be an integer value')
        # If got an invalid code revert to old value
        print('Reverting to intial EPSG')
        self.epsgLineEdit.setText(str(self.projDict['epsg']))
    
    # Get the projection function for a given EPSG code
    def getProjFunc(self,epsg):
        return pyproj.Proj(init='EPSG:'+epsg)
    
    # Get the current map projection dictionary
    def getCurProjDict(self):
        curDict={'type':'Simple' if self.simpleProjRadio.isChecked() else 'Custom',
                 'epsg':self.epsgLineEdit.text(),
                 'simpleType':self.simpleProjComboBox.currentText(),
                 'zDir':'end' if self.zDirCheckBox.isChecked() else 'enu',
                 'units':self.unitsComboBox.currentText(),
                 'func':None,
                 'funcInv':None}
        return curDict
    
    # Toggle between simple and custom projection types
    def toggleProjType(self):
        isSimple=self.simpleProjRadio.isChecked()
        self.epsgLineEdit.setEnabled(not isSimple)
        self.simpleProjComboBox.setEnabled(isSimple)
        # Toggle the available units (as can change between simple/custom)
        self.toggleUnitCombo()
        
    # Toggle which units are available for the current projection
    def toggleUnitCombo(self):
        curDict=self.getCurProjDict()
        self.unitsComboBox.clear()
        # If the projection is in degrees only
        if ((curDict['type']=='Simple' and curDict['simpleType']=='None') or
            (curDict['type']=='Custom' and self.getProjFunc(curDict['epsg']).is_latlong())):
            self.unitsComboBox.addItems(['deg'])
        else:
            self.unitsComboBox.addItems(['m','km','ft','yd','mi'])
            
    # Static method to create the dialog and return the selected value
    @staticmethod
    def returnValue(projDict):
        dialog=ProjDialog(projDict)
        result=dialog.exec_()
        # Recheck the projection
        dialog.checkValidEpsg()
        return dialog.getCurProjDict(),result==QtWidgets.QDialog.Accepted
        
        
        
        
        
        
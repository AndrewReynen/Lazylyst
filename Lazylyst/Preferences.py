# Copyright Andrew.M.G.Reynen
from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt
from CustomFunctions import dict2Text, text2Dict
from CustomPen import Ui_customPenDialog
from BasePen import Ui_basePenDialog
from ComboDialog import Ui_comboBoxDialog
from copy import deepcopy
from future.utils import iteritems

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
                        tip='Change the cursor icon'),
    'remExcessPicksStyle':Pref(tag='remExcessPicksStyle',val='oldest',dataType=str,
                        dialog='ComboBoxDialog',condition={'isOneOf':['oldest','closest','furthest']},
                        tip='Which excess pick(s) will be deleted when manually adding picks'),
    'staProjStyle':Pref(tag='staProjStyle',val='None',dataType=str,
                        dialog='ComboBoxDialog',func=main.updateStaLoc,condition={'isOneOf':['None','AEA Conic','UTM']},
                        tip='Projection method to be applied when converting Lat,Lon to X,Y'),
    'pickTypesMaxCountPerSta':Pref(tag='pickTypesMaxCountPerSta',val={'P':1,'S':1},dataType=dict,
                                   func=main.updatePagePicks,condition={'bound':[1,999]},
                                   tip='Max number of picks of a given phase type allowed on any individual trace widget'),
    'basePen':Pref(tag='basePen',val={'widgetText':[14474460,1.0,0.0,False], # [Color,Width,Depth,UpdateMe]
                                      'traceBackground':[0,1.0,0.0,False],
                                      'timeBackground':[0,1.0,0.0,False],
                                      'imageBackground':[0,1.0,0.0,False],
                                      'mapBackground':[0,1.0,0.0,False],
                                      'mapStaDefault':[16777215,4.0,0.0,False],
                                      'mapCurEve':[16776960,3.0,2.0,False],
                                      'mapPrevEve':[13107400,2.0,1.0,False],
                                      'archiveBackground':[0,1.0,0.0,False],
                                      'archiveAvailability':[65280,1.0,0.0,False],
                                      'archiveSpanSelect':[3289800,1.0,0.0,False],
                                      'archiveCurEve':[16711680,3.0,1.0,False],
                                      'archivePrevEve':[135,1.0,0.0,False],},
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
                 func=None,condition={},tip=''):
        self.tag=tag # The preference key, and user visible name
        self.val=val # The preference value
        self.dataType=dataType # What kind of data is expected upon update
        self.dialog=dialog # The dialog which will pop up to return a value
        self.func=func # Function which is called on successful updates
        self.condition=condition # Key-word conditionals (see "LineEditDialog" in this file) 
        self.tip=tip # Short description of the preference
    
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
class LineEditDialog(QtGui.QDialog):
    def __init__(self,parent,tag,initText,condition,dataType):
        super(LineEditDialog, self).__init__(parent)
        self.setWindowTitle(tag)
        self.cond=condition
        self.dataType=dataType
        
        # Set up the layout and line edit
        layout = QtGui.QVBoxLayout(self)
        self.le = QtGui.QLineEdit(self)
        self.le.setText(initText)
        layout.addWidget(self.le)
        
        # OK and Cancel buttons
        self.buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
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
        return dialog.lineEditValue(), result==QtGui.QDialog.Accepted


# Dialog window for editing the basic widget colors
class BasePenDialog(QtGui.QDialog, Ui_basePenDialog):
    def __init__(self,tpDict,parent=None):
        QtGui.QDialog.__init__(self,parent)
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
            tagItem=QtGui.QTableWidgetItem(key)
            tagItem.setFlags(Qt.ItemIsEnabled)
            penItem=QtGui.QTableWidgetItem('')
            penItem.setFlags(Qt.ItemIsEnabled)
            penItem.setBackground(QtGui.QColor(self.tpDict[key][0]))
            widItem=QtGui.QTableWidgetItem(str(self.tpDict[key][1]))
            depItem=QtGui.QTableWidgetItem(str(self.tpDict[key][2]))
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
        colorDialog=QtGui.QColorDialog()
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
class CustomPenDialog(QtGui.QDialog, Ui_customPenDialog):
    def __init__(self,tpDict,tag,parent=None):
        QtGui.QDialog.__init__(self,parent)
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
            tagItem=QtGui.QTableWidgetItem(key)
            if key=='default':
                tagItem.setFlags(Qt.ItemIsEnabled)
            penItem=QtGui.QTableWidgetItem('')
            penItem.setFlags(Qt.ItemIsEnabled)
            penItem.setBackground(QtGui.QColor(self.tpDict[key][0]))
            widItem=QtGui.QTableWidgetItem(str(self.tpDict[key][1]))
            depItem=QtGui.QTableWidgetItem(str(self.tpDict[key][2]))
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
        colorDialog=QtGui.QColorDialog()
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
        self.tpTable.setItem(m,0,QtGui.QTableWidgetItem('NewPen'))
        penItem=QtGui.QTableWidgetItem('')
        penItem.setFlags(Qt.ItemIsEnabled)
        self.tpTable.setItem(m,1,penItem)
        self.tpTable.setItem(m,2,QtGui.QTableWidgetItem('1.0'))
        self.tpTable.setItem(m,3,QtGui.QTableWidgetItem('0.0'))
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
class DateDialog(QtGui.QDialog):
    def __init__(self, parent = None):
        super(DateDialog, self).__init__(parent)
        
        # Give a window title
        self.setWindowTitle('Date Time Select')

        layout = QtGui.QVBoxLayout(self)
        # Widget for editing the date
        self.datetime = QtGui.QDateTimeEdit(self)
        self.datetime.setCalendarPopup(True)
        self.datetime.setDisplayFormat('yyyy-MM-dd hh:mm:ss')
        layout.addWidget(self.datetime)

        # OK and Cancel buttons
        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
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
        return newBound, result == QtGui.QDialog.Accepted
        
# Dialog window for selecting one of a few options
class ComboBoxDialog(QtGui.QDialog, Ui_comboBoxDialog):
    def __init__(self,parent,curVal,acceptVals,tag):
        QtGui.QDialog.__init__(self,parent)
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
        dialog = ComboBoxDialog(parent,curVal,acceptVals,tag)
        result = dialog.exec_()
        return dialog.comboBox.currentText(), result==QtGui.QDialog.Accepted
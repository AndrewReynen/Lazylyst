from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from CustomFunctions import dict2Text, text2Dict
from TracePen import Ui_tracePenDialog

# Default Preferences
def defaultPreferences(main):
    pref={
    'staPerPage':Pref(tag='staPerPage',val=6,dataType=int,
                      func=main.updateStaPerPage,condition={'bound':[1,30]}),
    'evePreTime':Pref(tag='evePreTime',val=-60,dataType=float),
    'evePostTime':Pref(tag='evePostTime',val=120,dataType=float),
    'archiveFileLen':Pref(tag='archiveFileLen',val=1800,dataType=float),
    'archiveLoadMethod':Pref(tag='archiveLoadMethod',val='fast'),
    'pickTypesMaxCountPerSta':Pref(tag='pickTypesMaxCountPerSta',val={'P':1,'S':1},dataType=dict,
                                   func=main.updatePickColorPrefs,condition={'bound':[1,999]}),
    'backgroundColorTrace':Pref(tag='backgroundColorTrace',val=0,dataType=int,
                                dialog='ColorDialog',func=main.updateTraceBackground),
    'backgroundColorTime':Pref(tag='backgroundColorTime',val=0,dataType=int,
                                dialog='ColorDialog',func=main.updateTimeBackground),
    'backgroundColorArchive':Pref(tag='backgroundColorArchive',val=0,dataType=int,
                                dialog='ColorDialog',func=main.updateArchiveBackground),
    'tracePen':Pref(tag='tracePen',val={'default':[4294967295,1.0]},dataType=dict,
                    dialog='TracePenDialog',func=main.updateTracePen),
    }
    return pref

# Capabilities for preferences
class Pref(object):
    def __init__(self,tag=None,val=None,dataType=str,
                 dialog='LineEditDialog',
                 func=None,condition={}):
        self.tag=tag # The preference key, and user visible name
        self.val=val # The preference value
        self.dataType=dataType # What kind of data is expected upon update
        self.dialog=dialog # The dialog which will pop up to return a value
        self.func=func # Function which is called on successful updates
        self.condition=condition # Key-word conditionals (see "LineEditDialog" in this file)
    
    # If the key was asked to be updated
    def update(self,hostWidget,init=False):
        # If this is the original initalization, don't ask for new value
        if not init:
            # Use the correct dialog
            if self.dialog=='LineEditDialog':
                if self.dataType==dict:
                    initText=dict2Text(self.val)
                else:
                    initText=str(self.val)
                val,ok=LineEditDialog.returnValue(tag=self.tag,initText=initText,
                                                  condition=self.condition,
                                                  dataType=self.dataType)
            # For singular valued colors
            elif self.dialog=='ColorDialog':
                colorDialog=QtGui.QColorDialog()
                val=colorDialog.getColor(QtGui.QColor(self.val),hostWidget)
                if val.isValid():
                    val,ok=val.rgba(),True
                else:
                    val,ok=None,False
            # For the trace colors and widths, with their associated tags for use as with hot variables
            elif self.dialog=='TracePenDialog':
                TracePenDialog(self.val).exec_()
                # The updates to the preference is done within the dialog (and the checks are done there)
                val,ok=self.val,True
            else:
                print 'New dialog?'
                val,ok=None,False
            # If the dialog was canceled, skip
            if not ok:
                return
            # If the no value was returned, skip
            if val==None:
                print 'Value did not conform to '+str(self.dataType)+' and conditionals '+str(self.condition)
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
                    print 'No keys are present in the dictionary'
                    return None
            else:
                val=self.dataType(val)
        except:
            return None
        # Loop through all values (usually just one, can be more for dictionary)
        if self.dataType==dict:
            vals=[aVal for key,aVal in val.iteritems()]
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

# Dialog window for editing the trace colors and widths
class TracePenDialog(QtGui.QDialog, Ui_tracePenDialog):
    def __init__(self,tpDict,parent=None):
        QtGui.QDialog.__init__(self,parent)
        self.setupUi(self)
        self.tpDict=tpDict
        self.keyOrder=sorted(self.tpDict.keys()) # Used to reference back before the last user change
        # Fill in the current tracePen information (before setting functionality, as functionality has a "onChanged" signal)
        self.fillDialog()
        # Give the dialog some functionaly
        self.setFunctionality()
        
    # Set up some functionality to the trace pen dialog
    def setFunctionality(self):
        self.tpTable.itemDoubleClicked.connect(self.updatePenColor)
        self.tpTable.itemChanged.connect(self.updateItemText)
        self.tpInsertButton.clicked.connect(self.insertPen)
        self.tpDeleteButton.clicked.connect(self.deletePen)

    # Fill the dialog with info relating to the current tracePen dictionary
    def fillDialog(self):
        # Make the table large enough to hold all current information
        self.tpTable.setRowCount(len(self.tpDict))
        self.tpTable.setColumnCount(3)
        # Set the headers
        self.tpTable.setHorizontalHeaderLabels(['Tag','Color','Width'])     
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
            # Put items in wanted position
            self.tpTable.setItem(m,0,tagItem)
            self.tpTable.setItem(m,1,penItem)
            self.tpTable.setItem(m,2,widItem)
    
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
        # Disconnect itself, changes occur herem weird looping otherwise
        self.tpTable.itemChanged.disconnect(self.updateItemText)
        # The key, prior to changes
        itemKey=self.keyOrder[item.row()]
        # Updating the width value
        if item.column()==2:
            try:
                width=float(item.text())
            except:
                width=-1
                print 'Width must be a number'
            # Ensure the width value is reasonable, if not change back the original
            if width<0 or width>10:
                print 'Width should be in the range [0,10]'
                item.setText(str(self.tpDict[itemKey][1]))
                return
            # If passed checks, update the tpDict with the new width
            else:
                self.tpDict[itemKey][1]=float(item.text())
        # Updating the tag
        elif item.column()==0:
            # If the same, do nothing
            if item.text()==itemKey:
                return
            # Do not allow duplicate tags
            if item.text() in [key for key in self.tpDict.keys() if key!=itemKey]:
                print 'This tag is already present, update denied'
                item.setText(itemKey)
                return
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
            print 'Change the tag "NewPen", to be able to add another trace pen"'
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
        # Add it also to the dictionary
        self.tpDict['NewPen']=[4294967295,1.0]
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
            print 'Cannot delete the pen tagged default'
            return
        # Disconnect the OnChanged signal (as this would trigger it)
        self.tpTable.itemChanged.disconnect(self.updateItemText)
        self.tpTable.removeRow(idx)
        self.keyOrder.pop(idx)
        self.tpDict.pop(key)
        # Reconnect to OnChanged signal
        self.tpTable.itemChanged.connect(self.updateItemText)
        print self.keyOrder
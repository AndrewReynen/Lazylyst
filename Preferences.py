from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from CustomFunctions import dict2Text, text2Dict

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
                             condition={'bound':[1,999]})
    }
    return pref

# Capabilities for preferences
class Pref(object):
    def __init__(self,tag=None,val=None,dataType=str,
                 dialog='LineEditDialog',
                 func=None,condition={}):
        self.tag=tag # The preference key, and user visible name
        self.dataType=dataType # What kind of data is expected upon update
        self.val=val # The preference value
        self.dialog='LineEditDialog' # The dialog which will pop up to return a value
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
                val,ok=LineEditDialog.returnValue(initText=initText,
                                                  condition=self.condition,
                                                  dataType=self.dataType)
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
            self.func()
            
# Dialog with line edit, allows for some initial text, and forced data type and condition
class LineEditDialog(QtGui.QDialog):
    def __init__(self,parent,initText,condition,dataType):
        super(LineEditDialog, self).__init__(parent)
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
    def returnValue(parent=None,initText='',condition={},dataType=str):
        dialog = LineEditDialog(parent,initText,condition,dataType)
        result = dialog.exec_()
        return dialog.lineEditValue(), result==QtGui.QDialog.Accepted
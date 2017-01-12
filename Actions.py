from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from ActionSetup import Ui_actionDialog

# Action setup dialog
class ActionSetupDialog(QtGui.QDialog, Ui_actionDialog):
    def __init__(self,action,actDict,parent=None):
        QtGui.QDialog.__init__(self,parent)
        self.setupUi(self)
        self.action=action # The action to update
        self.actDict=actDict # All other actions
        # Give the dialog some functionaly
        self.setFunctionality()
        # Load in the text to the related action
        self.fillDialog()
     
    # Set up some functionality to the action set up dialog
    def setFunctionality(self):
        self.actPassiveRadio.clicked.connect(self.togglePassiveActive)
        self.actActiveRadio.clicked.connect(self.togglePassiveActive)
        self.actTriggerLineEdit.keyPressed.connect(self.updateKeyBind)
    
    # Fill the dialog with info relating to action
    def fillDialog(self):
        # Fill in the text...
        # ...line edit entries
        self.actTagLineEdit.setText(self.action.tag)
        self.actNameLineEdit.setText(self.action.name)
        self.actPathLineEdit.setText(self.action.path)
        if self.action.passive:
            self.actTriggerLineEdit.setText(self.action.trigger)
        else:
            self.actTriggerLineEdit.setText(self.action.trigger.toString())
        # ...trigger list
        actTags=[action.tag for key,action in self.actDict.iteritems()]
        self.actTriggerList.addItems(sorted(actTags))
        # Set the appropriate radio button on
        if self.action.passive:
            self.actPassiveRadio.setChecked(True)
        else:
            self.actActiveRadio.setChecked(True)
        self.togglePassiveActive()
        # If started as a passive or action, do not allow the swap
        self.actPassiveRadio.setEnabled(False)
        self.actActiveRadio.setEnabled(False)
    
    # Update the key bind to what the user pressed
    def updateKeyBind(self,keyBindText):
        # Key binds are only used for active actions
        if self.actPassiveRadio.isChecked():
            return
        # If the key-bind is already in use, do not allow update
        for tag,action in self.actDict.iteritems():
            if action.trigger.toString()==keyBindText and action.tag!=self.action.tag:
                print action.tag+' already uses key-bind '+keyBindText
                return
        # Otherwise, update the trigger line edit (trigger value is updated upon close)
        self.actTriggerLineEdit.setText(keyBindText)
    
    # Depending on if this is an active or passive action, turn on/off some widgets
    def togglePassiveActive(self):
        if self.actActiveRadio.isChecked():
            self.passiveBeforeCheck.setEnabled(False)
            self.actTriggerList.setEnabled(False)
            self.actTriggerLineEdit.setReadOnly(True)
        else:
            self.passiveBeforeCheck.setEnabled(True)
            self.actTriggerList.setEnabled(True)
            self.actTriggerLineEdit.setReadOnly(True)
    
    # Upon close, fill in the action with all of the selected information and return
    def returnAction(self):
        self.action.tag=self.actTagLineEdit.text()
        self.action.name=self.actNameLineEdit.text()
        self.action.path=self.actPathLineEdit.text()
        self.action.passive=self.actPassiveRadio.isChecked()
        if self.action.passive:
            self.action.trigger=self.actTriggerLineEdit.text()
        else:
            self.action.trigger=QtGui.QKeySequence(self.actTriggerLineEdit.text())
        return self.action

# Default Actions
def defaultActions():
    act={
    'NextPage':Action(tag='NextPage',name='setCurPage',
                      path='$main',optionals={'nextPage':True},
                      trigger=Qt.Key_D),
    'PrevPage':Action(tag='PrevPage',name='setCurPage',
                      path='$main',optionals={'prevPage':True},
                      trigger=Qt.Key_A)                
    }
    return act

# Capabilities of an action
class Action(object):
    def __init__(self,tag='New action',name='Function name',
                 path='Add path to function',optionals={},
                 passive=False,beforeTrigger=False,
                 trigger='Add Trigger',func=None):
        self.tag=tag
        self.name=name
        self.path=path
        self.optionals=optionals
        self.passive=passive
        self.beforeTrigger=beforeTrigger
        self.trigger=trigger
        # convert the trigger to a key sequence, if the trigger was a key
        if type(trigger)==type(Qt.Key_1):
            self.trigger=QtGui.QKeySequence(self.trigger)
        self.func=func
    
    # When loading the previous settings, must link the action to its functions again
    def linkToFunction(self,main):
        print self.tag
        


from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from ActionSetup import Ui_actionDialog
import importlib
import os

# Default Actions
def defaultActions():
    act={
    'OpenOptions':Action(tag='OpenOptions',name='openConfiguration',
                      path='$main',
                      trigger=Qt.Key_O,locked=True),
    'ChangeSource':Action(tag='ChangeSource',name='openChangeSource',
                      path='$main',
                      trigger=Qt.Key_P,locked=True),
    'NextPage':Action(tag='NextPage',name='setCurPage',
                      path='$main',optionals={'nextPage':True},
                      trigger=Qt.Key_D,locked=True),
    'PrevPage':Action(tag='PrevPage',name='setCurPage',
                      path='$main',optionals={'prevPage':True},
                      trigger=Qt.Key_A,locked=True),  
    'Test':Action(tag='Test',name='testMe',
                      path='Functions.Testing.Testing',optionals={'value':True,'val2':5},
                      trigger=Qt.Key_T)  
    }
    return act

# Capabilities of an action
class Action(object):
    def __init__(self,tag='New action',name='Function name',
                 path='Add path to function',optionals={},
                 passive=False,beforeTrigger=False,
                 trigger='Add Trigger',func=None,locked=False):
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
        self.locked=locked
    
    # When loading the previous settings, must link the action to its functions again
    def linkToFunction(self,main):
        # If the path does not relate to already defined function locations
        if self.path not in ['$main']:
            # First check to see that the specified functions folder exists
            modPath=main.path+'/'+self.path.replace('.','/')
            funcDir=modPath[:-(len(self.path.split('.')[-1])+1)]
            if not os.path.exists(modPath+'.py'):
                print self.tag+' related module does not exist at path '+self.path
                return False
            # Next ensure that this path includes a __init__.py file
            elif not os.path.exists(funcDir+'/__init__.py'):
                print 'created __init__.py at '+funcDir
                initFile=open(funcDir+'/__init__.py','w')
                initFile.close()
            # Extract the function
            try:
                func = getattr(importlib.import_module(self.path),self.name)
            except:
                print self.tag+' did not load from '+self.path+'.'+self.name
                return False
        # Otherwise, grab function from predefined location
        else:
            try:
                if self.path=='$main':
                    func=getattr(main,self.name)
            except:
                print self.tag+' did not load from '+self.path+'.'+self.name
                return False
        # Assign the function to the action
        self.func=func
        return True
        
# Action setup dialog
class ActionSetupDialog(QtGui.QDialog, Ui_actionDialog):
    def __init__(self,action,actDict,parent=None):
        QtGui.QDialog.__init__(self,parent)
        self.setupUi(self)
        self.trigReminder=False # Used for reminder to user if toggling between active/passive
        self.action=action # The action to update
        self.actDict=actDict # All other actions
        # Give the dialog some functionaly
        self.setFunctionality()
        # Load in the text to the related action
        self.fillDialog()
        # Disable the majority of this gui if the action is locked
        if self.action.locked:
            self.lockDialog()
     
    # Set up some functionality to the action set up dialog
    def setFunctionality(self):
        self.actActiveRadio.clicked.connect(lambda: self.togglePassiveActive())
        self.actPassiveRadio.clicked.connect(lambda: self.togglePassiveActive())
        self.actTagLineEdit.hoverOut.connect(self.unqTagName)
        self.actTriggerLineEdit.keyPressed.connect(self.updateKeyBind)
        self.actTriggerList.itemDoubleClicked.connect(self.updatePassiveTrigger)
    
    # Fill the dialog with info relating to action
    def fillDialog(self):
        # Fill in the text...
        # ...line edit entries
        self.actTagLineEdit.setText(self.action.tag)
        self.actNameLineEdit.setText(self.action.name)
        self.actPathLineEdit.setText(self.action.path)
        # ...optionals line edit
        optStr=''
        for key,val in self.action.optionals.iteritems():
            optStr+=key+'='+str(val)+','
        if len(optStr)>0: optStr=optStr[:-1]
        self.actOptionalsLineEdit.setText(optStr)
        # ...trigger line edit entry
        if self.action.passive:
            self.actTriggerLineEdit.setText(self.action.trigger)
        else:
            self.actTriggerLineEdit.setText(self.action.trigger.toString())
        # ...trigger list, use only triggers which are active
        self.passiveTriggers=[action.tag for key,action in self.actDict.iteritems() if not action.passive]
        self.actTriggerList.addItems(sorted(self.passiveTriggers))
        # Set the appropriate radio button on
        if self.action.passive:
            self.actPassiveRadio.setChecked(True)
        else:
            self.actActiveRadio.setChecked(True)
        # Set the state of the beforeTrigger check box (used for passive only)
        if self.action.passive and self.action.beforeTrigger:
            self.passiveBeforeCheck.setChecked(True)
        else:
            self.passiveBeforeCheck.setChecked(False)
        # Toggle the appropriate radio button
        self.togglePassiveActive(init=True)
    
    # Lock the dialog so that values cannot be updated, for some built-in actions
    def lockDialog(self):
        for widget in [self.actNameLineEdit,self.actPathLineEdit,
                       self.actOptionalsLineEdit,self.actTriggerList,
                       self.actAvailInputList,self.actAvailReturnList,
                       self.actSelectInputList,self.actSelectReturnList,
                       self.actPassiveRadio,self.actActiveRadio,
                       self.passiveBeforeCheck]:
            widget.setEnabled(False)
    
    # Update the key bind to what the user pressed
    def updateKeyBind(self,keyBindText):
        # Key binds are only used for active actions
        if self.actPassiveRadio.isChecked():
            return
        # If the key-bind is already in use, do not allow update
        for tag,action in self.actDict.iteritems():
            # Only active actions have key-binds (do not need to check passive)
            if action.passive:
                continue
            if action.trigger.toString()==keyBindText and action.tag!=self.action.tag:
                print action.tag+' already uses key-bind '+keyBindText
                return
        # Otherwise, update the trigger line edit (trigger value is updated upon close)
        self.actTriggerLineEdit.setText(keyBindText)
    
    # Set the passive trigger to be the item selected from the available triggers
    def updatePassiveTrigger(self):
        self.actTriggerLineEdit.setText(self.actTriggerList.currentItem().text())
    
    # Depending on if this is an active or passive action, turn on/off some widgets
    def togglePassiveActive(self,init=False):
        if self.actActiveRadio.isChecked():
            self.passiveBeforeCheck.setEnabled(False)
            self.actTriggerList.setEnabled(False)
            self.actTriggerLineEdit.setReadOnly(True)
        else:
            self.passiveBeforeCheck.setEnabled(True)
            self.actTriggerList.setEnabled(True)
            self.actTriggerLineEdit.setReadOnly(True)
        # If the user has change from passive to active, remind that this will not be saved...
        # ...unless the trigger value is updated
        if (not self.trigReminder) and (not init):
            print 'If changing between active and passive, update the trigger value'
            self.trigReminder=True
            
    # Check the tag name to ensure that it doesn't conflict with other actions
    def unqTagName(self):
        curTag=self.actTagLineEdit.text()
        for tag,action in self.actDict.iteritems():
            if curTag==tag and action.tag!=self.action.tag:
                print 'This tag is already in use - if left as is changes will not be accepted'
                return False
        return True
        
    # Check that the trigger is appropriate relative to the action type
    def appropTrigger(self):
        # If a passive action, the trigger should be in the trigger list
        if self.actPassiveRadio.isChecked():
            if self.actTriggerLineEdit.text() not in self.passiveTriggers:
                return False
        # If a active action, the trigger should be able to convert to a key-bind
        else:
            try:
                QtGui.QKeySequence(self.actTriggerLineEdit.text())
            except:
                return False
        return True
    
    # Upon close, fill in the action with all of the selected information and return
    def returnAction(self):
        # First check to see that the new parameters make sense and the action is to be updated,
        # ... for now just checking that the tag is unique, and the trigger is appropriate
        if (not self.unqTagName()) or (not self.appropTrigger()):
            print 'Action update declined'
            return self.action
        # Set information from line edits...
        self.action.tag=self.actTagLineEdit.text()
        self.action.name=self.actNameLineEdit.text()
        self.action.path=self.actPathLineEdit.text()
        # ...optionals, set the values to the accepted format type (in order: bool,float,int,str)
        optText=self.actOptionalsLineEdit.text()
        if '=' in optText:
            try:
                optionals=dict(x.split('=') for x in optText.split(','))
                for key,val in optionals.iteritems():
                    # Do not convert numbers to bool
                    if val in ['True','False']:
                        optionals[key]=bool(val)
                    # Otherwise see if it is a number
                    try:
                        if '.' in val:
                            optionals[key]=float(val)
                        else:
                            optionals[key]=int(val)
                    # If none of the above, leave as a string
                    except:
                        continue
            except:
                print 'optionals were not formatted correctly, leaving as blank'
        else:
            optionals={}
        self.action.optionals=optionals
        # ...set whether this is an active or passive action
        self.action.passive=self.actPassiveRadio.isChecked()
        # ...trigger value
        if self.action.passive:
            self.action.trigger=self.actTriggerLineEdit.text()
        else:
            self.action.trigger=QtGui.QKeySequence(self.actTriggerLineEdit.text())
        # Set info from radio buttons (passive/active) 
        self.action.passive=self.actPassiveRadio.isChecked()
        # If the action should be applied before the trigger (used for passive only)
        if self.passiveBeforeCheck.isChecked():
            self.action.beforeTrigger=True
        # Note: linking to function will occur when self==$main
        return self.action
        
        
        
        


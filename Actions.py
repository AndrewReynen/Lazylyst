from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from ActionSetup import Ui_actionDialog
from CustomFunctions import dict2Text, text2Dict
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
    'PageNext':Action(tag='PageNext',name='tabCurPage',
                      path='$main',optionals={'nextPage':True},
                      trigger=Qt.Key_D,locked=True),
    'PagePrev':Action(tag='PagePrev',name='tabCurPage',
                      path='$main',optionals={'prevPage':True},
                      trigger=Qt.Key_A,locked=True),  
    'FiltHP1':Action(tag='FiltHP1',name='streamFilter',
                      path='Functions.Filters',optionals={'type':'highpass','freq':1,'corners':1,'zerophase':True},
                      trigger=QtGui.QKeySequence('Shift+Q'),inputs=['stream'],returns=['pltSt']),
    'ChangePickMode':Action(tag='ChangePickMode',name='togglePickMode',
                      path='Functions.General',
                      trigger=QtGui.QKeySequence('1'),inputs=['pickMode','pickTypesMaxCountPerSta'],returns=['pickMode']),
    'AddPick':Action(tag='AddPick',name='addClickPick',
                     path='$main',trigger='DoubleClick',locked=True),
    'PickFileSetToClick':Action(tag='PickFileGoToClick',name='setCurPickFile',
                                path='$main',trigger='DoubleClick',returns=['curPickFile'],locked=True),
    'PickFileNext':Action(tag='PickFileNext',name='setCurPickFile',optionals={'nextFile':True},
                          path='Functions.General',trigger=QtGui.QKeySequence('Shift+D'),locked=True,
                          inputs=['curPickFile','pickFiles'],returns=['curPickFile']),
    'PickFilePrev':Action(tag='PickFilePrev',name='setCurPickFile',optionals={'prevFile':True},
                          path='Functions.General',trigger=QtGui.QKeySequence('Shift+A'),locked=True,
                          inputs=['curPickFile','pickFiles'],returns=['curPickFile']),
    'SavePickSetOnDblClick':Action(tag='SavePickSetOnDblClick',name='savePickSet',
                                   path='Functions.General',passive=True,inputs=['pickDir','curPickFile','pickSet'],
                                   trigger='PickFileSetToClick',beforeTrigger=True),
    'SavePickSetOnNext':Action(tag='SavePickSetOnNext',name='savePickSet',
                               path='Functions.General',passive=True,inputs=['pickDir','curPickFile','pickSet'],
                               trigger='PickFileNext',beforeTrigger=True),
    'SavePickSetOnPrev':Action(tag='SavePickSetOnPrev',name='savePickSet',
                               path='Functions.General',passive=True,inputs=['pickDir','curPickFile','pickSet'],
                               trigger='PickFilePrev',beforeTrigger=True),
    }
    return act
    
# Return the action tags in alphabetical order...
# ...may be more customized later (by default)
def defaultPassiveOrder(actions):
    order=sorted([act.tag for tag,act in actions.iteritems() if act.passive])
    return order
    
# Capabilities of an action
class Action(object):
    def __init__(self,tag='New action',name='Function name',
                 path='Add path to function',optionals={},
                 passive=False,beforeTrigger=False,
                 trigger='Add Trigger',inputs=[],returns=[],
                 func=None,locked=False):
        self.tag=tag # User visible name for the action
        self.name=name # Function name
        self.path=path # Function path (uses "." instead of "\", path is relative main script location)
        self.optionals=optionals # Dictionary of the optional values which can be sent to the function
        self.passive=passive # If the action is passive, this is true
        self.beforeTrigger=beforeTrigger # If the passive function should be applied before/after the function
        self.trigger=trigger # Trigger of the action
        self.inputs=inputs # Hot variables to be sent as inputs to the function (in the correct order)
        self.returns=returns # Hot variables to be returned for update
        self.func=func # Function which is called upon trigger
        self.locked=locked # If the action is allowed to be altered (other than the trigger)
        # convert the trigger to a key sequence, if the trigger was a key
        if type(trigger)==type(Qt.Key_1):
            self.trigger=QtGui.QKeySequence(self.trigger)
    
    # When loading the previous settings, must link the action to its functions again
    def linkToFunction(self,main):
        # If the path does not relate to already defined function locations
        if self.path not in ['$main']:
            # First check to see that the specified functions folder exists
            modPath=main.path+'/'+self.path.replace('.','/')
            funcDir=modPath[:-(len(self.path.split('.')[-1])+1)]
            if not os.path.exists(modPath+'.py'):
                print self.tag+' related module does not exist at path '+self.path
                return
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
                return
        # Otherwise, grab function from predefined location
        else:
            try:
                if self.path=='$main':
                    func=getattr(main,self.name)
            except:
                print self.tag+' did not load from '+self.path+'.'+self.name
                return
        # Assign the function to the action
        self.func=func
        return
        
# Action setup dialog
class ActionSetupDialog(QtGui.QDialog, Ui_actionDialog):
    def __init__(self,main,action,actDict,hotVar,pref,parent=None):
        QtGui.QDialog.__init__(self,parent)
        self.setupUi(self)
        self.trigReminder=False # Used for reminder to user if toggling between active/passive
        self.main=main # The main window
        self.action=action # The action to update
        self.actDict=actDict # All other actions
        self.hotVar=hotVar # Inputs/returns to go to/from function
        self.pref=pref # Additional inputs to go to the function
        # Give the dialog some functionaly
        self.setFunctionality()
        # Load in the text to the related action
        self.fillDialog()
        # Disable the majority of this gui if the action is locked...
        if self.action.locked:
            self.lockDialog()
        # ...also, if this is only click event (double click for adding one pick)
        if self.action.trigger=='DoubleClick':
            self.actTriggerLineEdit.setEnabled(False)
     
    # Set up some functionality to the action set up dialog
    def setFunctionality(self):
        # For radio buttons, passive/active
        self.actActiveRadio.clicked.connect(lambda: self.togglePassiveActive())
        self.actPassiveRadio.clicked.connect(lambda: self.togglePassiveActive())
        # For the tag line edit, to remind if a tag is already being used
        self.actTagLineEdit.hoverOut.connect(self.unqTagName)
        # For the trigger line and list (which operate differently if action is passive/active)
        self.actTriggerLineEdit.keyPressed.connect(self.updateKeyBind)
        self.actTriggerList.itemDoubleClicked.connect(self.updatePassiveTrigger)
        # For the input/return, avail/select lists
        self.actAvailInputList.itemDoubleClicked.connect(lambda: self.addAvailVar('input'))
        self.actAvailReturnList.itemDoubleClicked.connect(lambda: self.addAvailVar('return'))
        self.actSelectInputList.keyPressedSignal.connect(lambda: self.removeSelectVar('input'))
        self.actSelectReturnList.keyPressedSignal.connect(lambda: self.removeSelectVar('return'))
    
    # Fill the dialog with info relating to action
    def fillDialog(self):
        # Fill in the text...
        # ...line edit entries
        self.actTagLineEdit.setText(self.action.tag)
        self.actNameLineEdit.setText(self.action.name)
        self.actPathLineEdit.setText(self.action.path)
        # ...optionals line edit
        self.actOptionalsLineEdit.setText(dict2Text(self.action.optionals))
        # ...trigger line edit entry
        if self.action.passive or self.action.trigger=='DoubleClick':
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
        # Fill in the available inputs and returns...
        # ...hot variables can go into inputs and outputs
        for key, hotVar in self.hotVar.iteritems():
            self.actAvailInputList.addItem(key)
            if hotVar.returnable:
                self.actAvailReturnList.addItem(key)
        # ...preferences are only allowed as inputs
        for key, pref in self.pref.iteritems():
            self.actAvailInputList.addItem(key)
        # Fill in the selected inputs and returns
        self.actSelectInputList.addItems(self.action.inputs)
        self.actSelectReturnList.addItems(self.action.returns)
    
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
            if action.passive or action.trigger=='DoubleClick':
                continue
            if action.trigger.toString()==keyBindText and action.tag!=self.action.tag:
                print action.tag+' already uses key-bind '+keyBindText
                return
        # Otherwise, update the trigger line edit (trigger value is updated upon close)
        self.actTriggerLineEdit.setText(keyBindText)
    
    # Set the passive trigger to be the item selected from the available triggers
    def updatePassiveTrigger(self):
        self.actTriggerLineEdit.setText(self.actTriggerList.currentItem().text())
    
    # Move the user chosen available hot variable or preference to the selected list
    def addAvailVar(self,listTag):
        # See which pair of lists was called
        if listTag=='return':
            fromList=self.actAvailReturnList
            toList=self.actSelectReturnList
        else:
            fromList=self.actAvailInputList
            toList=self.actSelectInputList
        # Add to the selected list, if the item is not already there
        text=fromList.currentItem().text()
        if text not in [toList.item(i).text() for i in range(toList.count())]:
            toList.addItem(text)
    
    # Removes the current item from a selected list of hot variables and/or preferences
    def removeSelectVar(self,listTag):
        # See which pair of lists was called
        if (listTag=='return' and self.actSelectReturnList.currentItem!=None and 
            self.actSelectReturnList.key==Qt.Key_Delete):
            self.actSelectReturnList.takeItem(self.actSelectReturnList.currentRow())
        elif (listTag=='input' and self.actSelectInputList.currentItem!=None and 
              self.actSelectInputList.key==Qt.Key_Delete):
            self.actSelectInputList.takeItem(self.actSelectInputList.currentRow())
            
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
        # ... for now just checking that the tag and the trigger are appropriate
        if self.action.trigger=='DoubleClick':
            print 'No changes can be made to actions with DoubleClick triggers'
            return None
        elif self.actTagLineEdit.text()=='New action':
            print 'Action update declined, tag was still default'
            return None
        elif not self.unqTagName():
            print 'Action update declined, tag is not unique'
            return None
        elif not self.appropTrigger():
            print 'Action update declined, trigger was not set'
            return None
        # Set information from line edits...
        self.action.tag=self.actTagLineEdit.text()
        self.action.name=self.actNameLineEdit.text()
        self.action.path=self.actPathLineEdit.text()
        # ...optionals, set the values to the accepted format type (in order: bool,float,int,str)
        optText=self.actOptionalsLineEdit.text()
        try:
            optionals=text2Dict(optText)
        except:
            print 'optionals were not formatted correctly, leaving as blank'
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
        # Collect the tags of the inputs and returns associated with the action
        self.action.inputs=self.actSelectInputList.visualListOrder()
        self.action.returns=self.actSelectReturnList.visualListOrder()
        # Try to link to the function (given the new path, and name)
        try:
            self.action.linkToFunction(self.main)
        except:
            print 'Failed to link '+self.action.tag+' to '+self.action.name+' at '+self.action.path 
        return self.action
        
        
        
        


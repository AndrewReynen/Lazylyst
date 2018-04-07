# Author: Andrew.M.G.Reynen
from __future__ import print_function
from future.utils import iteritems

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from lazylyst.UI.Configuration import Ui_ConfDialog
from Actions import Action, ActionSetupDialog

# Configuration dialog
class ConfDialog(QtWidgets.QDialog, Ui_ConfDialog):
    def __init__(self,parent=None,main=None,actions=None,
                 pref=None,hotVar=None):
        QtWidgets.QDialog.__init__(self,parent)
        self.setupUi(self)
        self.main=main
        self.pref=pref
        self.act=actions
        self.hotVar=hotVar
        # Give the dialog some functionaly
        self.setFunctionality()
        # Load in the previous lists of preferences and actions
        self.loadLists()
        
    # Set up some functionality to the configuration dialog
    def setFunctionality(self):
        # Key press events (also includes left double click)
        self.confPrefList.keyPressedSignal.connect(self.prefListKeyEvent)
        self.confActiveList.keyPressedSignal.connect(self.actionListKeyEvent)
        self.confPassiveList.keyPressedSignal.connect(self.actionListKeyEvent)
        # Right click menus for the action lists
        self.confActiveList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.confPassiveList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.confActiveList.customContextMenuRequested.connect(self.createActionMenu)
        self.confPassiveList.customContextMenuRequested.connect(self.createActionMenu)
        # If the ordering of the passive list ever changes, update actPassiveOrder
        self.confPassiveList.leaveSignal.connect(self.updatePassiveOrder)
        # Add and delete action buttons
        self.confActiveAddButton.clicked.connect(lambda: self.addDelClicked('active','add'))
        self.confActiveDelButton.clicked.connect(lambda: self.addDelClicked('active','del'))
        self.confPassiveAddButton.clicked.connect(lambda: self.addDelClicked('passive','add'))
        self.confPassiveDelButton.clicked.connect(lambda: self.addDelClicked('passive','del'))
    
    # Load in all of the lists from previous state
    def loadLists(self):
        # Add the passive actions in order
        for key in self.main.actPassiveOrder:
            self.confPassiveList.addItem(self.actionItem(key))
        # Add the active actions (will be alphabetically ordered)
        for key in [key for key in self.act.keys() if not self.act[key].passive]:
            self.confActiveList.addItem(self.actionItem(key))
        # Add the preferences
        for key in self.pref.keys():
            item=QtWidgets.QListWidgetItem()
            item.setText(key)
            self.setItemSleepColor(item,False)
            item.setToolTip(self.pref[key].tip)
            self.confPrefList.addItem(item)
            
    # Handle add and delete action button click...
    # ...mocks key press events
    def addDelClicked(self,whichList,addDel):
        # Set the appropriate current list
        self.curList=self.confActiveList if whichList=='active' else self.confPassiveList
        # Set the current lists button press
        self.curList.key=Qt.Key_Insert if addDel=='add' else Qt.Key_Delete
        # Forward this to the key press event handles
        self.actionListKeyEvent(mock=True)
            
    # Return which action list is in focus
    def getCurActionList(self):
        curList=None
        if self.confActiveList.hasFocus() or self.confPassiveList.hasFocus():
            curList=self.confActiveList if self.confActiveList.hasFocus() else self.confPassiveList
        return curList

    # Function to handle calls to the preference lists
    def prefListKeyEvent(self):
        # If the preference list had focus (again "backspace" is triggered by double click)
        if self.confPrefList.key==Qt.Key_Backspace:
            # Grab the key, and update if possible
            item=self.confPrefList.currentItem()
            if item.isSelected():
                self.pref[item.text()].update(self)
        
    # Function to handle calls to the active and passive lists
    def actionListKeyEvent(self,mock=False):
        # If this was not a mock event (ie. actually triggered by key press)
        if not mock:
            self.curList=self.getCurActionList()
        # See if either of the action lists had focus, otherwise skip
        if self.curList==None:
            return
        # Skip if no accepted keys were passed
        if self.curList.key not in [Qt.Key_Insert,Qt.Key_Backspace,Qt.Key_Delete]:
            return
        # Creating a new action (Insert Key)
        if self.curList.key==Qt.Key_Insert:
            self.createAction()
            return
        # Skip if no action was selected
        if self.curList.currentItem() is None:
            return
        if not self.curList.currentItem().isSelected():
            return
        # Mark if the current action is currently in use
        inUse=(self.curList.currentItem().text() in list(self.main.qTimers.keys())+list(self.main.qThreads.keys()))   
        # Updating an action (Backspace Key -> which is triggered by double click)
        if self.curList.key==Qt.Key_Backspace:
            self.updateAction(inUse=inUse)
        # Delete an action (Delete Key)
        elif self.curList.key==Qt.Key_Delete:
            self.deleteAction(inUse=inUse)
        # Update the passive order every time (ie. do not care how configuration dialog is closed)...
        # ...a passive action is added or edited
        self.updatePassiveOrder()
        
    # Assign the tool tip to an action
    def actionItem(self,key):
        item=QtWidgets.QListWidgetItem()
        item.setText(key)
        # Set the tip (which is the trigger value)
        if not self.act[key].passive:
            try:
                item.setToolTip('Keybind: '+self.act[key].trigger.toString())
            except:
                item.setToolTip('Keybind: '+self.act[key].trigger)
        else:
            self.setPassiveTip(item)
        # Set the color of the item displaying the sleep state
        self.setItemSleepColor(item,self.act[key].sleeping)
        return item
    
    # Set a passive items tip
    def setPassiveTip(self,item):
        triggers=self.act[item.text()].trigger
        # Don't fill the entire screen if many triggers
        if len(triggers)>3:
            item.setToolTip('Activated by: '+','.join(triggers[:3]+['...']))
        else:
            item.setToolTip('Activated by: '+','.join(triggers))
            
    # Update the selected action from the specified list
    def updateAction(self,inUse=False):
        # Let user know if edits will be accepted later
        if inUse:
            print('Only trigger edits are allowed as action is strolling or scheming')
        # Open the action set-up dialog with selected action
        action=self.openActionSetup(self.act[self.curList.currentItem().text()],tempLock=inUse)
        # Do not update if no action returned or action is in use
        if action==None or inUse:
            return
        # Remove the old action
        self.act.pop(self.curList.currentItem().text())
        # Update the action dictionary with new
        self.act[action.tag]=action
        # If the action change had anything to do with an active action
        if (self.curList==self.confActiveList and action.passive) or (not action.passive):
            self.curList.takeItem(self.curList.currentRow())
            oList=self.confPassiveList if action.passive else self.confActiveList
            oList.addItem(self.actionItem(action.tag))
        # Otherwise just update the existing passive item (to preserve the passive order)
        else:
            self.curList.currentItem().setText(action.tag)
            self.setPassiveTip(self.curList.currentItem())
    
    # Open the action set-up dialog with a blank new action
    def createAction(self):
        # Make the new action
        if self.confActiveList==self.curList:
            action=self.openActionSetup(Action(passive=False,trigger='Set Trigger'))
        else:
            action=self.openActionSetup(Action(passive=True,trigger=[]))
        self.insertLazyAction(action)
        
    # Insert a new action
    def insertLazyAction(self,action):
        if action==None:
            return
        # Insert new action to the action dictionary
        self.act[action.tag]=action
        # Create the item for the list widget
        item=self.actionItem(action.tag)
        # Add the action to the appropriate list
        if action.passive:
            self.confPassiveList.addItem(item)
        else:
            self.confActiveList.addItem(item)
    
    # Remove the selected action from the specified list
    def deleteAction(self,inUse=False):
        if inUse:
            print('Cannot delete an action which is strolling or scheming')
            return
        actTag=self.curList.currentItem().text()
        # If this is a locked action, the user cannot delete it
        if self.act[actTag].locked:
            print(actTag+' is a built-in action, it cannot be deleted')
            return
        # Remove from the list
        self.curList.takeItem(self.curList.currentRow())
        # As well as from the action dictionary
        self.act.pop(actTag)
    
    # Menu activated upon right clicking of action entries
    def createActionMenu(self,pos):
        # Get the key of the clicked on action
        self.curList=self.getCurActionList()
        item=self.curList.currentItem()
        if not item.isSelected():
            return
        self.menuAction=self.act[str(item.text())]
        # Can not edit locked actions, skip if locked        
        if self.menuAction.locked:
            print('Cannot sleep or copy locked actions')
            return
        # Create the menu, and fill with options...
        self.actionMenu= QtWidgets.QMenu()
        # ...sleep or awake
        if self.menuAction.sleeping:
            menuItem=self.actionMenu.addAction("Awake")
        else:
            menuItem=self.actionMenu.addAction("Sleep")
        menuItem.triggered.connect(self.toggleSleep)
        # ...copy the action
        menuItem=self.actionMenu.addAction("Copy")
        menuItem.triggered.connect(self.copyAction)
        # Move to cursor position and show
        parentPosition = self.curList.mapToGlobal(QtCore.QPoint(0, 0))       
        self.actionMenu.move(parentPosition + pos)
        self.actionMenu.show() 
    
    # Toggle the action sleeping state on/off
    def toggleSleep(self):
        item=self.curList.currentItem()
        if self.menuAction.sleeping:
            self.menuAction.sleeping=False
        else:
            self.menuAction.sleeping=True
        self.setItemSleepColor(item,self.menuAction.sleeping)
        
    # Set the color of a list widget item based on the actions sleeping state
    def setItemSleepColor(self,item,sleeping):
        if sleeping:
            item.setForeground(QtGui.QColor(150,150,150))
        else:
            item.setForeground(QtGui.QColor(40,40,40))
            
    # Copy an action, triggered from the action menu
    def copyAction(self):
        # Make a copy of the action
        newAction=Action()
        for key,val in iteritems(self.menuAction.__dict__):
            if key!='func':
                setattr(newAction,key,val)
        newAction.linkToFunction(self.main)
        # Set up the new actions tag
        seenKeys=self.act.keys()
        i=0
        while self.menuAction.tag+'('+str(i)+')' in seenKeys:
            i+=1
        # Assign the unique tag, and give a meaningless trigger (if an active action)
        newAction.tag=self.menuAction.tag+'('+str(i)+')'
        if not newAction.passive:
            print('Update '+newAction.tag+' trigger value, will be deleted upon configuration closure otherwise')
            newAction.trigger='Set Trigger'
        # Insert the copied action
        self.insertLazyAction(newAction)
    
    # Update the passive list ordering to what it seen by the user
    def updatePassiveOrder(self):
        self.main.actPassiveOrder=self.confPassiveList.visualListOrder()
                
    # Open the setup action dialog
    def openActionSetup(self,action,tempLock=False):
        self.dialog=ActionSetupDialog(self.main,action,self.act,
                                      self.hotVar,self.pref,tempLock)
        if self.dialog.exec_():
            action=self.dialog.returnAction()
            return action
    
    # On close, make sure that no new actions have incorrect triggers
    def closeEvent(self,ev):
        popKeys=[actKey for actKey in self.act.keys() if (self.act[actKey].trigger=='Set Trigger' and 
                                                          not self.act[actKey].passive)]
        for key in popKeys:
            print('Action '+key+' was removed, as its trigger value was not set')
            self.act.pop(key)
# Author: Andrew.M.G.Reynen
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from Configuration import Ui_ConfDialog
from Actions import Action, ActionSetupDialog
from copy import deepcopy

# Configuration dialog
class ConfDialog(QtGui.QDialog, Ui_ConfDialog):
    def __init__(self,parent=None,main=None,actions=None,
                 pref=None,hotVar=None):
        QtGui.QDialog.__init__(self,parent)
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
        self.confActiveList.connect(self.confActiveList,QtCore.SIGNAL("customContextMenuRequested(QPoint)" ),self.createActionMenu)
        self.confPassiveList.connect(self.confPassiveList,QtCore.SIGNAL("customContextMenuRequested(QPoint)" ),self.createActionMenu)
        # If the ordering of the passive list ever changes, update actPassiveOrder
        self.confPassiveList.leaveSignal.connect(self.updatePassiveOrder)
    
    # Load in all of the lists from previous state
    def loadLists(self):
        self.confActiveList.addItems([key for key in self.act.keys() if not self.act[key].passive])
        self.confPassiveList.addItems(self.main.actPassiveOrder)
        # Give tips for the preferences
        for key in self.pref.keys():
            item=QtGui.QListWidgetItem()
            item.setText(key)
            self.setItemSleepColor(item,False)
            item.setToolTip(self.pref[key].tip)
            self.confPrefList.addItem(item)
        # Set the colors of the action lists
        for aList in [self.confActiveList,self.confPassiveList]:
            for i in range(aList.count()):
                self.setItemSleepColor(aList.item(i),self.act[aList.item(i).text()].sleeping)
            
    # Return which action list is in focus
    def getCurActionList(self):
        curList=None
        if self.confActiveList.hasFocus() or self.confPassiveList.hasFocus():
            curList=self.confActiveList if self.confActiveList.hasFocus() else self.confPassiveList
        return curList
        
        
    # Function to handle calls to the active and passive lists
    def actionListKeyEvent(self):
        # See if either of the action lists had focus, otherwise skip
        self.curList=self.getCurActionList()
        if self.curList==None:
            return
        # Skip if no accepted keys were passed
        if self.curList.key not in [Qt.Key_Insert,Qt.Key_Backspace,Qt.Key_Delete]:
            return
        # Creating a new action (Insert Key)
        elif self.curList.key==Qt.Key_Insert:
            self.createAction()
        # Skip if no action was selected
        elif self.curList.currentItem()==None:
            print('No action was selected')
            return
        # Not allowed to edit any timed active action which is currently in use
        elif self.curList.currentItem().text() in self.main.qTimers.keys():
            print('Not allowed to change any timed active action which is currently in use')
            return
        # Updating an action (Backspace Key -> which is triggered by double click)
        elif self.curList.key==Qt.Key_Backspace:
            self.updateAction()
        # Delete an action (Delete Key)
        elif self.curList.key==Qt.Key_Delete:
            self.deleteAction()
        # Update the passive order every time (ie. do not care how configuration dialog is closed)...
        # ...a passive action is added or edited
        self.updatePassiveOrder()
            
    # Update the selected action from the specified list
    def updateAction(self):
        # Open the action set-up dialog with selected action
        action=self.openActionSetup(self.act[self.curList.currentItem().text()])
        if action==None:
            return
        # Remove the old action
        self.act.pop(self.curList.currentItem().text())
        # Check to see if the edit made it swap lists...
        # ...going from active to passive
        if (self.curList==self.confActiveList and action.passive):
            self.curList.takeItem(self.curList.currentRow())
            self.confPassiveList.addItem(action.tag)
        # ...going from passive to active
        elif (self.curList==self.confPassiveList and not action.passive):
            self.curList.takeItem(self.curList.currentRow())
            self.confActiveList.addItem(action.tag)
        # ...updating the original list
        else:
            self.curList.currentItem().setText(action.tag)
        # Update the action dictionary
        self.act[action.tag]=action
    
    # Open the action set-up dialog with a blank new action
    def createAction(self):
        # Make the new action
        if self.confActiveList.hasFocus():
            action=self.openActionSetup(Action(passive=False,trigger='Set Trigger'))
        else:
            action=self.openActionSetup(Action(passive=True,trigger=[]))
        self.insertLazyAction(action)
        
    # Insert a new action
    def insertLazyAction(self,action):
        if action==None:
            return
        # Create the item for the list widget
        item=QtGui.QListWidgetItem()
        item.setText(action.tag)
        self.setItemSleepColor(item,action.sleeping)
        # Add the action to the appropriate list
        if action.passive:
            self.confPassiveList.addItem(item)
        else:
            self.confActiveList.addItem(item)
        # Insert new action to the action dictionary
        self.act[action.tag]=action
    
    # Remove the selected action from the specified list
    def deleteAction(self):
        actTag=self.curList.currentItem().text()
        # If this is a locked action, the user cannot delete it
        if self.act[actTag].locked:
            print(actTag+' is a built-in action, it cannot be deleted')
            return
        # Remove from the list
        self.curList.takeItem(self.curList.currentRow())
        # As well as from the action dictionary
        self.act.pop(actTag)
    
    # Function to handle calls to the preference lists
    def prefListKeyEvent(self):
        # If the preference list had focus (again "backspace" is triggered by double click)
        if self.confPrefList.key==Qt.Key_Backspace:
            # Grab the key, and update if possible
            curKey=self.confPrefList.currentItem().text()
            self.pref[curKey].update(self)
    
    # Menu activated upon right clicking of action entries
    def createActionMenu(self,pos):
        # Get the key of the clicked on action
        self.curList=self.getCurActionList()
        self.menuAction=self.act[str(self.curList.currentItem().text())]
        # Can not edit locked actions, skip if locked        
        if self.menuAction.locked:
            return
        # Create the menu, and fill with options...
        self.actionMenu= QtGui.QMenu()
        # ...sleep or awake
        if self.menuAction.sleeping:
            menuItem=self.actionMenu.addAction("Awake")
        else:
            menuItem=self.actionMenu.addAction("Sleep")
        self.connect(menuItem, QtCore.SIGNAL("triggered()"), self.toggleSleep) 
        # ...copy the action
        menuItem=self.actionMenu.addAction("Copy")
        self.connect(menuItem, QtCore.SIGNAL("triggered()"), self.copyAction) 
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
            item.setTextColor(QtGui.QColor(150,150,150))
        else:
            item.setTextColor(QtGui.QColor(40,40,40))
            
    # Copy an action, triggered from the action menu
    def copyAction(self):
        seenKeys=self.act.keys()
        # Set up the new actions tag
        i=0
        while self.menuAction.tag+'('+str(i)+')' in seenKeys:
            i+=1
        # Assign the unique tag, and give a meaningless trigger (if an active action)
        try:
            newAction=deepcopy(self.menuAction)
        except:
            print('Failed to copy action '+str(self.menuAction.tag))
            return
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
    def openActionSetup(self,action):
        self.dialog=ActionSetupDialog(self.main,action,self.act,
                                      self.hotVar,self.pref)
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
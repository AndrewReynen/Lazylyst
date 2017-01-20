from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from Configuration import Ui_ConfDialog
from Actions import Action, ActionSetupDialog

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
        self.confPrefList.keyPressedSignal.connect(self.prefCalled)
        self.confActiveList.keyPressedSignal.connect(self.listCalled)
        self.confPassiveList.keyPressedSignal.connect(self.listCalled)
        # If the ordering of the passive list ever changes, update actPassiveOrder
        self.confPassiveList.leaveSignal.connect(self.updatePassiveOrder)
    
    # Load in all of the lists from previous state
    def loadLists(self):
        self.confPrefList.addItems([key for key in self.pref.keys()])
        self.confActiveList.addItems([key for key in self.act.keys() if not self.act[key].passive])
        self.confPassiveList.addItems(self.main.actPassiveOrder)
        
    # Function to handle calls to the active and passive lists
    ## May want to split this up... getting pretty rediculous ##
    def listCalled(self):
        # If either of the action lists had focus
        action=None
        if self.confActiveList.hasFocus() or self.confPassiveList.hasFocus():
            curList=self.confActiveList if self.confActiveList.hasFocus() else self.confPassiveList
            startList='active' if self.confActiveList.hasFocus() else 'passive'
            # Skip if no accepted keys were passed
            if curList.key not in [Qt.Key_Insert,Qt.Key_Backspace,Qt.Key_Delete]:
                return
            # Creating a new action (Insert Key)
            elif curList.key==Qt.Key_Insert:
                # If the action is sent from user, but has not changed - ignore
                if self.confActiveList.hasFocus():
                    action=self.openActionSetup(Action(passive=False,trigger=Qt.Key_questiondown))
                else:
                    action=self.openActionSetup(Action(passive=True,trigger=[]))
            # Skip if no action was selected
            elif curList.currentItem()==None:
                print 'No action was selected'
            # Updating an action (Backspace Key -> which is triggered by double click)
            elif curList.key==Qt.Key_Backspace:
                action=self.openActionSetup(self.act[curList.currentItem().text()])   
            # Delete an action (Delete Key)
            elif curList.key==Qt.Key_Delete:
                actTag=curList.currentItem().text()
                # If this is a locked action, the user cannot delete it
                if self.act[actTag].locked:
                    print actTag+' is a built-in action, it cannot be deleted'
                    return
                # Remove from the list
                curList.takeItem(curList.currentRow())
                # As well as from the action dictionary
                self.act.pop(actTag)
        if action!=None:
            # If a new action was added, add the item to the appropriate list
            if curList.key==Qt.Key_Insert:
                if action.passive:
                    self.confPassiveList.addItem(action.tag)
                else:
                    self.confActiveList.addItem(action.tag)
            # ...otherwise, update the name of the new action
            else:
                # Remove the old action
                self.act.pop(curList.currentItem().text())
                # Check to see if the edit made it swap lists...
                # ...going from active to passive
                if (startList=='active' and action.passive):
                    curList.takeItem(curList.currentRow())
                    self.confPassiveList.addItem(action.tag)
                # ...going from passive to active
                elif (startList=='passive' and not action.passive):
                    curList.takeItem(curList.currentRow())
                    self.confActiveList.addItem(action.tag)
                # ...updating the original list
                else:
                    curList.currentItem().setText(action.tag)
            # Finally add to the action dictionary
            self.act[action.tag]=action
            # Update the passive order every time (ie. do not care how configuration dialog is closed)...
            # ...a passive action is added or edited
            if action.passive:
                self.updatePassiveOrder()
                
    # Function to handle calls to the preference lists
    def prefCalled(self):
        # If the preference list had focus
        if self.confPrefList.key==Qt.Key_Backspace:
            # Grab the key, and update if possible
            curKey=self.confPrefList.currentItem().text()
            self.pref[curKey].update(self)
    
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
import sys

import numpy as np

from PyQt5 import QtWidgets,QtCore

class SourceDictWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent = None):
        QtWidgets.QTreeWidget.__init__(self, parent)
        self.resize(500, 200)
        self.setColumnCount(3)
        self.setHeaderLabels(["Name", "Type", "Value"])
        self.itemChanged.connect(self.checkEdits)
        # Value of an item prior to edit
        self.oldVal=''
        # Allowed variable data types
        self.varTypes=['str','int','float',
                       'array(str)',
                       'array(int)',
                       'array(float)']
        self.varConverts=[str,int,float,
                          lambda x: np.array(x.split(','),dtype=str),
                          lambda x: np.array(x.split(','),dtype=int),
                          lambda x: np.array(x.split(','),dtype=float)]
        
    # Keep default mouse presses
    def clickEvent(self,event):
        QtWidgets.QTreeWidget.mousePressEvent(self,event)
        # Clear selection if nothing clicked
        if self.itemAt(event.pos()) is None:
            self.clearSelection()

    def mousePressEvent(self, event):
        self.clickEvent(event)
        # If wanting to make add/remove an item (right click)
        if event.button() == QtCore.Qt.RightButton:
            self.createMenu(event)
    
    # Make a note of values prior to edits
    def mouseDoubleClickEvent(self,event):
        self.clickEvent(event)
        curItem=self.selectedItem()
        # Do nothing if no item selected
        if curItem is None:
            return
        # Allow group name to be edited, and the variable name/value
        curCol=self.currentColumn()
        if (curItem.parent() is None and curCol==0) or curCol!=1:
            self.oldVal=curItem.text(curCol)
            self.editItem(curItem,curCol)

    # Return list of the current group names
    def currentGroupNames(self):
        return[self.topLevelItem(i).text(0) for i in range(self.topLevelItemCount())]
    
    # Return list of the variable names in a given group item
    def currentVariableNames(self,groupItem):
        return [groupItem.child(i).text(0) for i in range(groupItem.childCount())]

    # Generate widget for a new group 
    def addGroup(self,groupName='NewGroup'):
        # Check to see that the default name is not taken
        if groupName in self.currentGroupNames():
            print('Name "'+groupName+'" already taken, edit before adding')
            return
        groupItem=QtWidgets.QTreeWidgetItem([groupName,'',''])
        # Allow the item to be edited
        groupItem.setFlags(groupItem.flags() | QtCore.Qt.ItemIsEditable)
        self.addTopLevelItem(groupItem)
        return groupItem
    
    # Generate widget for a new variable within a group
    def addVariable(self,groupItem,varName='NewVariable',varVal=None):
        # Check to see that the default name is not taken
        if varName in self.currentVariableNames(groupItem):
            print('Name "'+varName+'" already taken, edit before adding')
            return
        varText,varType=self.getVarTextAndType(varVal)
        # Give default values for new variable
        varItem=QtWidgets.QTreeWidgetItem([varName,'',varText])
        # Allow the item to be edited
        varItem.setFlags(varItem.flags() | QtCore.Qt.ItemIsEditable)
        # Add the variable to the group
        groupItem.addChild(varItem)
        # Show what types are accepted
        comboBox=QtWidgets.QComboBox()
        comboBox.addItems(self.varTypes)
        # Set the current combo item
        comboBox.setCurrentIndex(self.varTypes.index(varType))
        self.setItemWidget(varItem,1,comboBox)
        # Connect to check edits if this value is changed
        comboBox.currentIndexChanged.connect(lambda: self.checkEdits(varItem,1))
        comboBox.highlighted.connect(lambda: self.setOldVal(comboBox.itemText(comboBox.currentIndex())))
    
    def setOldVal(self,val):
        self.oldVal=val
    
    # Import and display a given source dictionary
    def showSourceDict(self,sourceDict):
        for groupName in sourceDict.keys():
            groupItem=self.addGroup(groupName=groupName)
            for varName in sourceDict[groupName].keys():
                self.addVariable(groupItem,varName=varName,
                                 varVal=sourceDict[groupName][varName])
    
    # Remove currently selected group
    def removeGroup(self,item):
        self.takeTopLevelItem(self.indexFromItem(item).row())
    
    # Remove currently selected variable
    def removeVariable(self,item):
        item.parent().takeChild(self.indexFromItem(item).row())
        
    # Get the user visible value from the value and variable type 
    def getVarTextAndType(self,val):
        # If the value is none, convert to string
        if val is None:
            return '','str'
        # Check first if a numpy array
        if type(val)==type(np.array([])):
            for aType in ['float','int','str']:
                match='|S' if aType=='str' else aType
                if match in str(val.dtype):
                    if len(val.shape)==0:
                        return str(val),'array('+aType+')'
                    else:
                        return ','.join(val.astype(str)),'array('+aType+')'
        # Otherwise check float,int,str
        for i in range(3)[::-1]:
            try:
                self.varConverts[i](val)
                return str(val),self.varTypes[i]
            except:
                continue
        return str(val),'str'
        
    # Convert the variable value to its appropriate type
    def stringToVarType(self,item):
        comboBox=self.itemWidget(item,1)
        varType=comboBox.itemText(comboBox.currentIndex())
        convertFunc=self.varConverts[self.varTypes.index(varType)]
        if item.text(2).replace(' ','')=='':
            return None
        else:
            return convertFunc(item.text(2))
    
    # Revert to an older value
    def revertEdits(self,item,col,message):
        # Disconnect from changed edits, revert to old value, reconnect
        print(message)
        self.itemChanged.disconnect(self.checkEdits)
        item.setText(col,self.oldVal)
        self.itemChanged.connect(self.checkEdits)
    
    # Check recent edits for errors
    def checkEdits(self,item,col):
        # Ensure names are unique
        if col==0:
            # Make a list of the names currently present
            if item.parent() is None:
                takenNames=self.currentGroupNames()
            else:
                takenNames=self.currentVariableNames(item.parent())
            # If name already taken, revert to old
            if np.sum(np.array(takenNames,dtype=str)==str(item.text(col)))>1:
                self.revertEdits(item,col,'Name already taken')
        # Ensure type matches the value
        elif col==1 and item.parent() is not None:
            # Do not check if string (should always work)
            comboBox=self.itemWidget(item,1)
            if comboBox.itemText(comboBox.currentIndex())=='str':
                return
            try:
                self.stringToVarType(item)
            except Exception as error:
                # Disconnect from changed edits, revert to type string, reconnect
                print(str(error)+', reverting to old type')
                comboBox.setCurrentIndex(self.varTypes.index(self.oldVal))
        # Ensure value matches the type
        elif col==2 and item.parent() is not None:
            try:
                self.stringToVarType(item)
            except Exception as error:
                self.revertEdits(item,col,str(error)+', reverting to old value')
    
    # Get the currently selected item
    def selectedItem(self):
        items=self.selectedItems()
        if len(items)==0:
            return None
        else:
            return items[0]
    
    # Create pop up menu to add/remove groups/variables
    def createMenu(self,event, parent=None):
        self.menu=QtWidgets.QMenu(parent)
        self.menu.addAction('Add Group', self.addGroup)
        if self.selectedItem() is not None:
            if self.selectedItem().parent() is None:
                self.menu.addAction('Add Variable',lambda: self.addVariable(self.selectedItem()))
                self.menu.addSeparator()
                self.menu.addAction('Remove Group',lambda: self.removeGroup(self.selectedItem()))
            elif self.selectedItem().parent().parent() is None:
                self.menu.addAction('Add Variable',lambda: self.addVariable(self.selectedItem().parent()))
                self.menu.addSeparator()
                self.menu.addAction('Remove Variable',lambda: self.removeVariable(self.selectedItem()))
        self.menu.move(self.mapToGlobal(QtCore.QPoint(0,0))+event.pos())
        self.menu.show() 

if __name__ == '__main__':
    
    app = 0
    if QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication.instance()
    else:
        app = QtWidgets.QApplication(sys.argv) 

    w = QtWidgets.QWidget()
    tw = SourceDictWidget(w)
    
    inDict={'G1':{'A1':'ajskd',
                  'B1':np.array(99)},
            'C1':{'D1':'ajskd',
                  'D2':np.array([99,99.9]),
                  'D3':np.array(['cc','aa'])}}
    tw.showSourceDict(inDict)

    w.show()
    sys.exit(app.exec_())
    
    
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
import pyqtgraph as pg
from obspy import UTCDateTime

# Custom axis labels for the archive widget
class TimeAxisItemArchive(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(TimeAxisItemArchive, self).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [UTCDateTime(value).strftime("%Y-%m-%d %H:%M:%S") for value in values]

# Widget for seeing what data times are available, and sub-selecting pick files
class ArchiveWidget(pg.PlotWidget):
    # Assign some signals when clicked
    addNewEventSignal = QtCore.pyqtSignal()  
    
    def __init__(self, parent=None, t1=0, t2=0):
        super(ArchiveWidget, self).__init__(parent,axisItems={'bottom': TimeAxisItemArchive(orientation='bottom')})
        self.pltItem=self.getPlotItem()
        self.pltItem.setMenuEnabled(enableMenu=False)
        # Only show the bottom axis
        self.pltItem.hideAxis('left')
        self.pltItem.hideButtons()
        # Set up the event view list boundary times
        self.t1=t1
        self.t2=t2
        self.line1=self.pltItem.addLine(x=t1,pen=(255,0,0))
        self.line2=self.pltItem.addLine(x=t2,pen=(255,0,0))
        self.boxes=[]
        # Give some x-limits (do not go prior to 1970)
        self.pltItem.setLimits(xMin=0)
        # No y-axis panning or zooming allowed
        self.pltItem.vb.setMouseEnabled(y=False)
        
    # Place a vertical lines when double clicked
    def mouseDoubleClickEvent(self, ev):
        super(ArchiveWidget, self).mouseDoubleClickEvent(ev)
        aPos=self.pltItem.vb.mapSceneToView(ev.pos())
        if ev.button()==1:
            self.t1=aPos.x()
        elif ev.button()==2:
            self.t2=aPos.x()
        else:
            return
        self.updateBoundaries()
        
    # Update the line positions
    def updateBoundaries(self):
        self.line1.setValue(self.t1)
        self.line2.setValue(self.t2)
        
    # Update the boxes representing the times
    def updateBoxes(self,ranges):
        # Remove the previous boxes
        for item in self.boxes:
            self.removeItem(item)
        self.boxes=[]
        # Add in the new boxes
        for r in ranges:
            rect=self.pltItem.plot(x=[r[0],r[1]],y=[0.5,0.5],pen=pg.mkPen(width=1.0,color='g'))
            self.addItem(rect)         
    
    # Add a new pick file with the center mouse button
    def mousePressEvent(self, ev):
        super(ArchiveWidget, self).mousePressEvent(ev)
        aPos=self.pltItem.vb.mapSceneToView(ev.pos())
        if ev.button()==4:
            self.makeEmptyPickFile(aPos.x())
    
    # Make an empty pick file at the specified time       
    def makeEmptyPickFile(self,time):
        self.newEveStr=UTCDateTime(time).strftime('%Y%m%d.%H%M%S.%f')
        self.addNewEventSignal.emit()
        
# Custom axis labels for the time widget        
class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(TimeAxisItem, self).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [UTCDateTime(value).strftime("%H:%M:%S.%f") for value in values]

# Widget to nicely show the time axis, which is in sync with the trace data
class TimeWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super(TimeWidget, self).__init__(parent,name='timeAxis',axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self.getPlotItem().getAxis('left').setWidth(70)
        self.getPlotItem().setMenuEnabled(enableMenu=False)
        self.getPlotItem().hideButtons()
   
# Widget which will hold the trace data, and respond to picking keybinds     
class TraceWidget(pg.PlotWidget):
    def __init__(self, parent=None,sta=None,delPickKey=Qt.Key_4):
        super(TraceWidget, self).__init__(parent)
        self.pltItem=self.getPlotItem()
        self.pltItem.setMenuEnabled(enableMenu=False)
        # Speed up the panning and zooming
        self.pltItem.setClipToView(True)
        self.pltItem.setDownsampling(True, True, 'peak')
        # Turn off the auto ranging
        self.pltItem.vb.disableAutoRange()
        # Only show the left axis
        self.pltItem.hideAxis('bottom')
        self.pltItem.hideButtons()
        self.pltItem.getAxis('left').setWidth(70)
        # Assign this widget a station
        self.sta=sta
        # Assign key to delete a pick off this widget
        self.delPickKey=delPickKey
        # Give this widget a set of vertical lines (represents a pick)
        self.vlines=[]
    
    # The built in buttons for each trace window
    def keyPressEvent(self, ev):
        super(TraceWidget, self).keyPressEvent(ev)
        # Remove all picks from the current axis
        if ev.key()==self.delPickKey:
            for aLine in self.vlines:
                self.pltItem.removeItem(aLine)
            self.vlines=[]
    
    # Place a vertical lines when double clicked
    def mouseDoubleClickEvent(self, ev):
        super(TraceWidget, self).mouseDoubleClickEvent(ev)
        aPos=self.pltItem.vb.mapSceneToView(ev.pos())
        self.vlines.append(self.pltItem.addLine(x=aPos.x(),pen=(255,0,0)))
    
    # Ensure that key presses are sent to the widget which the mouse is hovering over
    def enterEvent(self,ev):
        super(TraceWidget, self).enterEvent(ev)
        self.setFocus()
        
# Widget which return key presses, however double click replace backspace
class MixListWidget(QtGui.QListWidget):       
    # Return signal if key was pressed while in focus
    keyPressedSignal = QtCore.pyqtSignal()  
    
    def __init__(self, parent=None):
        super(MixListWidget, self).__init__(parent)
    
    # Load a list of strings to be added to gui list
    def loadList(self,strArr):
        self.addItems(strArr)
    
    # Update this widgets last pressed key, and return a signal
    def keyPressEvent(self, ev):
        self.key=ev.key()
        if self.key not in [Qt.Key_Insert,Qt.Key_Delete]:
            return
        self.keyPressedSignal.emit()
        
    # Swapping a double click with the backspace button...
    # ...wanted to transmit double click as a key
    def mouseDoubleClickEvent(self,ev):
        self.key=Qt.Key_Backspace
        self.keyPressedSignal.emit()
    
    # Ensure that key presses are sent to the widget which the mouse is hovering over
    def enterEvent(self,ev):
        super(MixListWidget, self).enterEvent(ev)
        self.setFocus()
        
# Generic widget for QListWidget with remove only keyPresses
class KeyListWidget(QtGui.QListWidget):       
    # Return signal if key was pressed while in focus
    keyPressedSignal = QtCore.pyqtSignal()  
    
    def __init__(self, parent=None):
        super(KeyListWidget, self).__init__(parent)
    
    # Update this widgets last pressed key, and return a signal
    def keyPressEvent(self, ev):
        self.key=ev.key()
        if self.key not in [Qt.Key_Delete]:
            return
        self.keyPressedSignal.emit()
    
    # Ensure that key presses are sent to the widget which the mouse is hovering over
    def enterEvent(self,ev):
        super(KeyListWidget, self).enterEvent(ev)
        self.setFocus()
    
def keyPressToString(ev):
    MOD_MASK = (Qt.CTRL | Qt.ALT | Qt.SHIFT | Qt.META)
    keyname = None
    key = ev.key()
    modifiers = int(ev.modifiers())
    if key in [Qt.Key_Shift,Qt.Key_Alt,Qt.Key_Control,Qt.Key_Meta]:
        pass
    elif (modifiers and modifiers & MOD_MASK==modifiers and key>0):
        keyname=QtGui.QKeySequence(modifiers+key).toString()
    else:
        keyname=QtGui.QKeySequence(key).toString()
    return keyname
    
# Line edit which returns key-bind strings
class KeyBindLineEdit(QtGui.QLineEdit):
    keyPressed=QtCore.pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(KeyBindLineEdit, self).__init__(parent)    
        self.MOD_MASK = (Qt.CTRL | Qt.ALT | Qt.SHIFT | Qt.META)
    
    # If any usual key bind was pressed, return the human recognizable string
    def keyPressEvent(self, ev):
        keyname = keyPressToString(ev)
        if keyname==None:
            return
        self.keyPressed.emit(keyname)

# Line edit which returns signal upon being double cliced     
class DblClickLineEdit(QtGui.QLineEdit):
    doubleClicked=QtCore.pyqtSignal()  
    
    def __init__(self, parent=None):
        super(DblClickLineEdit, self).__init__(parent)   
    
    def mouseDoubleClickEvent(self,ev):
        self.doubleClicked.emit()
        
# Line edit which returns a signal upon being hovered out of
class HoverLineEdit(QtGui.QLineEdit):
    hoverOut = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super(HoverLineEdit, self).__init__(parent)   
        self.changeState=False        
        self.textChanged.connect(self.updateChangeState)
        
    def leaveEvent(self, ev):
        # Only emit if the text was changed
        if self.changeState:
            self.hoverOut.emit()
            self.changeState=False
    
    def updateChangeState(self,ev):
        self.changeState=True
        
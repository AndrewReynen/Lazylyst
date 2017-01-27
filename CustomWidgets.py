from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
import pyqtgraph as pg
from obspy import UTCDateTime
import numpy as np
from decimal import Decimal

# Custom axis labels for the archive widget
class TimeAxisItemArchive(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(TimeAxisItemArchive, self).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [UTCDateTime(value).strftime("%Y-%m-%d %H:%M") for value in values]

# Widget for seeing what data times are available, and sub-selecting pick files
class ArchiveSpanWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super(ArchiveSpanWidget, self).__init__(parent,axisItems={'bottom': TimeAxisItemArchive(orientation='bottom')})
        self.pltItem=self.getPlotItem()
        self.pltItem.setMenuEnabled(enableMenu=False)
        # Turn off the auto ranging
        self.pltItem.vb.disableAutoRange()
        # Don't plot anything outside of the plot limits
        self.pltItem.setClipToView(True)
        # Only show the bottom axis
        self.pltItem.hideAxis('left')
        self.pltItem.hideButtons()
        # Give this widget a span select, for zooming
        self.span = pg.LinearRegionItem([500,1000])
        self.addItem(self.span)
        # Give a name to the data availability regions
        self.boxes=[]
        # Give some x-limits (do not go prior/after to 1970/2200)
        self.getPlotItem().setLimits(xMin=0,xMax=UTCDateTime('2200-01-01').timestamp)
        # No y-axis panning or zooming allowed
        self.pltItem.vb.setMouseEnabled(y=False)
        self.pltItem.setYRange(0,1)
    
    # Disable any scroll in/scroll out motions
    def wheelEvent(self,ev):
        return
        
    # Update the boxes representing the times
    def updateBoxes(self,ranges,pen):
        # Remove the previous boxes
        for item in self.boxes:
            self.removeItem(item)
        self.boxes=[]
        # Add in the new boxes
        for r in ranges:
            box=TraceCurve([r[0],r[1]],[0.5,0.5],'BOX',pen,-10)
            self.boxes.append(box)
            self.addItem(box)         
        
# Graphview widget which holds all current pick files
class ArchiveEventWidget(pg.PlotWidget):
    # Assign some signals when clicked
    addNewEventSignal = QtCore.pyqtSignal()  

    def __init__(self, parent=None):
        super(ArchiveEventWidget, self).__init__(parent)
        self.pltItem=self.getPlotItem()
        self.pltItem.setMenuEnabled(enableMenu=False)
        # Don't plot anything outside of the plot limits
        self.pltItem.setClipToView(True)
        # Do not show any axes
        self.pltItem.hideAxis('left')
        self.pltItem.hideAxis('bottom')
        self.pltItem.hideButtons()
        # Give some x-limits (do not go prior/after to 1970/2200)
        self.getPlotItem().setLimits(xMin=0,xMax=UTCDateTime('2200-01-01').timestamp)
        # Disable all panning and zooming
        self.pltItem.vb.setMouseEnabled(x=False,y=False)
        self.eveLines=[]
    
    # Scale to where ever the archiveSpan has selected
    def updateXRange(self,linkWidget):
        self.setXRange(*linkWidget.getRegion(), padding=0)
        
    # Disable any scroll in/scroll out motions
    def wheelEvent(self,ev):
        return
        
    # Add a new pick file with the center mouse button
    def mouseDoubleClickEvent(self, ev):
        super(ArchiveEventWidget, self).mouseDoubleClickEvent(ev)
        aPos=self.pltItem.vb.mapSceneToView(ev.pos())
        self.newEveStr=UTCDateTime(aPos.x()).strftime('%Y%m%d.%H%M%S.%f')
        self.addNewEventSignal.emit()
    
    # Reset the event lines, given a new set of event times
    def updateEveLines(self,fileTimes,pen,method):
        if method=='reset':
            self.eveLines=[]
            self.clear()
        for t in fileTimes:
            line=pg.InfiniteLine(pos=t,pen=pen)
            self.eveLines.append(line)
            self.addItem(line)
        
# List widget which holds all current pick files
class ArchiveListWidget(QtGui.QListWidget):       
    def __init__(self, parent=None):
        super(ArchiveListWidget, self).__init__(parent)
        
    # Return the list entries in the order which it appears
    def visualListOrder(self):
        aList=np.array([self.item(i).text() for i in range(self.count())])
        args=np.array([self.indexFromItem(self.item(i)).row() for i in range(self.count())])
        return [str(aFile) for aFile in aList[np.argsort(args)]]
        
# Custom axis labels for the time widget        
class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(TimeAxisItem, self).__init__(*args, **kwargs)
        # Some nice units with respect to time
        self.units=np.array([10**-6,10**-5,10**-4,10**-3,10**-2,10**-1,
                             1,2,5,10,30,60,
                             120,300,600,1800,3600,7200,
                             3600*6,3600*24,3600*48,3600*24*5,3600*24*31,3600*24*180],dtype=float)
        self.unitIdxs=np.arange(len(self.units))
        # What the above units should be displayed as
        self.unitStrs=['%S.%fs','%S.%fs','%S.%fs','%S.%fs','%S.%fs','%S.%fs',
                       '%S.%fs','%S.%fs','%Mm%Ss','%Mm%Ss','%Mm%Ss','%Mm%Ss',
                       '%Mm%Ss','%Hh%Mm','%Hh%Mm','%dd %Hh%Mm','%dd %Hh%Mm','%dd %Hh%Mm',
                       '%m-%d %Hh','%m-%d %Hh','%m-%d %Hh','%Y-%m-%d','%Y-%m-%d','%Y-%m-%d']
        # How many characters to trim off the end of the above string
        self.strTrim=[0,0,0,0,1,2,
                      3,3,0,0,0,0,
                      0,0,0,0,0,0,
                      0,0,0,0,0,0]
        self.unitIdx=0

    # Customize the locations of the ticks
    def tickValues(self, minVal, maxVal, size):
        # How many ticks are wanted on the page
        numTicks=float(max([int(size/160),2]))
        # Given how big the page is, see which units to apply
        diff=maxVal-minVal
        self.unitIdx=int(np.interp((diff)/numTicks,self.units,self.unitIdxs))
        unit=self.units[self.unitIdx]
        # In the case where zoomed in way to close
        if unit>diff:
            return [(0.5*diff,[minVal+0.20*diff,maxVal-0.20*diff])]
        # In the case where zoomed out very far
        if diff/(unit*numTicks)>2:
            unit*=int(diff/(unit*numTicks))
        # Start at the nearest whole unit
        val=minVal-minVal%unit+unit
        ticks=[]
        while val<maxVal:
            ticks.append(val)
            val+=unit
        return [(unit,ticks)]

    # Customize what string are being shown
    def tickStrings(self, values, scale, spacing):
        x=self.strTrim[self.unitIdx]
        if x==0:
            return [UTCDateTime(value).strftime(self.unitStrs[self.unitIdx]) for value in values]
        else:
            return [UTCDateTime(value).strftime(self.unitStrs[self.unitIdx])[:-(x+1)]+'s' for value in values]

# Widget to nicely show the time axis, which is in sync with the trace data
class TimeWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super(TimeWidget, self).__init__(parent,name='timeAxis',axisItems={'bottom': TimeAxisItem(orientation='bottom'),
                                                                           'left':pg.AxisItem(orientation='left',showValues=False)})
        self.getPlotItem().getAxis('left').setWidth(70)
        self.getPlotItem().setMenuEnabled(enableMenu=False)
        self.getPlotItem().hideButtons()
        # Give some x-limits (do not go prior/after to 1970/2200)
        self.getPlotItem().setLimits(xMin=0,xMax=UTCDateTime('2200-01-01').timestamp)
    
    # Return the xmin,xmax (times) of the plot
    def getTimeRange(self):
        return self.getPlotItem().vb.viewRange()[0]

# Infinite line, but now with reference to the pick type
class PickLine(pg.InfiniteLine):
    def __init__(self, aTime,aType,pen,parent=None):
        super(PickLine, self).__init__(parent)
        self.setZValue(10) # Allow picks to be over trace data
        self.pickType=aType
        self.setValue(aTime)
        self.setPen(pen)

# Plot curve item, but now with reference to the channel
class TraceCurve(pg.PlotCurveItem):
    def __init__(self,x,y,cha,pen,dep,parent=None):
        super(TraceCurve,self).__init__(parent)
        self.setData(x=x,y=y,pen=pen)
        self.cha=cha
        self.setZValue(dep)

# Widget which will hold the trace data, and respond to picking keybinds     
class TraceWidget(pg.PlotWidget):
    doubleClickSignal=QtCore.pyqtSignal()  
    
    def __init__(self, parent=None,sta='',clickPos=None):
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
        # Give some x-limits (do not go prior/after to 1970/2200)
        self.getPlotItem().setLimits(xMin=0,xMax=UTCDateTime('2200-01-01').timestamp)
        # Assign this widget a station
        self.sta=sta
        self.clickPos=clickPos
        # Allow the widget to hold memory of pick lines, and traces
        self.pickLines=[]
        self.traceCurves=[]
    
    # Add a trace to the widget
    def addTrace(self,x,y,cha,pen,dep):
        curve=TraceCurve(x,y,cha,pen,dep)
        self.addItem(curve)
        self.traceCurves.append(curve)
    
    # Add a single pick line to this station
    def addPick(self,aTime,aType,pen):
        aLine=PickLine(aTime,aType,pen)
        # Add the line to the plot, and its own pick lines
        self.pltItem.addItem(aLine)
        self.pickLines.append(aLine)
        
    # Remove a specific number of picks from the pick lines (with a given pick type)
    def removePicks(self,aType,num):
        # Count forwards to select picks for deletion
        delIdxs=[]
        for i,aLine in enumerate(self.pickLines):
            # Stop when enough picks have been marked
            if len(delIdxs)==num:
                break
            if aLine.pickType==aType:
                delIdxs.append(i)
        # Loop backwards and pop these picks off the widget
        for idx in delIdxs[::-1]:
            aLine=self.pickLines.pop(idx)
            self.pltItem.removeItem(aLine)
    
    # Emit signal for picking
    def mouseDoubleClickEvent(self, ev):
        super(TraceWidget, self).mouseDoubleClickEvent(ev)
        if self.sta==None:
            return
        # Figure out the position of the click, and update value
        self.clickPos=Decimal(self.pltItem.vb.mapSceneToView(ev.pos()).x())
        
        # Return signal
        self.doubleClickSignal.emit()
    
    # Ensure that key presses are sent to the widget which the mouse is hovering over
    def enterEvent(self,ev):
        super(TraceWidget, self).enterEvent(ev)
        self.setFocus()
        
    # Exit focus when the trace is left
    def leaveEvent(self,ev):
        super(TraceWidget, self).leaveEvent(ev)
        self.clearFocus()
    
# Widget which return key presses, however double click replace backspace
class MixListWidget(QtGui.QListWidget):       
    # Return signal if key was pressed while in focus
    keyPressedSignal=QtCore.pyqtSignal()  
    leaveSignal=QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super(MixListWidget, self).__init__(parent)
    
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

    # If ever the list if left by the mouse, emit (used to trigger ordering of passive functions)
    def leaveEvent(self,ev):
        self.leaveSignal.emit()
        
    # Return the lists entries in the order which it appears
    def visualListOrder(self):
        txt=np.array([self.item(i).text() for i in range(self.count())])
        args=np.array([self.indexFromItem(self.item(i)).row() for i in range(self.count())])
        return list(txt[np.argsort(args)])
        
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

    # Return a lists entries in the order which is appears
    def visualListOrder(self):
        txt=np.array([self.item(i).text() for i in range(self.count())])
        args=np.array([self.indexFromItem(self.item(i)).row() for i in range(self.count())])
        return list(txt[np.argsort(args)])

# Convert any key press signal to a human readable string (ignores modifiers like shift, ctrl)
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
        
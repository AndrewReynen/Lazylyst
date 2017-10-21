# Author: Andrew.M.G.Reynen
from __future__ import print_function, division
from decimal import Decimal

import numpy as np
from obspy import UTCDateTime
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
import pyqtgraph as pg

from CustomFunctions import getTimeFromFileName

# Custom axis labels for the archive widget
class TimeAxisItemArchive(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(TimeAxisItemArchive, self).__init__(*args, **kwargs)
        # Some nice units with respect to time
        self.units=np.array([60,
                             120,300,600,1800,3600,7200,
                             3600*6,3600*24,3600*48,3600*24*5,3600*24*31,3600*24*180],dtype=float)
        self.unitIdxs=np.arange(len(self.units))
        # What the above units should be displayed as
        self.unitStrs=['%Hh%Mm',
                       '%Hh%Mm','%Hh%Mm','%Hh%Mm','%Hh%Mm','%Y-%m-%d %Hh','%Y-%m-%d %Hh',
                       '%Y-%m-%d %Hh','%Y-%m-%d','%Y-%m-%d','%Y-%m-%d','%Y-%m-%d','%Y-%m-%d']
        self.unitIdx=0

    # Customize the locations of the ticks
    def tickValues(self, minVal, maxVal, size):
        # How many ticks are wanted on the page
        numTicks=float(max([int(size/225),2]))
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
        return [UTCDateTime(value).strftime(self.unitStrs[self.unitIdx]) for value in values]

# Function called to display date time text on widget
def showHoverText(self,pixPoint):
    mousePoint=self.pltItem.vb.mapSceneToView(pixPoint)
    if np.isnan(mousePoint.x()):
        return
    self.hoverTimeItem.setText(str(UTCDateTime(Decimal(mousePoint.x()))))
    t1,t2=self.getPlotItem().vb.viewRange()[0]
    if t2<=1:
        return
    self.hoverTimeItem.setPos(t1+(t2-t1)*0.5,0)
    self.hoverTimeItem.show() 
    
# Hide the date time text when not hovering over widget
def hideHoverText(self,ev):
    super(pg.PlotWidget, self).leaveEvent(ev)
    self.hoverTimeItem.hide()
    
# Add a new pick file with the center mouse button
def addNewPickFile(self, ev):
    super(pg.PlotWidget, self).mouseDoubleClickEvent(ev)
    self.newEveTime=self.pltItem.vb.mapSceneToView(ev.pos()).x()
    self.addNewEventSignal.emit()
    
# Initiate common functions between the archiveEvent and archiveSpan widgets
def addArchiveWidgetElements(self):
    # Create text item
    self.hoverTimeItem=pg.TextItem(text='',anchor=(0.5,1))
    self.hoverTimeItem.setZValue(5)
    self.hoverTimeItem.hide()
    self.addItem(self.hoverTimeItem)
    # Add the show text function
    self.scene().sigMouseMoved.connect(lambda pixPoint:showHoverText(self,pixPoint))
    # Add the hide text function
    self.leaveEvent=lambda ev:hideHoverText(self,ev)
    
    # Add ability to add empty pick files if double clicked
    self.mouseDoubleClickEvent=lambda ev:addNewPickFile(self,ev)
    
# Widget for seeing what data times are available, and sub-selecting pick files
class ArchiveSpanWidget(pg.PlotWidget):
    addNewEventSignal=QtCore.pyqtSignal()
    
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
        # Give some text upon hovering, and allow events to be added on double clicking
        addArchiveWidgetElements(self)
        
    # Return the span bounds
    def getSpanBounds(self):
        t1,t2=self.span.getRegion()
        return UTCDateTime(t1),UTCDateTime(t2)
    
    # Disable any scroll in/scroll out motions
    def wheelEvent(self,ev):
        return
        
    # Update the boxes representing the times
    def updateBoxes(self,ranges,penInt):
        # Remove the previous boxes
        for item in self.boxes:
            self.removeItem(item)
        self.boxes=[]
        # Skip, if no ranges to add
        if len(ranges)==0:
            return
        # Try to merge these ranges (less lines)...
        # ...sort first by range start values
        ranges=np.array(ranges)
        ranges=ranges[np.argsort(ranges[:,0])]
        merge=[ranges[0]]
        for rng in ranges:
            # In the case they do not overlap
            if rng[0]>merge[-1][1]:
                merge.append(rng)
            # If overlaping, and the new range extends further, push it
            elif rng[1]>merge[-1][1]:
                merge[-1][1]=rng[1]
        merge=np.array(merge)
        # Plot these efficiently (one disconnected line, rather than many lines)
        connect = np.ones((len(merge), 2), dtype=np.ubyte)
        connect[:,-1] = 0  #  disconnect segment between lines
        path = pg.arrayToQPath(merge.reshape(len(merge)*2), np.ones((len(merge)*2))*0.5, connect.reshape(len(merge)*2))
        item = pg.QtGui.QGraphicsPathItem(path)
        item.setPen(pg.mkPen(QtGui.QColor(penInt)))
        # Add in the new box
        self.boxes.append(item)
        self.addItem(item)      
        
# Graphview widget which holds all current pick files
class ArchiveEventWidget(pg.PlotWidget): 
    addNewEventSignal=QtCore.pyqtSignal()
    
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
        self.getPlotItem().setLimits(xMin=0,xMax=UTCDateTime('2200-01-01').timestamp,yMin=-0.3,yMax=1.3)
        # Disable all panning and zooming
        self.pltItem.vb.setMouseEnabled(x=False,y=False)
        self.curEveLine=None # For the highlighted event
        self.otherEveLine=None # For all other events
        # Give some text upon hovering, and allow events to be added on double clicking
        addArchiveWidgetElements(self)
    
    # Scale to where ever the archiveSpan has selected
    def updateXRange(self,linkWidget):
        self.setXRange(*linkWidget.getRegion(), padding=0)
        
    # Disable any scroll in/scroll out motions
    def wheelEvent(self,ev):
        return
    
    # Reset the event lines, given a new set of event times
    def updateEveLines(self,fileTimes,curFile):
        # Remove the not-current event lines
        if self.otherEveLine!=None:
            self.removeItem(self.otherEveLine)
            self.otherEveLine=None
        # Generate the many pick lines as one disconnected line
        if len(fileTimes)!=0:
            fileTimes=np.reshape(fileTimes,(len(fileTimes),1))
            times=np.hstack((fileTimes,fileTimes))
            connect = np.ones((len(times), 2), dtype=np.ubyte)
            connect[:,-1] = 0  #  disconnect segment between lines
            connect=connect.reshape(len(times)*2)
            path = pg.arrayToQPath(times.reshape(len(times)*2),connect,connect)
            item = pg.QtGui.QGraphicsPathItem(path)
            # Reference and plot the line
            self.otherEveLine=item
            self.addItem(item)
        # Generate and plot the current pick file (if present)
        self.updateEveLineSelect(curFile)
    
    # Update the current event line to proper position, and appropriate color
    def updateEveLineSelect(self,curFile):
        # Remove this line if no current file
        if self.curEveLine!=None:
            self.removeItem(self.curEveLine)
            self.curEveLine=None
        # Add the line if a pick file is selected
        if curFile!='':
            t=getTimeFromFileName(curFile)
            line=pg.InfiniteLine(pos=t,pen=pg.mkPen(QtGui.QColor(0)))
            # Reference and plot the line
            self.curEveLine=line
            self.addItem(line)
            
    # Update the color, width and depth of an event line
    def updateEvePens(self,evePen,eveType):
        col,width,dep=evePen
        col=QtGui.QColor(QtGui.QColor(col))
        if eveType=='cur':
            item=self.curEveLine
        else:
            item=self.otherEveLine
        if item!=None:
            item.setPen(pg.mkPen(col,width=width))
            item.setZValue(dep)

# List widget which holds all current pick files
class ArchiveListWidget(QtWidgets.QListWidget):       
    def __init__(self, parent=None):
        super(ArchiveListWidget, self).__init__(parent)
        
    # Return the list entries in the order which it appears
    def visualListOrder(self):
        aList=np.array([self.item(i).text() for i in range(self.count())])
        args=np.array([self.indexFromItem(self.item(i)).row() for i in range(self.count())])
        return [str(aFile) for aFile in aList[np.argsort(args)]]
        
    # Ensure that key presses are sent to the widget which the mouse is hovering over
    def enterEvent(self,ev):
        super(ArchiveListWidget, self).enterEvent(ev)
        self.setFocus()
        
    # Exit focus when the list widget is left
    def leaveEvent(self,ev):
        super(ArchiveListWidget, self).leaveEvent(ev)
        self.clearFocus()
        
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
        self.getPlotItem().vb.setMouseEnabled(y=False,x=False)
        # Turn off all interaction
        self.setEnabled(False)
        # Give a blank title (gets rid of the y-axis)
        self.getPlotItem().setLabels(title='')
    
    # Null any built in hover actions
    def enterEvent(self,event):
        return
        
    def leaveEvent(self,event):
        return
    
    # Return the xmin,xmax (times) of the plot
    def getTimeRange(self):
        return self.getPlotItem().vb.viewRange()[0]

# Infinite line, but now with reference to the pick type
class PickLine(pg.InfiniteLine):
    def __init__(self, aTime,aType,pen,parent=None):
        super(PickLine, self).__init__(parent)
        col,width,depth=pen
        self.pickType=aType
        self.setValue(aTime)
        self.setZValue(depth)
        self.setPen(col,width=width)

# Plot curve item, but now with reference to the channel
class TraceCurve(pg.PlotCurveItem):
    def __init__(self,x,y,cha,pen,dep,parent=None):
        super(TraceCurve,self).__init__(parent)
        self.setData(x=x,y=y,pen=pen)
        self.cha=cha
        self.setZValue(dep)
        # If width of zero, do not show the curve
        if pen.widthF()==0:
            self.setVisible(False)

# Widget which will hold the trace data, and respond to picking keybinds     
class TraceWidget(pg.PlotWidget):
    doubleClickSignal=QtCore.pyqtSignal()  
    
    def __init__(self, parent=None,sta='',hoverPos=None):
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
        # Allow the widget to hold memory of pick lines, and traces
        self.pickLines=[]
        self.traceCurves=[]
        # Set the hover position, upon hovering
        self.scene().sigMouseMoved.connect(self.onHover)
        self.hoverPos=hoverPos
        # Allow this widget to be fairly small
        sizePolicy = QtGui.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(0, 15))
        
    # Update the mouse position
    def onHover(self,pixPoint):
        mousePoint=self.pltItem.vb.mapSceneToView(pixPoint)
        self.hoverPos=Decimal(mousePoint.x()),Decimal(mousePoint.y())
    
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
    def removePicks(self,aType,delTimes):
        # Count forwards to select picks for deletion
        delIdxs=[]
        for i,aLine in enumerate(self.pickLines):
            # If picks overlap, do not delete more than necessary
            if len(delIdxs)==len(delTimes):
                break
            if aLine.pickType==aType and aLine.value() in delTimes:
                delIdxs.append(i)
        # Check to make sure all were deleted
        if len(delIdxs)!=len(delTimes):
            print('Missed deleting some plotted pick lines')
        # Loop backwards and pop these picks off the widget
        for idx in delIdxs[::-1]:
            aLine=self.pickLines.pop(idx)
            self.pltItem.removeItem(aLine)
    
    # Emit signal for picking
    def mouseDoubleClickEvent(self, ev):
        super(TraceWidget, self).mouseDoubleClickEvent(ev)
        # If this widget is assigned a station, return signal
        if self.sta!=None:
            self.doubleClickSignal.emit()
    
    # Ensure that key presses are sent to the widget which the mouse is hovering over
    def enterEvent(self,ev):
        super(TraceWidget, self).enterEvent(ev)
        self.setFocus()
        
    # Exit focus when the trace is left
    def leaveEvent(self,ev):
        super(TraceWidget, self).leaveEvent(ev)
        self.clearFocus()
        self.hoverPos=None
        
    # Return the ymin,ymax of the plot
    def getRangeY(self):
        return self.getPlotItem().vb.viewRange()[1]
    
# Widget which return key presses, however double click replaces backspace
class MixListWidget(QtWidgets.QListWidget):       
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
        
    # Deselect all items if in a blank space
    def mousePressEvent(self, ev):
        if self.itemAt(ev.pos()) is None:
            self.clearSelection()
        QtWidgets.QListWidget.mousePressEvent(self, ev)
        
    # Swapping a double click with the backspace button...
    # ...wanted to transmit double click as a key
    def mouseDoubleClickEvent(self,ev):
        # Only allow left-double clicks
        if ev.button()!=1:
            return
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
        
# Generic widget for QListWidget with remove only keyPresses...
# ...currently only used for key bind of delete (if want more keys, must check appropriate lists)
class KeyListWidget(QtWidgets.QListWidget):       
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
        
    # Deselect all items if in a blank space
    def mousePressEvent(self, ev):
        if self.itemAt(ev.pos()) is None:
            self.clearSelection()
        QtWidgets.QListWidget.mousePressEvent(self, ev)
    
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
class KeyBindLineEdit(QtWidgets.QLineEdit):
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
class DblClickLineEdit(QtWidgets.QLineEdit):
    doubleClicked=QtCore.pyqtSignal()  
    
    def __init__(self, parent=None):
        super(DblClickLineEdit, self).__init__(parent)   
    
    def mouseDoubleClickEvent(self,ev):
        self.doubleClicked.emit()
        
# Line edit which returns a signal upon being hovered out of
class HoverLineEdit(QtWidgets.QLineEdit):
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
        
# Generic widget for QListWidget with remove only keyPresses
class DblClickLabelWidget(QtWidgets.QLabel):       
    # Return signal if label was double clicked
    doubleClicked=QtCore.pyqtSignal()  
    
    def __init__(self, parent=None):
        super(DblClickLabelWidget, self).__init__(parent)
        
    def mouseDoubleClickEvent(self,ev):
        self.doubleClicked.emit()

# Scatter Item class, but allow double click signal
class CustScatter(pg.ScatterPlotItem):
    doubleClicked=QtCore.Signal(object)
    
    def __init__(self, *args, **kwargs):
        super(CustScatter, self).__init__(*args, **kwargs)
    
    # Set the clicked points upon double clicking
    def mouseDoubleClickEvent(self,ev):
        if ev.button() == QtCore.Qt.LeftButton:
            # Set the clicked position
            self.clickPos=np.array([ev.pos().x(),ev.pos().y()])
            # See which points were near the click position
            self.ptsClicked=self.pointsAt(ev.pos())
            # Emit the scatter plot
            self.doubleClicked.emit(self)
            ev.accept()

# Widget for seeing what data times are available, and sub-selecting pick files
class MapWidget(pg.GraphicsLayoutWidget):
    doubleClicked=QtCore.Signal()
    
    def __init__(self, parent=None):
        super(MapWidget, self).__init__(parent)
        # Add the map to the view, and turn off some of the automatic interactive properties
        self.map=self.addPlot()
        self.map.setMenuEnabled(enableMenu=False)
        self.map.hideButtons()
        self.stas=[] # The station names for the station spot items
        self.staItem=None # The station scatter item
        self.selectSta=None # Which station is currently selected
        self.curEveItem=None # The current event scatter item
        self.prevEveItem=None # The previous event scatter item 
        self.clickPos=[0,0] # Last double clicked position
        # Add in the hovered over station label
        self.hoverStaItem=pg.TextItem(text='',anchor=(0.5,1))
        self.hoverStaItem.hide()
        self.map.addItem(self.hoverStaItem)
        # Show station text when hovering over the station symbol
        self.scene().sigMouseMoved.connect(self.onHover)
        
    # Handle double click events to the station scatter item
    def dblClicked(self,staScat):
        self.clickPos=list(staScat.clickPos)
        # Update the nearby station which was clicked
        self.selectSta=self.getSelectSta(staScat.clickPos,staScat.ptsClicked)
        # Forward the double clicked signal to main window
        self.doubleClicked.emit()
        
    # Function to return the nearest station to the current moused point
    def getSelectSta(self,mousePos,nearPoints):
        if len(nearPoints)>0:
            selPos=np.array([[point.pos().x(),point.pos().y()] for point in nearPoints])
            selPoint=nearPoints[np.argmin(np.sum((selPos-mousePos)**2))]
            return str(self.stas[np.where(self.staItem.points()==selPoint)[0][0]])
        else:
            return None
        
    # Load the new station meta data
    def loadStaLoc(self,staLoc,colorAssign,
                   staSize,staDep,init):
        # Enable the autoscaling temporarily
        self.map.vb.enableAutoRange(enable=True)
        # Hide the hovered station label
        self.hoverStaItem.hide()
        # Clear away the old station spots
        if self.staItem!=None:
            self.map.removeItem(self.staItem)
        # Reset the double clicked station, if reloading the station file entirely
        if init:
            self.selectSta=None
        # Generate the station items
        if len(staLoc)==0:
            self.stas=[]
        else:
            self.stas=staLoc[:,0]
        # Get the brush values to be assigned
        brushArr=[]
        for sta in self.stas:
            color=colorAssign[sta]
            brushArr.append(pg.mkBrush(color.red(),color.green(),color.blue(),200))
        staScatter=CustScatter(size=staSize*2,symbol='t1',pen=pg.mkPen(None))
        staScatter.setZValue(staDep)
        # Add in the points
        if len(staLoc)!=0:
            staScatter.addPoints(x=staLoc[:,1], y=staLoc[:,2], brush=brushArr)
        # Give some clicking ability to the stations
        staScatter.doubleClicked.connect(self.dblClicked) # For any point being clicked
        # Add the station scatter items
        self.map.addItem(staScatter)
        self.staItem=staScatter
        # Disable autoscaling the for map items
        self.map.vb.enableAutoRange(enable=False)
    
    # See which station is being hovered over
    def onHover(self,pixPoint):
        if len(self.stas)==0:
            return
        # Get the nearby points
        mousePoint=self.staItem.mapFromScene(pixPoint)
        nearPoints = self.staItem.pointsAt(mousePoint)
        # Grab the nearest ones station code and update the 
        if len(nearPoints)==0:
            self.hoverStaItem.hide()
        else:
            mousePos=np.array([mousePoint.x(),mousePoint.y()])
            sta=self.getSelectSta(mousePos,nearPoints)
            self.hoverStaItem.setText(sta)
            self.hoverStaItem.setPos(mousePoint)
            self.hoverStaItem.show()
        
    # Load a set of event points
    def loadEvePoints(self,eveMeta,eveType):
        if eveType=='cur':
            item,alpha=self.curEveItem,200
        else:
            item,alpha=self.prevEveItem,160
        # Remove the previous item
        if item is not None:
            self.map.removeItem(item)
        # Add in all of the new points, size & color set in different function
        scatter=pg.ScatterPlotItem(size=1,symbol='o',pen=pg.mkPen(None),brush=pg.mkBrush(0,0,0,alpha))
        scatter.addPoints(x=eveMeta[:,1],y=eveMeta[:,2])
        ## Why does this update if autoRange already off?? ##
        # print(self.map.vb.state['autoRange'])
        self.map.addItem(scatter)
        # Update the scatter item reference
        if eveType=='cur':
            self.curEveItem=scatter
        else:
            self.prevEveItem=scatter
        
    # Update the event pen values
    def updateEvePen(self,evePen,eveType):
        col,size,dep=evePen
        col=QtGui.QColor(QtGui.QColor(col))
        if eveType=='cur':
            item=self.curEveItem
        else:
            item=self.prevEveItem
        if item!=None:
            item.setBrush(pg.mkBrush(col.red(),col.green(),col.blue(),200))
            item.setSize(size*2)
            item.setZValue(dep)
    
    # Change the pen of the axis and axis labels
    def setPen(self,pen):
        for item in self.items():
            if type(item)==pg.graphicsItems.AxisItem.AxisItem:
                item.setPen(pen)
                
# Widget to hold raster information for plotting
class ImageWidget(pg.PlotWidget): 
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)        
        self.pltItem=self.getPlotItem()
        self.pltItem.setMenuEnabled(enableMenu=False)
        # Speed up the panning and zooming
        self.pltItem.setClipToView(True)
        # Turn off the auto ranging
        self.pltItem.vb.disableAutoRange()
        # Only show the left axis
        self.pltItem.hideAxis('bottom')
        self.pltItem.hideButtons()
        self.pltItem.getAxis('left').setWidth(70)
        self.pltItem.getAxis('left').setZValue(1)
        # Give some x-limits (do not go prior/after to 1970/2200)
        self.getPlotItem().setLimits(xMin=0,xMax=UTCDateTime('2200-01-01').timestamp)
        # Create a blank image item
        self.imageItem=pg.ImageItem()
        self.addItem(self.imageItem)
        self.prevPosX,self.prevScaleX=0,1
        self.prevPosY,self.prevScaleY=0,1
        # Give the image a border
        self.imageBorder=pg.QtGui.QGraphicsRectItem(-1,-1,0.1,0.1)
        self.addItem(self.imageBorder)
        
    # Update the image on this widget
    def loadImage(self,imgDict):
        # Load in the defaults if some optional keys are not present
        imgDict=self.loadDefaultKeys(imgDict)
        # Set the image data
        self.imageItem.setImage(imgDict['data'].T)
        # Set position and scale of image...
        diffX=imgDict['t0']-self.prevPosX
        diffY=imgDict['y0']-self.prevPosY
        self.imageItem.scale(imgDict['tDelta']/self.prevScaleX,imgDict['yDelta']/self.prevScaleY)
        self.imageItem.translate(diffX/imgDict['tDelta'], diffY/imgDict['yDelta'])
        self.prevPosX+=diffX
        self.prevPosY+=diffY
        self.prevScaleX,self.prevScaleY=imgDict['tDelta'],imgDict['yDelta']
        # Set the coloring
        lut=self.getLUT(imgDict['data'],imgDict['cmapPos'],imgDict['cmapRGBA']) 
        self.imageItem.setLookupTable(lut)
        # Update image boundary
        xSize,ySize=np.array([imgDict['tDelta'],imgDict['yDelta']])*imgDict['data'].T.shape
        self.imageBorder.setRect(imgDict['t0'],imgDict['y0'],xSize,ySize)
        # Set default Y-limit to zoom to the image
        self.setYRange(imgDict['y0'],ySize,padding=0.0)
        # Apply the label
        self.pltItem.setLabel(axis='left',text=imgDict['label'])
    
    # Give default values to keys which are not present in the image dictionary
    def loadDefaultKeys(self,imgDict):
        for key,val in [['y0',0],['yDelta',1],['label',''],
                        ['cmapPos',np.array([np.min(imgDict['data']),np.max(imgDict['data'])])],
                        ['cmapRGBA',np.array([[0,0,0,255],[255,255,255,255]])]
                        ]:
            if key not in imgDict.keys():
                # In the case where the colors are given, but the positions are not, give evenly spaced positions
                if key=='cmapPos' and 'cmapRGBA' in imgDict.keys():
                    imgDict[key]=np.linspace(np.min(imgDict['data']),np.max(imgDict['data']),len(imgDict['cmapRGBA']))
                else:
                    imgDict[key]=val
        # In the case where the positions are given, but not the colors - just use first and last position
        if len(imgDict['cmapPos'])!=len(imgDict['cmapRGBA']):
            imgDict['cmapPos']=np.array([imgDict['cmapPos'][0],imgDict['cmapPos'][-1]])
        return imgDict
    
    # Get the look-up-table (color map) 
    def getLUT(self,data,pos,col):
        aMap = pg.ColorMap(np.array(pos), np.array(col,dtype=np.ubyte))
        lut = aMap.getLookupTable(np.min(data),np.max(data),256)
        return lut

# Copyright Andrew.M.G.Reynen
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
import pyqtgraph as pg
import numpy as np
#from pyqtgraph.dockarea import DockArea, Dock
from CustomFunctions import getTimeFromFileName
from obspy import UTCDateTime
from decimal import Decimal

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
        self.getPlotItem().setLimits(xMin=0,xMax=UTCDateTime('2200-01-01').timestamp,yMin=-0.3,yMax=1.3)
        # Disable all panning and zooming
        self.pltItem.vb.setMouseEnabled(x=False,y=False)
        self.curEveLine=None # For the highlighted event
        self.otherEveLine=None # For all other events
        # Give some text upon hovering
        self.scene().sigMouseMoved.connect(self.onHover)
        self.hoverTimeItem=pg.TextItem(text='',anchor=(0.5,1))
        self.hoverTimeItem.setZValue(5)
        self.hoverTimeItem.hide()
        self.addItem(self.hoverTimeItem)
        
    # Update the mouse position text
    def onHover(self,pixPoint):
        mousePoint=self.pltItem.vb.mapSceneToView(pixPoint)
        self.hoverTimeItem.setText(str(UTCDateTime(Decimal(mousePoint.x()))))
        t1,t2=self.getPlotItem().vb.viewRange()[0]
        if t2<=1:
            return
        self.hoverTimeItem.setPos(t1+(t2-t1)*0.5,0)
        self.hoverTimeItem.show()
        
    # Turn off the time when not hovering
    def leaveEvent(self,ev):
        super(ArchiveEventWidget, self).leaveEvent(ev)
        self.hoverTimeItem.hide()
    
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
    def updateEveLines(self,fileTimes,curFile,penInt,penIntSelect):
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
            item.setPen(pg.mkPen(QtGui.QColor(penInt)))
            item.setZValue(0)
            # Reference and plot the line
            self.otherEveLine=item
            self.addItem(item)
        # Generate and plot the current pick file (if present)
        self.updateEveLineSelect(curFile,penIntSelect)
    
    # Update the current event line to proper position, and appropriate color
    def updateEveLineSelect(self,curFile,penIntSelect):
        # Remove this line if no current file
        if self.curEveLine!=None:
            self.removeItem(self.curEveLine)
            self.curEveLine=None
        # Add the line if a pick file is selected
        if curFile!='':
            t=getTimeFromFileName(curFile)
            line=pg.InfiniteLine(pos=t,pen=pg.mkPen(QtGui.QColor(penIntSelect)))
            line.setZValue(10)
            # Reference and plot the line
            self.curEveLine=line
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
        
    # Ensure that key presses are sent to the widget which the mouse is hovering over
    def enterEvent(self,ev):
        super(ArchiveListWidget, self).enterEvent(ev)
        self.setFocus()
        
    # Exit focus when the list widget is left
    def leaveEvent(self,ev):
        super(ArchiveListWidget, self).leaveEvent(ev)
        self.clearFocus()
        
#    # Allow the enter key to do the same as double clicking
#    def keyPressEvent(self,ev):
#        print ev.key()
        
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
    
    def __init__(self, parent=None,sta='',clickPos=None,hoverPos=None):
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
        # Set the hover position, upon hovering
        self.scene().sigMouseMoved.connect(self.onHover)
        self.hoverPos=hoverPos
        
    # Update the mouse position
    def onHover(self,pixPoint):
        mousePoint=self.pltItem.vb.mapSceneToView(pixPoint)
        self.hoverPos=Decimal(mousePoint.x())
    
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
        self.hoverPos=None
        
    # Return the ymin,ymax of the plot
    def getRangeY(self):
        return self.getPlotItem().vb.viewRange()[1]
    
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
        
# Generic widget for QListWidget with remove only keyPresses
class DblClickLabelWidget(QtGui.QLabel):       
    # Return signal if label was double clicked
    doubleClicked=QtCore.pyqtSignal()  
    
    def __init__(self, parent=None):
        super(DblClickLabelWidget, self).__init__(parent)
        
    def mouseDoubleClickEvent(self,ev):
        self.doubleClicked.emit()

# Scatter Item class, but allow double click signal
class CustScatter(pg.ScatterPlotItem):
    dblClicked=QtCore.Signal(object)
    
    def __init__(self, *args, **kwargs):
        super(CustScatter, self).__init__(*args, **kwargs)
    
    # Return the clicked points upon double clicking
    def mouseDoubleClickEvent(self,ev):
        if ev.button() == QtCore.Qt.LeftButton:
            pts = self.pointsAt(ev.pos())
            if len(pts) > 0:
                self.clickPos=np.array([ev.pos().x(),ev.pos().y()])
                self.ptsClicked = pts
                self.dblClicked.emit(self)
                ev.accept()
            else:
                ev.ignore()
        else:
            ev.ignore()

# Widget for seeing what data times are available, and sub-selecting pick files
class MapWidget(pg.GraphicsLayoutWidget):
    staDblClicked=QtCore.Signal()
    
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
        # Add in the hovered over station label
        self.hoverStaItem=pg.TextItem(text='',anchor=(0.5,1))
        self.hoverStaItem.hide()
        self.map.addItem(self.hoverStaItem)
        
    # Get the station which was closest to the double click event, and set the selected station
    def staClicked(self,staScat):
        cPos=staScat.clickPos
        self.selectSta=self.getSelectSta(cPos,staScat.ptsClicked)
        self.staDblClicked.emit()
        
    # Function to return the nearest station to the current moused point
    def getSelectSta(self,mousePos,nearPoints):
        selPos=np.array([[point.pos().x(),point.pos().y()] for point in nearPoints])
        selPoint=nearPoints[np.argmin(np.sum((selPos-mousePos)**2))]
        return str(self.stas[np.where(self.staItem.points()==selPoint)[0][0]])
        
    # Load the new station meta data
    def loadStaMeta(self,staMeta,colorAssign,init):
        # Enable the autoscaling temporarily
        self.map.vb.enableAutoRange()
        # Hide the hovered station label
        self.hoverStaItem.hide()
        # Clear away the old station spots
        if self.staItem!=None:
            self.map.removeItem(self.staItem)
        # Reset the double clicked station, if reloading the station file entirely
        if init:
            self.selectSta=None
        # Generate the station items
        if len(staMeta)==0:
            self.stas=[]
        else:
            self.stas=staMeta[:,0]
        # Get the brush values to be assigned
        brushArr=[]
        for sta in self.stas:
            color=colorAssign[sta]
            brushArr.append(pg.mkBrush(color.red(),color.green(),color.blue(),200))
        staScatter = CustScatter(size=8,symbol='t1',pen=pg.mkPen(None))
        # Add in the points
        if len(staMeta)!=0:
            staScatter.addPoints(x=staMeta[:,1], y=staMeta[:,2], brush=brushArr)
        # Give some clicking ability to the stations
        staScatter.dblClicked.connect(self.staClicked)
        self.scene().sigMouseMoved.connect(self.onHover)
        # Add the station scatter items
        self.map.addItem(staScatter)
        self.staItem=staScatter
        # Disable autoscaling the for map items
        self.map.vb.disableAutoRange() 
    
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
    def loadEvePoints(self,eveMeta,eveType,QCol):
        if eveType=='cur':
            item,size,alpha=self.curEveItem,6,200
        else:
            item,size,alpha=self.prevEveItem,3,160
        # Remove the previous item
        if item!=None:
            self.map.removeItem(item)
        # Add in all of the new points
        scatter=pg.ScatterPlotItem(size=size,symbol='o',pen=pg.mkPen(None),
                                   brush=pg.mkBrush(QCol.red(),QCol.green(),QCol.blue(),alpha))
        scatter.addPoints(x=eveMeta[:,1],y=eveMeta[:,2])
        self.map.addItem(scatter)
        # Update the scatter item reference
        if eveType=='cur':
            scatter.setZValue(3.0)
            self.curEveItem=scatter
        else:
            scatter.setZValue(-1.0)
            self.prevEveItem=scatter
    
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
        # No y-axis panning or zooming allowed
        self.pltItem.vb.setMouseEnabled(y=False)
        # Create a blank image item
        self.imageItem=pg.ImageItem()
        self.addItem(self.imageItem)
        self.prevPosX,self.prevScaleX=0,1
        self.prevPosY,self.prevScaleY=0,1
        
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
        # Set Y-limit to bound the image
        self.setYRange(imgDict['y0'],imgDict['data'].shape[0]*imgDict['yDelta'],padding=0.0)
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
        

## For when a QWidget can be promoted to a DockArea/Dock in qtDesigner ##
## Testing the dock area class
#class CustDockArea(DockArea):
#    def __init__(self, parent=None):
#        super(CustDockArea, self).__init__(parent) 
#
## Testing the dock class      
#class CustDock(Dock):
#    def __init__(self, parent=None):
#        super(CustDock, self).__init__(parent)
        

        

        

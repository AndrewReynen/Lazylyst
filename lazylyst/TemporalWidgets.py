# Author: Andrew.M.G.Reynen
from __future__ import print_function, division
from decimal import Decimal

import numpy as np
from obspy import UTCDateTime
from PyQt5 import QtWidgets, QtGui, QtCore
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
        self.setVisible(width!=0)

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
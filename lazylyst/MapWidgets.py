# Author: Andrew.M.G.Reynen
from __future__ import print_function, division
import time

import numpy as np
from PyQt5 import QtGui,QtCore,QtWidgets
import pyqtgraph as pg

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
            
# Verticies on the polygon
class RoiHandle(pg.graphicsItems.ROI.Handle):
    handleMenuSignal=QtCore.Signal(float)
    def __init__(self, *args, **kwargs):
        super(RoiHandle, self).__init__(*args, **kwargs)

    def mouseClickEvent(self, ev):
        # Right-click cancels drag
        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            self.isMoving = False  # Prevent any further motion
            self.movePoint(self.startPos, finish=True)
            ev.accept()
        elif int(ev.button() & self.acceptedMouseButtons()) > 0:
            ev.accept()
            if ev.button() == QtCore.Qt.RightButton and self.deletable:
                self.raiseContextMenu(ev)
            self.sigClicked.emit(self, ev)
        else:
            ev.ignore()        
    
    # Make some edits to default pg Handle
    def raiseContextMenu(self, ev):
        menu = self.scene().addParentContextMenus(self, self.getMenu(), ev)
        # Remove the unwanted actions
        for action in menu.actions():
            if str(action.text())!='Remove handle':
                menu.removeAction(action)
        # Make sure it is still ok to remove this handle
        removeAllowed = all([r.checkRemoveHandle(self) for r in self.rois])
        self.removeAction.setEnabled(removeAllowed)
        pos = ev.screenPos()
        # Note when the menu was added
        self.handleMenuSignal.emit(time.time())
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))  

# Editable polygon
class RoiPolyLine(pg.PolyLineROI):
    handleMenuSignal=QtCore.Signal(float)
    def __init__(self, *args, **kwargs):
        super(RoiPolyLine, self).__init__(*args, **kwargs)
    
    # Make use of the edited pg Handle "RoiHandle"  
    def addHandle(self, info, index=None):
        # If a Handle was not supplied, create it now
        if 'item' not in info or info['item'] is None:
            h = RoiHandle(self.handleSize, typ=info['type'], pen=self.handlePen, parent=self)
            h.setPos(info['pos'] * self.state['size'])
            info['item'] = h
        else:
            h = info['item']
            if info['pos'] is None:
                info['pos'] = h.pos()
        # Connect the handle to this ROI
        h.connectROI(self)
        if index is None:
            self.handles.append(info)
        else:
            self.handles.insert(index, info)
        h.setZValue(self.zValue()+1)
        h.sigRemoveRequested.connect(self.removeHandle)
        h.handleMenuSignal.connect(self.relayMenuTime)
        self.stateChanged(finish=True)
        return h
    
    # Relay the time of a menu pop up on a handle 
    def relayMenuTime(self,aTime):
        self.handleMenuSignal.emit(aTime)

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
        self.clickDownPos=False # Mouse position upon clicking down
        # Add in the hovered over station label
        self.hoverStaItem=pg.TextItem(text='',anchor=(0.5,1))
        self.hoverStaItem.hide()
        self.map.addItem(self.hoverStaItem)
        # Show station text when hovering over the station symbol
        self.scene().sigMouseMoved.connect(self.onHover)
        # Holder for editable polygon
        self.polygon=None
        self.handleMenuTime=0

    # Track where the mouse was pressed down
    def mousePressEvent(self, event):
        pg.GraphicsLayoutWidget.mousePressEvent(self,event)
        self.clickDownPos=event.pos()
    
    # If no dragging occcured and handle menu was not created, create menu to add polygon
    def mouseReleaseEvent(self,event):
        pg.GraphicsLayoutWidget.mouseReleaseEvent(self,event)
        if (event.pos()==self.clickDownPos and event.button() == QtCore.Qt.RightButton and
            time.time()-self.handleMenuTime>0.05):
            self.createMenu(event)
            
    # Add some functionality to default hover events...
    # ...see which station is being hovered over
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
        
    # Handle double click events to the station scatter item
    def dblClicked(self,staScat):
        self.clickPos=list(staScat.clickPos)
        # Update the nearby station which was clicked
        self.selectSta=self.getSelectSta(staScat.clickPos,staScat.ptsClicked)
        # Forward the double clicked signal to main window
        self.doubleClicked.emit()
        
    # Create pop up menu to add/remove groups/variables
    def createMenu(self,event, parent=None):
        pixelPos=event.pos()
        self.menu=QtWidgets.QMenu(parent)
        if self.polygon is None:
            self.menu.addAction('Add polygon', lambda:self.addPolygon(pixelPos))
        else:
            self.menu.addAction('Remove polygon',self.removePolygon)
        self.menu.move(self.mapToGlobal(QtCore.QPoint(0,0))+pixelPos)
        self.menu.show()
        
    # Add the polygon to map 
    def addPolygon(self,pixelPos,verticies=None):
        # If no verticies giveb, make a box near clicked position
        if verticies is None:
            viewBox=self.map.getViewBox()
            # Convert from pixel position
            clickPos=viewBox.mapSceneToView(pixelPos)
            clickPos=np.array([clickPos.x(),clickPos.y()])
            # Get the map axis lengths
            xLen,yLen=np.diff(np.array(viewBox.viewRange(),dtype=float),axis=1)*0.2
            xLen,yLen=xLen[0],yLen[0]
            verticies=[clickPos+np.array(extra) for extra in [[0,0],[0,yLen],[xLen,yLen],[xLen,0]]]
        self.polygon=RoiPolyLine(verticies, closed=True)
        self.polygon.handleMenuSignal.connect(self.setHandleMenuTime)
        self.map.addItem(self.polygon)
        
    # Remove polygon from the map
    def removePolygon(self):
        self.map.removeItem(self.polygon)
        self.polygon=None
    
    # Set the time the handle menu was created
    def setHandleMenuTime(self,aTime):
        self.handleMenuTime=aTime
        
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
        # Remove the old polygon
        if self.polygon is not None:
            self.removePolygon()
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
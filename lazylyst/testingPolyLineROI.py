import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

#http://www.pyqtgraph.org/documentation/_modules/pyqtgraph/graphicsItems/ROI.html#PolyLineROI

## create GUI  
        
app = QtGui.QApplication([])
w = pg.GraphicsWindow(size=(1000,800), border=True)
w.setWindowTitle('pyqtgraph example: ROI Examples')

class MyHandle(pg.graphicsItems.ROI.Handle):
    def __init__(self, *args, **kwargs):
        super(MyHandle, self).__init__(*args, **kwargs)
        
    def mouseClickEvent(self, ev):
        print 123
        ## right-click cancels drag
        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            self.isMoving = False  ## prevents any further motion
            self.movePoint(self.startPos, finish=True)
            #for r in self.roi:
                #r[0].cancelMove()
            ev.accept()
        elif int(ev.button() & self.acceptedMouseButtons()) > 0:
            ev.accept()
            if ev.button() == QtCore.Qt.RightButton and self.deletable:
                self.raiseContextMenu(ev)
            self.sigClicked.emit(self, ev)
        else:
            ev.ignore()    
        
class MyPolyLineROI(pg.PolyLineROI):
    def __init__(self, *args, **kwargs):
        super(MyPolyLineROI, self).__init__(*args, **kwargs)
        

    def mouseClickEvent(self, ev):
        print 5555
        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            ev.accept()
            self.cancelMove()
        if ev.button() == QtCore.Qt.RightButton and self.contextMenuEnabled():
            self.raiseContextMenu(ev)
            ev.accept()
        elif int(ev.button() & self.acceptedMouseButtons()) > 0:
            ev.accept()
            self.sigClicked.emit(self, ev)
        else:
            ev.ignore() 
    
    def addHandle(self, info, index=None):
#        addHandle(self, info, index=None):
        ## If a Handle was not supplied, create it now
        if 'item' not in info or info['item'] is None:
            h = MyHandle(self.handleSize, typ=info['type'], pen=self.handlePen, parent=self)
            h.setPos(info['pos'] * self.state['size'])
            info['item'] = h
        else:
            h = info['item']
            if info['pos'] is None:
                info['pos'] = h.pos()
            
        ## connect the handle to this ROI
        h.connectROI(self)
        if index is None:
            self.handles.append(info)
        else:
            self.handles.insert(index, info)
        
        h.setZValue(self.zValue()+1)
        self.stateChanged()
#        return h
        h.sigRemoveRequested.connect(self.removeHandle)
        self.stateChanged(finish=True)
        return h
            
    def raiseContextMenu(self, ev):
            """
            Raise the context menu
            """
            print 'woooo'
            if not self.menuEnabled():
                return
            menu = self.getMenu()
            pos  = ev.screenPos()
            menu.popup(QtCore.QPoint(pos.x(), pos.y()))
            
text = """User-Modifiable ROIs<br>
Click on a line segment to add a new handle.
Right click on a handle to remove.
"""
w2 = w.addLayout(row=0, col=0)
label2 = w2.addLabel(text, row=0, col=0)
v2a = w2.addViewBox(row=1, col=0, lockAspect=True)
r2a = MyPolyLineROI([[90,0], [10,10], [10,30], [30,10]], closed=True)
v2a.addItem(r2a)
#v2a.disableAutoRange('xy')
#v2b.disableAutoRange('xy')
v2a.autoRange()

#r2a.mouseCli

#def hi():
#    print 1

#print dir(r2a.segmentClicked)
#print dir(r2a)
#print dir(r2a.getHandles()[0])
#print r2a.getHandles()[0].x()
#for handle in r2a.getHandles():
#    print handle.x(),handle.y()
#quit()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
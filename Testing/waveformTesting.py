from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
import numpy as np
import pyqtgraph as pg
from obspy import read, UTCDateTime

st=read('0000000011_20150907.050000.000000.seed')
st.sort(keys=['station','channel'])
st.detrend()
st.filter('highpass',freq=1.0,corners=1,zerophase=True)

class PltWidget(pg.PlotWidget):
    def __init__(self, parent=None,sta=None):
        super(PltWidget, self).__init__(parent)
        self.pltItem=self.getPlotItem()
        self.pltItem.setMenuEnabled(enableMenu=False)
        # Speed up the panning and zooming
        self.pltItem.setClipToView(True)
        self.pltItem.setDownsampling(True, True, 'peak')
        # Only show the left axis
        self.pltItem.hideAxis('bottom')
        self.pltItem.hideButtons()
        self.pltItem.getAxis('left').setWidth(70)
        # Assign this widget a station
        self.sta=sta   
        # Give this widget a set of vertical lines (represents a pick)
        self.vlines=[]
    
    # The built in buttons for each trace window
    def keyPressEvent(self, ev):
        super(PltWidget, self).keyPressEvent(ev)
        # Remove all picks from the current axis
        if ev.key()==Qt.Key_4:
            for aLine in self.vlines:
                self.pltItem.removeItem(aLine)
            self.vlines=[]
    
    # Place a vertical lines when double clicked
    def mouseDoubleClickEvent(self, ev):
        super(PltWidget, self).mouseDoubleClickEvent(ev)
        aPos=self.pltItem.vb.mapSceneToView(ev.pos())
        self.vlines.append(self.pltItem.addLine(x=aPos.x(),pen=(255,0,0)))
    
    # Ensure that key presses are sent to the widget which the mouse is hovering over
    def enterEvent(self,ev):
        super(PltWidget, self).enterEvent(ev)
        self.setFocus()

class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(TimeAxisItem, self).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [UTCDateTime(value).strftime("%H:%M:%S.%f") for value in values]

class TimeWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super(TimeWidget, self).__init__(parent,name='timeAxis',axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self.getPlotItem().getAxis('left').setWidth(70)
        self.getPlotItem().setMenuEnabled(enableMenu=False)
        self.getPlotItem().hideButtons()
        
app=QtGui.QApplication([])
mw=QtGui.QMainWindow()
mw.setWindowTitle('pyqtgraph example: PlotWidget')
mw.resize(800,800)
# set layout
cw=QtGui.QWidget()
mw.setCentralWidget(cw)
l=QtGui.QVBoxLayout()
l.setSpacing(1)
cw.setLayout(l)


timeWidget=TimeWidget()
l.addWidget(timeWidget)

# Add all of the other bits
for j in range(5):
    aPW=PltWidget(sta=st[3*j+1].stats.station)
    l.addWidget(aPW)
    for i in range(3):
        aLine=aPW.plot(y=st[3*j+i].data,x=st[3*j+i].times()+st[3*j+i].stats.starttime.timestamp)
    aPW.setXLink('timeAxis')

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        mw.show()
        QtGui.QApplication.instance().exec_()
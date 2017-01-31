import sys
import sip
sip.setapi('QVariant', 2)
sip.setapi('QString', 2)
from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import QSettings
from TestMainWindow import Ui_TestMainWindow

# Main window class
class TestMain(QtGui.QMainWindow, Ui_TestMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_TestMainWindow.__init__(self)
        self.setupUi(self)

# Start up the logging and UI
if __name__ == '__main__':
    # Start up the UI
    app = QtGui.QApplication(sys.argv)
    window = TestMain()
    window.show()
    sys.exit(app.exec_())
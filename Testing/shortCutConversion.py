import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt

def main():
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())

class MyWindow(QtGui.QWidget):
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)

        self.la = QLabel("Press tab in this box:")
        self.le = MyLineEdit()

        layout = QVBoxLayout()
        layout.addWidget(self.la)
        layout.addWidget(self.le)
        self.setLayout(layout)

        self.le.keyPressed.connect(self.update)

    def update(self, text):
        self.le.setText(text)

MOD_MASK = (Qt.CTRL | Qt.ALT | Qt.SHIFT | Qt.META)

class KeyBindLineEdit(QtGui.QLineEdit):
    keyPressed = QtCore.pyqtSignal(str)

    # If any usual key bind was pressed, return the human recognizable string
    def keyPressEvent(self, event):
        keyname = ''
        key = event.key()
        modifiers = int(event.modifiers())
        if key in [Qt.Key_Shift,Qt.Key_Alt,Qt.Key_Control,Qt.Key_Meta]:
            return
        elif (modifiers and modifiers & MOD_MASK==modifiers and key>0):
            keyname=QtGui.QKeySequence(modifiers+key).toString()
        else:
            keyname=QtGui.QKeySequence(key).toString()
        self.keyPressed.emit(keyname)

if __name__ == "__main__":
    main()
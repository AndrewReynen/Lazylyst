import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

def main():
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())

class MyWindow(QWidget):
    def __init__(self, *args):
        QWidget.__init__(self, *args)

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

class MyLineEdit(QLineEdit):
    keyPressed = pyqtSignal(str)

    def keyPressEvent(self, event):
        keyname = ''
        key = event.key()
        modifiers = int(event.modifiers())
        if (modifiers and modifiers & MOD_MASK == modifiers and
            key > 0 and key != Qt.Key_Shift and key != Qt.Key_Alt and
            key != Qt.Key_Control and key != Qt.Key_Meta):

            keyname = QKeySequence(modifiers + key).toString()

            print('event.text(): %r' % event.text())
            print('event.key(): %d, %#x, %s' % (key, key, keyname))
        self.keyPressed.emit(keyname)

if __name__ == "__main__":
    main()
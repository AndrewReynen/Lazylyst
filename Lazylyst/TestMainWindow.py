# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'TestMainWindow.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_TestMainWindow(object):
    def setupUi(self, TestMainWindow):
        TestMainWindow.setObjectName(_fromUtf8("TestMainWindow"))
        TestMainWindow.resize(707, 709)
        self.centralwidget = QtGui.QWidget(TestMainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.widget = CustDockArea(self.centralwidget)
        self.widget.setObjectName(_fromUtf8("widget"))
        self.widget_2 = CustDock(self.widget)
        self.widget_2.setGeometry(QtCore.QRect(70, 180, 211, 241))
        self.widget_2.setObjectName(_fromUtf8("widget_2"))
        self.lineEdit = QtGui.QLineEdit(self.widget_2)
        self.lineEdit.setGeometry(QtCore.QRect(50, 80, 113, 27))
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.lineEdit_2 = QtGui.QLineEdit(self.widget_2)
        self.lineEdit_2.setGeometry(QtCore.QRect(60, 150, 113, 27))
        self.lineEdit_2.setObjectName(_fromUtf8("lineEdit_2"))
        self.verticalLayout.addWidget(self.widget)
        TestMainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(TestMainWindow)
        QtCore.QMetaObject.connectSlotsByName(TestMainWindow)

    def retranslateUi(self, TestMainWindow):
        TestMainWindow.setWindowTitle(_translate("TestMainWindow", "TestMainWindow", None))

from CustomWidgets import CustDock, CustDockArea

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'TracePen.ui'
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

class Ui_tracePenDialog(object):
    def setupUi(self, tracePenDialog):
        tracePenDialog.setObjectName(_fromUtf8("tracePenDialog"))
        tracePenDialog.resize(400, 300)
        self.verticalLayout = QtGui.QVBoxLayout(tracePenDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tpTable = QtGui.QTableWidget(tracePenDialog)
        self.tpTable.setObjectName(_fromUtf8("tpTable"))
        self.tpTable.setColumnCount(0)
        self.tpTable.setRowCount(0)
        self.verticalLayout.addWidget(self.tpTable)
        self.tpButtonLayout = QtGui.QHBoxLayout()
        self.tpButtonLayout.setObjectName(_fromUtf8("tpButtonLayout"))
        self.tpInsertButton = QtGui.QPushButton(tracePenDialog)
        self.tpInsertButton.setObjectName(_fromUtf8("tpInsertButton"))
        self.tpButtonLayout.addWidget(self.tpInsertButton)
        self.tpDeleteButton = QtGui.QPushButton(tracePenDialog)
        self.tpDeleteButton.setObjectName(_fromUtf8("tpDeleteButton"))
        self.tpButtonLayout.addWidget(self.tpDeleteButton)
        self.verticalLayout.addLayout(self.tpButtonLayout)

        self.retranslateUi(tracePenDialog)
        QtCore.QMetaObject.connectSlotsByName(tracePenDialog)

    def retranslateUi(self, tracePenDialog):
        tracePenDialog.setWindowTitle(_translate("tracePenDialog", "Trace Pen", None))
        self.tpInsertButton.setText(_translate("tracePenDialog", "Insert", None))
        self.tpDeleteButton.setText(_translate("tracePenDialog", "Delete", None))


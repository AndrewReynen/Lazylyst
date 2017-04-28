# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'BasePen.ui'
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

class Ui_basePenDialog(object):
    def setupUi(self, basePenDialog):
        basePenDialog.setObjectName(_fromUtf8("basePenDialog"))
        basePenDialog.resize(393, 512)
        self.verticalLayout = QtGui.QVBoxLayout(basePenDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tpTable = QtGui.QTableWidget(basePenDialog)
        self.tpTable.setObjectName(_fromUtf8("tpTable"))
        self.tpTable.setColumnCount(0)
        self.tpTable.setRowCount(0)
        self.verticalLayout.addWidget(self.tpTable)

        self.retranslateUi(basePenDialog)
        QtCore.QMetaObject.connectSlotsByName(basePenDialog)

    def retranslateUi(self, basePenDialog):
        basePenDialog.setWindowTitle(_translate("basePenDialog", "basePen", None))


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'BasePen.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_basePenDialog(object):
    def setupUi(self, basePenDialog):
        basePenDialog.setObjectName("basePenDialog")
        basePenDialog.resize(393, 512)
        self.verticalLayout = QtWidgets.QVBoxLayout(basePenDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tpTable = QtWidgets.QTableWidget(basePenDialog)
        self.tpTable.setObjectName("tpTable")
        self.tpTable.setColumnCount(0)
        self.tpTable.setRowCount(0)
        self.verticalLayout.addWidget(self.tpTable)

        self.retranslateUi(basePenDialog)
        QtCore.QMetaObject.connectSlotsByName(basePenDialog)

    def retranslateUi(self, basePenDialog):
        _translate = QtCore.QCoreApplication.translate
        basePenDialog.setWindowTitle(_translate("basePenDialog", "basePen"))


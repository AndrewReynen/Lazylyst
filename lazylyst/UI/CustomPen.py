# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'CustomPen.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_customPenDialog(object):
    def setupUi(self, customPenDialog):
        customPenDialog.setObjectName("customPenDialog")
        customPenDialog.resize(477, 338)
        self.verticalLayout = QtWidgets.QVBoxLayout(customPenDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tpTable = QtWidgets.QTableWidget(customPenDialog)
        self.tpTable.setObjectName("tpTable")
        self.tpTable.setColumnCount(0)
        self.tpTable.setRowCount(0)
        self.verticalLayout.addWidget(self.tpTable)
        self.tpButtonLayout = QtWidgets.QHBoxLayout()
        self.tpButtonLayout.setObjectName("tpButtonLayout")
        self.tpInsertButton = QtWidgets.QPushButton(customPenDialog)
        self.tpInsertButton.setObjectName("tpInsertButton")
        self.tpButtonLayout.addWidget(self.tpInsertButton)
        self.tpDeleteButton = QtWidgets.QPushButton(customPenDialog)
        self.tpDeleteButton.setObjectName("tpDeleteButton")
        self.tpButtonLayout.addWidget(self.tpDeleteButton)
        self.verticalLayout.addLayout(self.tpButtonLayout)

        self.retranslateUi(customPenDialog)
        QtCore.QMetaObject.connectSlotsByName(customPenDialog)

    def retranslateUi(self, customPenDialog):
        _translate = QtCore.QCoreApplication.translate
        customPenDialog.setWindowTitle(_translate("customPenDialog", "Custom Pen"))
        self.tpInsertButton.setText(_translate("customPenDialog", "Insert"))
        self.tpDeleteButton.setText(_translate("customPenDialog", "Delete"))


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ComboDialog.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_comboBoxDialog(object):
    def setupUi(self, comboBoxDialog):
        comboBoxDialog.setObjectName("comboBoxDialog")
        comboBoxDialog.resize(352, 84)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(comboBoxDialog.sizePolicy().hasHeightForWidth())
        comboBoxDialog.setSizePolicy(sizePolicy)
        comboBoxDialog.setMinimumSize(QtCore.QSize(0, 84))
        comboBoxDialog.setMaximumSize(QtCore.QSize(16777215, 84))
        self.verticalLayout = QtWidgets.QVBoxLayout(comboBoxDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.comboBox = QtWidgets.QComboBox(comboBoxDialog)
        self.comboBox.setObjectName("comboBox")
        self.verticalLayout.addWidget(self.comboBox)
        self.buttonBox = QtWidgets.QDialogButtonBox(comboBoxDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        spacerItem = QtWidgets.QSpacerItem(20, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(comboBoxDialog)
        self.buttonBox.accepted.connect(comboBoxDialog.accept)
        self.buttonBox.rejected.connect(comboBoxDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(comboBoxDialog)

    def retranslateUi(self, comboBoxDialog):
        _translate = QtCore.QCoreApplication.translate
        comboBoxDialog.setWindowTitle(_translate("comboBoxDialog", "Dialog"))


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ListEntry.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_listEntryDialog(object):
    def setupUi(self, listEntryDialog):
        listEntryDialog.setObjectName("listEntryDialog")
        listEntryDialog.resize(555, 269)
        self.verticalLayout = QtWidgets.QVBoxLayout(listEntryDialog)
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setObjectName("verticalLayout")
        self.topListEntryLayout = QtWidgets.QHBoxLayout()
        self.topListEntryLayout.setSpacing(1)
        self.topListEntryLayout.setObjectName("topListEntryLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.topListEntryLayout.addItem(spacerItem)
        self.entryAddButton = QtWidgets.QPushButton(listEntryDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.entryAddButton.sizePolicy().hasHeightForWidth())
        self.entryAddButton.setSizePolicy(sizePolicy)
        self.entryAddButton.setMinimumSize(QtCore.QSize(25, 25))
        self.entryAddButton.setMaximumSize(QtCore.QSize(25, 25))
        self.entryAddButton.setAutoDefault(False)
        self.entryAddButton.setObjectName("entryAddButton")
        self.topListEntryLayout.addWidget(self.entryAddButton)
        self.entryDelButton = QtWidgets.QPushButton(listEntryDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.entryDelButton.sizePolicy().hasHeightForWidth())
        self.entryDelButton.setSizePolicy(sizePolicy)
        self.entryDelButton.setMinimumSize(QtCore.QSize(25, 25))
        self.entryDelButton.setMaximumSize(QtCore.QSize(25, 25))
        self.entryDelButton.setAutoDefault(False)
        self.entryDelButton.setObjectName("entryDelButton")
        self.topListEntryLayout.addWidget(self.entryDelButton)
        self.verticalLayout.addLayout(self.topListEntryLayout)
        self.entryListWidget = MixListWidget(listEntryDialog)
        self.entryListWidget.setObjectName("entryListWidget")
        self.verticalLayout.addWidget(self.entryListWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(listEntryDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(listEntryDialog)
        self.buttonBox.accepted.connect(listEntryDialog.accept)
        self.buttonBox.rejected.connect(listEntryDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(listEntryDialog)

    def retranslateUi(self, listEntryDialog):
        _translate = QtCore.QCoreApplication.translate
        listEntryDialog.setWindowTitle(_translate("listEntryDialog", "List Entry Dialog"))
        self.entryAddButton.setText(_translate("listEntryDialog", "+"))
        self.entryDelButton.setText(_translate("listEntryDialog", "-"))

from lazylyst.CustomWidgets import MixListWidget

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Configuration.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ConfDialog(object):
    def setupUi(self, ConfDialog):
        ConfDialog.setObjectName("ConfDialog")
        ConfDialog.resize(634, 535)
        self.horizontalLayout = QtWidgets.QHBoxLayout(ConfDialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.confPrefLayout = QtWidgets.QVBoxLayout()
        self.confPrefLayout.setSpacing(1)
        self.confPrefLayout.setObjectName("confPrefLayout")
        self.confPrefLabel = QtWidgets.QLabel(ConfDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.confPrefLabel.sizePolicy().hasHeightForWidth())
        self.confPrefLabel.setSizePolicy(sizePolicy)
        self.confPrefLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.confPrefLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.confPrefLabel.setObjectName("confPrefLabel")
        self.confPrefLayout.addWidget(self.confPrefLabel)
        self.confPrefList = MixListWidget(ConfDialog)
        self.confPrefList.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.confPrefList.setObjectName("confPrefList")
        self.confPrefLayout.addWidget(self.confPrefList)
        self.horizontalLayout.addLayout(self.confPrefLayout)
        self.confActionsLayout = QtWidgets.QVBoxLayout()
        self.confActionsLayout.setSpacing(1)
        self.confActionsLayout.setObjectName("confActionsLayout")
        self.confPassiveLayout = QtWidgets.QVBoxLayout()
        self.confPassiveLayout.setSpacing(1)
        self.confPassiveLayout.setObjectName("confPassiveLayout")
        self.confPassiveLabel = QtWidgets.QLabel(ConfDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.confPassiveLabel.sizePolicy().hasHeightForWidth())
        self.confPassiveLabel.setSizePolicy(sizePolicy)
        self.confPassiveLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.confPassiveLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.confPassiveLabel.setObjectName("confPassiveLabel")
        self.confPassiveLayout.addWidget(self.confPassiveLabel)
        self.confPassiveList = MixListWidget(ConfDialog)
        self.confPassiveList.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.confPassiveList.setObjectName("confPassiveList")
        self.confPassiveLayout.addWidget(self.confPassiveList)
        self.confActionsLayout.addLayout(self.confPassiveLayout)
        self.confActiveLayout = QtWidgets.QVBoxLayout()
        self.confActiveLayout.setSpacing(1)
        self.confActiveLayout.setObjectName("confActiveLayout")
        self.confActiveLabel = QtWidgets.QLabel(ConfDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.confActiveLabel.sizePolicy().hasHeightForWidth())
        self.confActiveLabel.setSizePolicy(sizePolicy)
        self.confActiveLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.confActiveLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.confActiveLabel.setObjectName("confActiveLabel")
        self.confActiveLayout.addWidget(self.confActiveLabel)
        self.confActiveList = MixListWidget(ConfDialog)
        self.confActiveList.setObjectName("confActiveList")
        self.confActiveLayout.addWidget(self.confActiveList)
        self.confActionsLayout.addLayout(self.confActiveLayout)
        self.horizontalLayout.addLayout(self.confActionsLayout)

        self.retranslateUi(ConfDialog)
        QtCore.QMetaObject.connectSlotsByName(ConfDialog)

    def retranslateUi(self, ConfDialog):
        _translate = QtCore.QCoreApplication.translate
        ConfDialog.setWindowTitle(_translate("ConfDialog", "Configuration"))
        self.confPrefLabel.setText(_translate("ConfDialog", "Preferences"))
        self.confPrefList.setSortingEnabled(True)
        self.confPassiveLabel.setText(_translate("ConfDialog", "Passive Actions Ordering"))
        self.confActiveLabel.setText(_translate("ConfDialog", "Active Actions"))
        self.confActiveList.setSortingEnabled(True)

from CustomWidgets import MixListWidget

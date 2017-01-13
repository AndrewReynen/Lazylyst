# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Configuration.ui'
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

class Ui_ConfDialog(object):
    def setupUi(self, ConfDialog):
        ConfDialog.setObjectName(_fromUtf8("ConfDialog"))
        ConfDialog.resize(634, 535)
        self.horizontalLayout = QtGui.QHBoxLayout(ConfDialog)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.confPrefLayout = QtGui.QVBoxLayout()
        self.confPrefLayout.setSpacing(1)
        self.confPrefLayout.setObjectName(_fromUtf8("confPrefLayout"))
        self.confPrefLabel = QtGui.QLabel(ConfDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.confPrefLabel.sizePolicy().hasHeightForWidth())
        self.confPrefLabel.setSizePolicy(sizePolicy)
        self.confPrefLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.confPrefLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.confPrefLabel.setObjectName(_fromUtf8("confPrefLabel"))
        self.confPrefLayout.addWidget(self.confPrefLabel)
        self.confPrefList = MixListWidget(ConfDialog)
        self.confPrefList.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.confPrefList.setObjectName(_fromUtf8("confPrefList"))
        self.confPrefLayout.addWidget(self.confPrefList)
        self.horizontalLayout.addLayout(self.confPrefLayout)
        self.confActionsLayout = QtGui.QVBoxLayout()
        self.confActionsLayout.setSpacing(1)
        self.confActionsLayout.setObjectName(_fromUtf8("confActionsLayout"))
        self.confPassiveLayout = QtGui.QVBoxLayout()
        self.confPassiveLayout.setSpacing(1)
        self.confPassiveLayout.setObjectName(_fromUtf8("confPassiveLayout"))
        self.confPassiveLabel = QtGui.QLabel(ConfDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.confPassiveLabel.sizePolicy().hasHeightForWidth())
        self.confPassiveLabel.setSizePolicy(sizePolicy)
        self.confPassiveLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.confPassiveLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.confPassiveLabel.setObjectName(_fromUtf8("confPassiveLabel"))
        self.confPassiveLayout.addWidget(self.confPassiveLabel)
        self.confPassiveList = MixListWidget(ConfDialog)
        self.confPassiveList.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.confPassiveList.setObjectName(_fromUtf8("confPassiveList"))
        self.confPassiveLayout.addWidget(self.confPassiveList)
        self.confActionsLayout.addLayout(self.confPassiveLayout)
        self.confActiveLayout = QtGui.QVBoxLayout()
        self.confActiveLayout.setSpacing(1)
        self.confActiveLayout.setObjectName(_fromUtf8("confActiveLayout"))
        self.confActiveLabel = QtGui.QLabel(ConfDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.confActiveLabel.sizePolicy().hasHeightForWidth())
        self.confActiveLabel.setSizePolicy(sizePolicy)
        self.confActiveLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.confActiveLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.confActiveLabel.setObjectName(_fromUtf8("confActiveLabel"))
        self.confActiveLayout.addWidget(self.confActiveLabel)
        self.confActiveList = MixListWidget(ConfDialog)
        self.confActiveList.setObjectName(_fromUtf8("confActiveList"))
        self.confActiveLayout.addWidget(self.confActiveList)
        self.confActionsLayout.addLayout(self.confActiveLayout)
        self.horizontalLayout.addLayout(self.confActionsLayout)

        self.retranslateUi(ConfDialog)
        QtCore.QMetaObject.connectSlotsByName(ConfDialog)

    def retranslateUi(self, ConfDialog):
        ConfDialog.setWindowTitle(_translate("ConfDialog", "Configuration", None))
        self.confPrefLabel.setText(_translate("ConfDialog", "Preferences", None))
        self.confPassiveLabel.setText(_translate("ConfDialog", "Passive Actions Ordering", None))
        self.confActiveLabel.setText(_translate("ConfDialog", "Active Actions", None))
        self.confActiveList.setSortingEnabled(True)

from CustomWidgets import MixListWidget

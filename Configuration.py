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

class Ui_confDialog(object):
    def setupUi(self, confDialog):
        confDialog.setObjectName(_fromUtf8("confDialog"))
        confDialog.resize(634, 535)
        self.horizontalLayout = QtGui.QHBoxLayout(confDialog)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.confPrefLayout = QtGui.QVBoxLayout()
        self.confPrefLayout.setSpacing(1)
        self.confPrefLayout.setObjectName(_fromUtf8("confPrefLayout"))
        self.confPrefLabel = QtGui.QLabel(confDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.confPrefLabel.sizePolicy().hasHeightForWidth())
        self.confPrefLabel.setSizePolicy(sizePolicy)
        self.confPrefLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.confPrefLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.confPrefLabel.setObjectName(_fromUtf8("confPrefLabel"))
        self.confPrefLayout.addWidget(self.confPrefLabel)
        self.confPrefList = KeyListWidget(confDialog)
        self.confPrefList.setObjectName(_fromUtf8("confPrefList"))
        self.confPrefLayout.addWidget(self.confPrefList)
        self.horizontalLayout.addLayout(self.confPrefLayout)
        self.confActionsLayout = QtGui.QVBoxLayout()
        self.confActionsLayout.setSpacing(1)
        self.confActionsLayout.setObjectName(_fromUtf8("confActionsLayout"))
        self.confPassiveLayout = QtGui.QVBoxLayout()
        self.confPassiveLayout.setSpacing(1)
        self.confPassiveLayout.setObjectName(_fromUtf8("confPassiveLayout"))
        self.confPassiveLabel = QtGui.QLabel(confDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.confPassiveLabel.sizePolicy().hasHeightForWidth())
        self.confPassiveLabel.setSizePolicy(sizePolicy)
        self.confPassiveLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.confPassiveLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.confPassiveLabel.setObjectName(_fromUtf8("confPassiveLabel"))
        self.confPassiveLayout.addWidget(self.confPassiveLabel)
        self.confPassiveList = KeyListWidget(confDialog)
        self.confPassiveList.setObjectName(_fromUtf8("confPassiveList"))
        self.confPassiveLayout.addWidget(self.confPassiveList)
        self.confActionsLayout.addLayout(self.confPassiveLayout)
        self.confActiveLayout = QtGui.QVBoxLayout()
        self.confActiveLayout.setSpacing(1)
        self.confActiveLayout.setObjectName(_fromUtf8("confActiveLayout"))
        self.confActiveLabel = QtGui.QLabel(confDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.confActiveLabel.sizePolicy().hasHeightForWidth())
        self.confActiveLabel.setSizePolicy(sizePolicy)
        self.confActiveLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.confActiveLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.confActiveLabel.setObjectName(_fromUtf8("confActiveLabel"))
        self.confActiveLayout.addWidget(self.confActiveLabel)
        self.confActiveList = KeyListWidget(confDialog)
        self.confActiveList.setObjectName(_fromUtf8("confActiveList"))
        self.confActiveLayout.addWidget(self.confActiveList)
        self.confActionsLayout.addLayout(self.confActiveLayout)
        self.horizontalLayout.addLayout(self.confActionsLayout)

        self.retranslateUi(confDialog)
        QtCore.QMetaObject.connectSlotsByName(confDialog)

    def retranslateUi(self, confDialog):
        confDialog.setWindowTitle(_translate("confDialog", "Configuration", None))
        self.confPrefLabel.setText(_translate("confDialog", "Preferences", None))
        self.confPassiveLabel.setText(_translate("confDialog", "Passive Actions Ordering", None))
        self.confActiveLabel.setText(_translate("confDialog", "Active Actions Ordering", None))

from CustomWidgets import KeyListWidget

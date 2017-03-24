# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ComboDialog.ui'
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

class Ui_comboBoxDialog(object):
    def setupUi(self, comboBoxDialog):
        comboBoxDialog.setObjectName(_fromUtf8("comboBoxDialog"))
        comboBoxDialog.resize(352, 84)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(comboBoxDialog.sizePolicy().hasHeightForWidth())
        comboBoxDialog.setSizePolicy(sizePolicy)
        comboBoxDialog.setMinimumSize(QtCore.QSize(0, 84))
        comboBoxDialog.setMaximumSize(QtCore.QSize(16777215, 84))
        self.verticalLayout = QtGui.QVBoxLayout(comboBoxDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.comboBox = QtGui.QComboBox(comboBoxDialog)
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.verticalLayout.addWidget(self.comboBox)
        self.buttonBox = QtGui.QDialogButtonBox(comboBoxDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)
        spacerItem = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(comboBoxDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), comboBoxDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), comboBoxDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(comboBoxDialog)

    def retranslateUi(self, comboBoxDialog):
        comboBoxDialog.setWindowTitle(_translate("comboBoxDialog", "Dialog", None))


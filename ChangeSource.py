# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ChangeSource.ui'
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

class Ui_CsDialog(object):
    def setupUi(self, CsDialog):
        CsDialog.setObjectName(_fromUtf8("CsDialog"))
        CsDialog.resize(636, 529)
        CsDialog.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.verticalLayout = QtGui.QVBoxLayout(CsDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.csLineEditLayout = QtGui.QGridLayout()
        self.csLineEditLayout.setSpacing(1)
        self.csLineEditLayout.setObjectName(_fromUtf8("csLineEditLayout"))
        self.csStationLabel = QtGui.QLabel(CsDialog)
        self.csStationLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csStationLabel.setObjectName(_fromUtf8("csStationLabel"))
        self.csLineEditLayout.addWidget(self.csStationLabel, 3, 0, 1, 1)
        self.csPickLabel = QtGui.QLabel(CsDialog)
        self.csPickLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csPickLabel.setObjectName(_fromUtf8("csPickLabel"))
        self.csLineEditLayout.addWidget(self.csPickLabel, 2, 0, 1, 1)
        self.csStationLineEdit = DblClickLineEdit(CsDialog)
        self.csStationLineEdit.setObjectName(_fromUtf8("csStationLineEdit"))
        self.csLineEditLayout.addWidget(self.csStationLineEdit, 3, 1, 1, 1)
        self.csTagLineEdit = QtGui.QLineEdit(CsDialog)
        self.csTagLineEdit.setObjectName(_fromUtf8("csTagLineEdit"))
        self.csLineEditLayout.addWidget(self.csTagLineEdit, 0, 1, 1, 1)
        self.csPickLineEdit = DblClickLineEdit(CsDialog)
        self.csPickLineEdit.setObjectName(_fromUtf8("csPickLineEdit"))
        self.csLineEditLayout.addWidget(self.csPickLineEdit, 2, 1, 1, 1)
        self.csTagLabel = QtGui.QLabel(CsDialog)
        self.csTagLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csTagLabel.setObjectName(_fromUtf8("csTagLabel"))
        self.csLineEditLayout.addWidget(self.csTagLabel, 0, 0, 1, 1)
        self.csArchiveLabel = QtGui.QLabel(CsDialog)
        self.csArchiveLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csArchiveLabel.setObjectName(_fromUtf8("csArchiveLabel"))
        self.csLineEditLayout.addWidget(self.csArchiveLabel, 1, 0, 1, 1)
        self.csArchiveLineEdit = DblClickLineEdit(CsDialog)
        self.csArchiveLineEdit.setObjectName(_fromUtf8("csArchiveLineEdit"))
        self.csLineEditLayout.addWidget(self.csArchiveLineEdit, 1, 1, 1, 1)
        self.csSaveSourceButton = QtGui.QPushButton(CsDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.csSaveSourceButton.sizePolicy().hasHeightForWidth())
        self.csSaveSourceButton.setSizePolicy(sizePolicy)
        self.csSaveSourceButton.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.csSaveSourceButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.csSaveSourceButton.setObjectName(_fromUtf8("csSaveSourceButton"))
        self.csLineEditLayout.addWidget(self.csSaveSourceButton, 3, 2, 1, 1)
        self.verticalLayout.addLayout(self.csLineEditLayout)
        self.csSaveSourceLabel = QtGui.QLabel(CsDialog)
        self.csSaveSourceLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csSaveSourceLabel.setObjectName(_fromUtf8("csSaveSourceLabel"))
        self.verticalLayout.addWidget(self.csSaveSourceLabel)
        self.csSaveSourceList = KeyListWidget(CsDialog)
        self.csSaveSourceList.setObjectName(_fromUtf8("csSaveSourceList"))
        self.verticalLayout.addWidget(self.csSaveSourceList)
        self.buttonBox = QtGui.QDialogButtonBox(CsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CsDialog)
        CsDialog.setTabOrder(self.csTagLineEdit, self.csArchiveLineEdit)
        CsDialog.setTabOrder(self.csArchiveLineEdit, self.csPickLineEdit)
        CsDialog.setTabOrder(self.csPickLineEdit, self.csStationLineEdit)
        CsDialog.setTabOrder(self.csStationLineEdit, self.csSaveSourceButton)
        CsDialog.setTabOrder(self.csSaveSourceButton, self.csSaveSourceList)
        CsDialog.setTabOrder(self.csSaveSourceList, self.buttonBox)

    def retranslateUi(self, CsDialog):
        CsDialog.setWindowTitle(_translate("CsDialog", "Change Source", None))
        self.csStationLabel.setText(_translate("CsDialog", "Station File", None))
        self.csPickLabel.setText(_translate("CsDialog", "Pick Directory", None))
        self.csTagLabel.setText(_translate("CsDialog", "Tag", None))
        self.csArchiveLabel.setText(_translate("CsDialog", "Archive Directory", None))
        self.csSaveSourceButton.setText(_translate("CsDialog", "Save Source", None))
        self.csSaveSourceLabel.setText(_translate("CsDialog", "Saved Sources", None))

from CustomWidgets import DblClickLineEdit, KeyListWidget

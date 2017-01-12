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

class Ui_ChangeSource(object):
    def setupUi(self, ChangeSource):
        ChangeSource.setObjectName(_fromUtf8("ChangeSource"))
        ChangeSource.resize(636, 529)
        ChangeSource.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.verticalLayout = QtGui.QVBoxLayout(ChangeSource)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.csLineEditLayout = QtGui.QGridLayout()
        self.csLineEditLayout.setSpacing(1)
        self.csLineEditLayout.setObjectName(_fromUtf8("csLineEditLayout"))
        self.csStationLabel = QtGui.QLabel(ChangeSource)
        self.csStationLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csStationLabel.setObjectName(_fromUtf8("csStationLabel"))
        self.csLineEditLayout.addWidget(self.csStationLabel, 3, 0, 1, 1)
        self.csPickLabel = QtGui.QLabel(ChangeSource)
        self.csPickLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csPickLabel.setObjectName(_fromUtf8("csPickLabel"))
        self.csLineEditLayout.addWidget(self.csPickLabel, 2, 0, 1, 1)
        self.csStationLineEdit = QtGui.QLineEdit(ChangeSource)
        self.csStationLineEdit.setObjectName(_fromUtf8("csStationLineEdit"))
        self.csLineEditLayout.addWidget(self.csStationLineEdit, 3, 1, 1, 1)
        self.csTagLineEdit = QtGui.QLineEdit(ChangeSource)
        self.csTagLineEdit.setObjectName(_fromUtf8("csTagLineEdit"))
        self.csLineEditLayout.addWidget(self.csTagLineEdit, 0, 1, 1, 1)
        self.csPickLineEdit = QtGui.QLineEdit(ChangeSource)
        self.csPickLineEdit.setObjectName(_fromUtf8("csPickLineEdit"))
        self.csLineEditLayout.addWidget(self.csPickLineEdit, 2, 1, 1, 1)
        self.csTagLabel = QtGui.QLabel(ChangeSource)
        self.csTagLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csTagLabel.setObjectName(_fromUtf8("csTagLabel"))
        self.csLineEditLayout.addWidget(self.csTagLabel, 0, 0, 1, 1)
        self.csArchiveLabel = QtGui.QLabel(ChangeSource)
        self.csArchiveLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csArchiveLabel.setObjectName(_fromUtf8("csArchiveLabel"))
        self.csLineEditLayout.addWidget(self.csArchiveLabel, 1, 0, 1, 1)
        self.csArchiveLineEdit = QtGui.QLineEdit(ChangeSource)
        self.csArchiveLineEdit.setObjectName(_fromUtf8("csArchiveLineEdit"))
        self.csLineEditLayout.addWidget(self.csArchiveLineEdit, 1, 1, 1, 1)
        self.csSaveSourceButton = QtGui.QPushButton(ChangeSource)
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
        self.csSaveSourceLabel = QtGui.QLabel(ChangeSource)
        self.csSaveSourceLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csSaveSourceLabel.setObjectName(_fromUtf8("csSaveSourceLabel"))
        self.verticalLayout.addWidget(self.csSaveSourceLabel)
        self.csSaveSourceList = KeyListWidget(ChangeSource)
        self.csSaveSourceList.setObjectName(_fromUtf8("csSaveSourceList"))
        self.verticalLayout.addWidget(self.csSaveSourceList)
        self.buttonBox = QtGui.QDialogButtonBox(ChangeSource)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ChangeSource)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ChangeSource.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ChangeSource.reject)
        QtCore.QMetaObject.connectSlotsByName(ChangeSource)

    def retranslateUi(self, ChangeSource):
        ChangeSource.setWindowTitle(_translate("ChangeSource", "Change Source", None))
        self.csStationLabel.setText(_translate("ChangeSource", "Station File", None))
        self.csPickLabel.setText(_translate("ChangeSource", "Pick Directory", None))
        self.csTagLabel.setText(_translate("ChangeSource", "Tag", None))
        self.csArchiveLabel.setText(_translate("ChangeSource", "Archive Directory", None))
        self.csSaveSourceButton.setText(_translate("ChangeSource", "Save Source", None))
        self.csSaveSourceLabel.setText(_translate("ChangeSource", "Saved Sources", None))

from CustomWidgets import KeyListWidget

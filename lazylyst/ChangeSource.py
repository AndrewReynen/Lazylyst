# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ChangeSource.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CsDialog(object):
    def setupUi(self, CsDialog):
        CsDialog.setObjectName("CsDialog")
        CsDialog.resize(636, 529)
        CsDialog.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.verticalLayout = QtWidgets.QVBoxLayout(CsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.csLineEditLayout = QtWidgets.QGridLayout()
        self.csLineEditLayout.setSpacing(1)
        self.csLineEditLayout.setObjectName("csLineEditLayout")
        self.csStationLabel = QtWidgets.QLabel(CsDialog)
        self.csStationLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csStationLabel.setObjectName("csStationLabel")
        self.csLineEditLayout.addWidget(self.csStationLabel, 3, 0, 1, 1)
        self.csPickLabel = QtWidgets.QLabel(CsDialog)
        self.csPickLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csPickLabel.setObjectName("csPickLabel")
        self.csLineEditLayout.addWidget(self.csPickLabel, 2, 0, 1, 1)
        self.csStationLineEdit = DblClickLineEdit(CsDialog)
        self.csStationLineEdit.setObjectName("csStationLineEdit")
        self.csLineEditLayout.addWidget(self.csStationLineEdit, 3, 1, 1, 1)
        self.csTagLineEdit = QtWidgets.QLineEdit(CsDialog)
        self.csTagLineEdit.setObjectName("csTagLineEdit")
        self.csLineEditLayout.addWidget(self.csTagLineEdit, 0, 1, 1, 1)
        self.csPickLineEdit = DblClickLineEdit(CsDialog)
        self.csPickLineEdit.setObjectName("csPickLineEdit")
        self.csLineEditLayout.addWidget(self.csPickLineEdit, 2, 1, 1, 1)
        self.csTagLabel = QtWidgets.QLabel(CsDialog)
        self.csTagLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csTagLabel.setObjectName("csTagLabel")
        self.csLineEditLayout.addWidget(self.csTagLabel, 0, 0, 1, 1)
        self.csArchiveLabel = QtWidgets.QLabel(CsDialog)
        self.csArchiveLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csArchiveLabel.setObjectName("csArchiveLabel")
        self.csLineEditLayout.addWidget(self.csArchiveLabel, 1, 0, 1, 1)
        self.csArchiveLineEdit = DblClickLineEdit(CsDialog)
        self.csArchiveLineEdit.setObjectName("csArchiveLineEdit")
        self.csLineEditLayout.addWidget(self.csArchiveLineEdit, 1, 1, 1, 1)
        self.csSaveSourceButton = QtWidgets.QPushButton(CsDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.csSaveSourceButton.sizePolicy().hasHeightForWidth())
        self.csSaveSourceButton.setSizePolicy(sizePolicy)
        self.csSaveSourceButton.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.csSaveSourceButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.csSaveSourceButton.setObjectName("csSaveSourceButton")
        self.csLineEditLayout.addWidget(self.csSaveSourceButton, 3, 2, 1, 1)
        self.verticalLayout.addLayout(self.csLineEditLayout)
        self.csSaveSourceLabel = QtWidgets.QLabel(CsDialog)
        self.csSaveSourceLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.csSaveSourceLabel.setObjectName("csSaveSourceLabel")
        self.verticalLayout.addWidget(self.csSaveSourceLabel)
        self.csSaveSourceList = KeyListWidget(CsDialog)
        self.csSaveSourceList.setObjectName("csSaveSourceList")
        self.verticalLayout.addWidget(self.csSaveSourceList)
        self.buttonBox = QtWidgets.QDialogButtonBox(CsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CsDialog)
        self.buttonBox.accepted.connect(CsDialog.accept)
        self.buttonBox.rejected.connect(CsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CsDialog)
        CsDialog.setTabOrder(self.csTagLineEdit, self.csArchiveLineEdit)
        CsDialog.setTabOrder(self.csArchiveLineEdit, self.csPickLineEdit)
        CsDialog.setTabOrder(self.csPickLineEdit, self.csStationLineEdit)
        CsDialog.setTabOrder(self.csStationLineEdit, self.csSaveSourceButton)
        CsDialog.setTabOrder(self.csSaveSourceButton, self.csSaveSourceList)
        CsDialog.setTabOrder(self.csSaveSourceList, self.buttonBox)

    def retranslateUi(self, CsDialog):
        _translate = QtCore.QCoreApplication.translate
        CsDialog.setWindowTitle(_translate("CsDialog", "Change Source"))
        self.csStationLabel.setText(_translate("CsDialog", "Station File"))
        self.csPickLabel.setText(_translate("CsDialog", "Pick Directory"))
        self.csTagLabel.setText(_translate("CsDialog", "Tag"))
        self.csArchiveLabel.setText(_translate("CsDialog", "Archive Directory"))
        self.csSaveSourceButton.setText(_translate("CsDialog", "Save Source"))
        self.csSaveSourceLabel.setText(_translate("CsDialog", "Saved Sources"))

from CustomWidgets import DblClickLineEdit, KeyListWidget

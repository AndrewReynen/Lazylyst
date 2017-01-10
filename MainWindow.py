# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainWindow.ui'
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(720, 603)
        self.mainLayout = QtGui.QWidget(MainWindow)
        self.mainLayout.setObjectName(_fromUtf8("mainLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.mainLayout)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.traceLayout = QtGui.QVBoxLayout()
        self.traceLayout.setSpacing(1)
        self.traceLayout.setObjectName(_fromUtf8("traceLayout"))
        self.timeWidget = TimeWidget(self.mainLayout)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.timeWidget.sizePolicy().hasHeightForWidth())
        self.timeWidget.setSizePolicy(sizePolicy)
        self.timeWidget.setMaximumSize(QtCore.QSize(16777215, 50))
        self.timeWidget.setBaseSize(QtCore.QSize(0, 0))
        self.timeWidget.setObjectName(_fromUtf8("timeWidget"))
        self.traceLayout.addWidget(self.timeWidget)
        self.horizontalLayout.addLayout(self.traceLayout)
        MainWindow.setCentralWidget(self.mainLayout)
        self.textOutDock = QtGui.QDockWidget(MainWindow)
        self.textOutDock.setFeatures(QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetMovable)
        self.textOutDock.setObjectName(_fromUtf8("textOutDock"))
        self.textOutLayout = QtGui.QWidget()
        self.textOutLayout.setObjectName(_fromUtf8("textOutLayout"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.textOutLayout)
        self.verticalLayout_4.setMargin(0)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.textOutBrowser = QtGui.QTextBrowser(self.textOutLayout)
        self.textOutBrowser.setObjectName(_fromUtf8("textOutBrowser"))
        self.verticalLayout_4.addWidget(self.textOutBrowser)
        self.textOutDock.setWidget(self.textOutLayout)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.textOutDock)
        self.archiveDock = QtGui.QDockWidget(MainWindow)
        self.archiveDock.setFeatures(QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetMovable)
        self.archiveDock.setObjectName(_fromUtf8("archiveDock"))
        self.archiveLayout = QtGui.QWidget()
        self.archiveLayout.setObjectName(_fromUtf8("archiveLayout"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.archiveLayout)
        self.verticalLayout_2.setMargin(0)
        self.verticalLayout_2.setSpacing(1)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.archiveWidget = ArchiveWidget(self.archiveLayout)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.archiveWidget.sizePolicy().hasHeightForWidth())
        self.archiveWidget.setSizePolicy(sizePolicy)
        self.archiveWidget.setMaximumSize(QtCore.QSize(16777215, 50))
        self.archiveWidget.setObjectName(_fromUtf8("archiveWidget"))
        self.verticalLayout_2.addWidget(self.archiveWidget)
        self.archiveList = QtGui.QListWidget(self.archiveLayout)
        self.archiveList.setObjectName(_fromUtf8("archiveList"))
        self.verticalLayout_2.addWidget(self.archiveList)
        self.archiveDock.setWidget(self.archiveLayout)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.archiveDock)
        self.mapDock = QtGui.QDockWidget(MainWindow)
        self.mapDock.setFeatures(QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetMovable)
        self.mapDock.setObjectName(_fromUtf8("mapDock"))
        self.mayLayout = QtGui.QWidget()
        self.mayLayout.setObjectName(_fromUtf8("mayLayout"))
        self.verticalLayout_6 = QtGui.QVBoxLayout(self.mayLayout)
        self.verticalLayout_6.setMargin(0)
        self.verticalLayout_6.setSpacing(1)
        self.verticalLayout_6.setObjectName(_fromUtf8("verticalLayout_6"))
        self.mapWidget = QtGui.QGraphicsView(self.mayLayout)
        self.mapWidget.setObjectName(_fromUtf8("mapWidget"))
        self.verticalLayout_6.addWidget(self.mapWidget)
        self.mapDock.setWidget(self.mayLayout)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.mapDock)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))

from CustomWidgets import ArchiveWidget, TimeWidget

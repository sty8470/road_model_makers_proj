# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'launcher.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_launcher(object):
    def setupUi(self, launcher):
        launcher.setObjectName("launcher")
        launcher.resize(380, 280)
        self.centralwidget = QtWidgets.QWidget(launcher)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 2, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 0, 1, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 1, 0, 1, 1)
        self.pushButton_Launch = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(20)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_Launch.sizePolicy().hasHeightForWidth())
        self.pushButton_Launch.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.pushButton_Launch.setFont(font)
        self.pushButton_Launch.setObjectName("pushButton_Launch")
        self.gridLayout.addWidget(self.pushButton_Launch, 1, 1, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem3, 2, 1, 1, 1)
        launcher.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(launcher)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 380, 21))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        launcher.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(launcher)
        self.statusbar.setObjectName("statusbar")
        launcher.setStatusBar(self.statusbar)
        self.action_userinfo = QtWidgets.QAction(launcher)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/user.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.action_userinfo.setIcon(icon)
        self.action_userinfo.setIconVisibleInMenu(True)
        self.action_userinfo.setObjectName("action_userinfo")
        self.action_edit_userinfo = QtWidgets.QAction(launcher)
        self.action_edit_userinfo.setObjectName("action_edit_userinfo")
        self.actionGo_to_User_Manual = QtWidgets.QAction(launcher)
        self.actionGo_to_User_Manual.setObjectName("actionGo_to_User_Manual")
        self.actionMorai = QtWidgets.QAction(launcher)
        self.actionMorai.setObjectName("actionMorai")
        self.actionLogout = QtWidgets.QAction(launcher)
        self.actionLogout.setObjectName("actionLogout")
        self.menu.addAction(self.action_userinfo)
        self.menu.addAction(self.action_edit_userinfo)
        self.menu.addAction(self.actionLogout)
        self.menuHelp.addAction(self.actionGo_to_User_Manual)
        self.menuHelp.addAction(self.actionMorai)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(launcher)
        QtCore.QMetaObject.connectSlotsByName(launcher)

    def retranslateUi(self, launcher):
        _translate = QtCore.QCoreApplication.translate
        launcher.setWindowTitle(_translate("launcher", "Launcher"))
        self.pushButton_Launch.setText(_translate("launcher", "Launch"))
        self.menu.setTitle(_translate("launcher", "User Info"))
        self.menuHelp.setTitle(_translate("launcher", "Help"))
        self.action_userinfo.setText(_translate("launcher", "View Profile"))
        self.action_edit_userinfo.setText(_translate("launcher", "Edit Profile"))
        self.actionGo_to_User_Manual.setText(_translate("launcher", "User Manual"))
        self.actionMorai.setText(_translate("launcher", "Morai"))
        self.actionLogout.setText(_translate("launcher", "Logout"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    launcher = QtWidgets.QMainWindow()
    ui = Ui_launcher()
    ui.setupUi(launcher)
    launcher.show()
    sys.exit(app.exec_())


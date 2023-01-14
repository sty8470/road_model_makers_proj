import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

opengl_path = os.path.normpath(os.path.join(current_path, '../../proj_mgeo_editor_morai_opengl'))

from lib.common.logger import Logger

import numpy as np
import json

from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from PyQt5 import QtGui
from PyQt5.QtGui import QIcon 

class FindLinkWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        

    def initUI(self):
        self.setWindowIcon(QIcon(os.path.join(opengl_path, 'map.ico')))

        self.setModal = True
        
        self.setWindowTitle('Find Link')

        self.cbLinkID = QCheckBox('', self)
        self.cbLinkID.toggle()
        self.cbMaxSpeedHigh = QCheckBox('', self)
        self.cbMaxSpeedLow = QCheckBox('', self)
        self.cbLinkType = QCheckBox('', self)

        self.txtLinkID = QLineEdit('', self)
        self.txtMaxSpeedHigh = QLineEdit('0', self)
        self.txtMaxSpeedLow = QLineEdit('0', self)
        self.txtLinkType = QLineEdit('', self)
            
        self.btnOk = QPushButton('Find', self)
        self.btnOk.clicked.connect(self.onOkButtonClicked)        
        self.btnCancel = QPushButton('Cancel', self)
        self.btnCancel.clicked.connect(self.onCancelButtonClicked) 

        self.lbLinkID = QLabel('Link ID : ')
        self.lbLinkID.setBuddy(self.txtLinkID)        
        self.lbMaxSpeedLow = QLabel('Max Speed >= ')
        self.lbMaxSpeedLow.setBuddy(self.txtMaxSpeedLow)
        self.lbMaxSpeedHigh = QLabel('Max Speed <= ')
        self.lbMaxSpeedHigh.setBuddy(self.txtMaxSpeedHigh)
        self.lbLinkType = QLabel('Link Type : ')
        self.lbLinkType.setBuddy(self.txtLinkType)
        
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.cbLinkID, 0, 0)
        gridLayout.addWidget(self.lbLinkID, 0, 1)
        gridLayout.addWidget(self.txtLinkID, 0, 2)

        gridLayout.addWidget(self.cbMaxSpeedLow, 1, 0)
        gridLayout.addWidget(self.lbMaxSpeedLow, 1, 1)
        gridLayout.addWidget(self.txtMaxSpeedLow, 1, 2)

        gridLayout.addWidget(self.cbMaxSpeedHigh, 2, 0)
        gridLayout.addWidget(self.lbMaxSpeedHigh, 2, 1)
        gridLayout.addWidget(self.txtMaxSpeedHigh, 2, 2)

        gridLayout.addWidget(self.cbLinkType, 3, 0)
        gridLayout.addWidget(self.lbLinkType, 3, 1)
        gridLayout.addWidget(self.txtLinkType, 3, 2)

        gridLayout.setContentsMargins(0, 0, 0, 8)
        
        btnLayout = QHBoxLayout()
        btnLayout.addWidget(self.btnOk)
        btnLayout.addWidget(self.btnCancel)

        rootLayout = QVBoxLayout()
        rootLayout.addLayout(gridLayout)
        rootLayout.addLayout(btnLayout)
        self.setLayout(rootLayout)
    
    def onOkButtonClicked(self):
        if(self.validate()):
            self.accept()
        else:
            return

    def onCancelButtonClicked(self):        
        self.close()

    def validate(self):
        if self.cbMaxSpeedLow.isChecked():
            try:
                int(self.txtMaxSpeedLow.text())
            except:
                QMessageBox.warning(self, "Type Error", "Please enter the integer value.")
                return False

        if self.cbMaxSpeedHigh.isChecked():
            try:
                int(self.txtMaxSpeedHigh.text())
            except:
                QMessageBox.warning(self, "Type Error", "Please enter the integer value.")
                return False

        return True

    def getParameters(self):
        link_id = ''
        max_speed_low = 0
        max_speed_high = 9999
        link_type = ''

        if self.cbLinkID.isChecked():
            link_id = self.txtLinkID.text()

        if self.cbMaxSpeedLow.isChecked():
            int_val = int(self.txtMaxSpeedLow.text())
            max_speed_low = int_val

        if self.cbMaxSpeedHigh.isChecked():            
            int_val = int(self.txtMaxSpeedHigh.text())
            max_speed_high = int_val
        
        if self.cbLinkType.isChecked():
            link_type = self.txtLinkType.text()

        search_conditions = {
            'link_id': {
                'checked': self.cbLinkID.isChecked(), 
                'val': link_id},
            'max_speed_low': max_speed_low,
            'max_speed_high': max_speed_high,
            'link_type': link_type
        }

        return search_conditions


    def showDialog(self):
        return super().exec_()


    def isFloat(self, value):
        if value != '':
            try:
                float(value)
                return True
            except:
                QMessageBox.warning(self, "Type Error", "Please check the type")
                return False


if __name__ == '__main__':
    pass
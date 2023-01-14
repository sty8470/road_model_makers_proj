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

class FindSingleCrosswalkWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon(os.path.join(opengl_path, 'map.ico')))
        self.setModal = True
        self.setWindowTitle('Find Single Crosswalk')

        self.width = 700
        self.height = 500

        self.cbSingleCrosswalkID = QCheckBox('', self)
        self.cbSingleCrosswalkID.toggle()

        self.txtSingleCrosswalkID = QLineEdit('', self)
            
        self.btnOk = QPushButton('Find', self)
        self.btnOk.clicked.connect(self.onOkButtonClicked)        
        self.btnCancel = QPushButton('Cancel', self)
        self.btnCancel.clicked.connect(self.onCancelButtonClicked) 

        self.lbSingleCrosswalkID = QLabel('Single Crosswalk ID : ')      
        self.lbSingleCrosswalkID.setBuddy(self.txtSingleCrosswalkID)
        
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.cbSingleCrosswalkID, 0, 0)
        gridLayout.addWidget(self.lbSingleCrosswalkID, 0, 1)
        gridLayout.addWidget(self.txtSingleCrosswalkID, 0, 2)

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
        return True

    def getParameters(self):
        single_crosswalk_id = ''
        
        if self.cbSingleCrosswalkID.isChecked():
            single_crosswalk_id = self.txtSingleCrosswalkID.text()

        search_conditions = {
            'single_crosswalk_id': {
              'checked': self.cbSingleCrosswalkID.isChecked(),
              'val': single_crosswalk_id
            }
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
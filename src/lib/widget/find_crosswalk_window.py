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

class FindCrosswalkWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon(os.path.join(opengl_path, 'map.ico')))
        self.setModal = True
        self.setWindowTitle('Find Crosswalk')

        self.width = 700
        self.height = 500

        self.cbCrosswalkID = QCheckBox('', self)
        self.cbCrosswalkID.toggle()

        self.txtCrosswalkID = QLineEdit('', self)
            
        self.btnOk = QPushButton('Find', self)
        self.btnOk.clicked.connect(self.onOkButtonClicked)        
        self.btnCancel = QPushButton('Cancel', self)
        self.btnCancel.clicked.connect(self.onCancelButtonClicked) 

        self.lbCrosswalkID = QLabel('Single Crosswalk ID : ')      
        self.lbCrosswalkID.setBuddy(self.txtCrosswalkID)
        
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.cbCrosswalkID, 0, 0)
        gridLayout.addWidget(self.lbCrosswalkID, 0, 1)
        gridLayout.addWidget(self.txtCrosswalkID, 0, 2)

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
        crosswalk_id = ''
        
        if self.cbCrosswalkID.isChecked():
            crosswalk_id = self.txtCrosswalkID.text()

        search_conditions = {
            'crosswalk_id': {
              'checked': self.cbCrosswalkID.isChecked(),
              'val': crosswalk_id
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
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

from PyQt5 import QtGui
from PyQt5.QtGui import QIcon 
from PyQt5.QtWidgets import *
from PyQt5.Qt import *

class FindMGeoItemWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.mgeo_item_id = ''
        self.search_conditions = None
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon(os.path.join(opengl_path, 'map.ico')))

        self.setModal = True
        
        self.setWindowTitle('Find')

        self.width = 500
        self.height = 200

        self.cbMgeoItemID = QCheckBox('', self)
        self.cbMgeoItemID.toggle()

        self.txtMGeoItemID = QLineEdit('', self)
            
        self.btnOk = QPushButton('Find', self)
        self.btnOk.clicked.connect(self.onOkButtonClicked)        
        self.btnCancel = QPushButton('Cancel', self)
        self.btnCancel.clicked.connect(self.onCancelButtonClicked) 

        self.lbMGeoItemID = QLabel('Enter ID: ')
        self.lbMGeoItemID.setBuddy(self.txtMGeoItemID)        
        
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.cbMgeoItemID, 0, 0)
        gridLayout.addWidget(self.lbMGeoItemID, 0, 1)
        gridLayout.addWidget(self.txtMGeoItemID, 0, 2)

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

        if self.cbMgeoItemID.isChecked():
            self.mgeo_item_id = self.txtMGeoItemID.text().strip()

        self.search_conditions = {
            'mgeo_item_id': {
                'checked': self.cbMgeoItemID.isChecked(),
                'val': self.mgeo_item_id
            }
        }

        return self.search_conditions

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
    def accept(self):
        if self.txtMGeoItemID.text() == '':
            QMessageBox.warning(self, "Value Error", "Please enter the ID")
        else:
            self.done(1)

if __name__ == '__main__':
    pass
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.common.logger import Logger

import numpy as np
import json
from PyQt5.QtWidgets import *
from PyQt5.Qt import *


class EditWorldOriginLatLonWindow(QDialog):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.initUI()
        

    def initUI(self):
        self.setModal = True
        
        self.setWindowTitle('Edit World Origin')

        if self.config is not None:
            self.txtWorldOriginLat = QLineEdit(self.config['world_orign_latitude'], self)
            self.txtWorldOriginLong = QLineEdit(self.config['world_orign_longitude'], self)
        else:
            self.txtWorldOriginLat = QLineEdit('0', self)
            self.txtWorldOriginLong = QLineEdit('0', self)
            
        self.btnOk = QPushButton('OK', self)
        self.btnOk.clicked.connect(self.onOkButtonClicked) 
        

        self.lbWorldOriginLat = QLabel('& World Origin Latitude (deg) : ')
        self.lbWorldOriginLat.setBuddy(self.txtWorldOriginLat)
        self.lbWorldOriginLong = QLabel('& World Origin Longtidue (deg) : ')
        self.lbWorldOriginLong.setBuddy(self.txtWorldOriginLong)
        
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.lbWorldOriginLat, 0,0)
        gridLayout.addWidget(self.txtWorldOriginLat, 0,1)
        gridLayout.addWidget(self.lbWorldOriginLong, 1,0)
        gridLayout.addWidget(self.txtWorldOriginLong, 1,1)
        gridLayout.addWidget(self.btnOk, 2,1)
        
        self.setLayout(gridLayout)
    

    def onOkButtonClicked(self):
        self.accept()


    def getParameters(self):
        world_origin_lat = float(self.txtWorldOriginLat.text()) if self.isFloat(self.txtWorldOriginLat.text()) == True else QMessageBox.warning(self, "Type Error", "Please check the type")
        world_origin_lon = float(self.txtWorldOriginLong.text()) if self.isFloat(self.txtWorldOriginLong.text()) == True else QMessageBox.warning(self, "Type Error", "Please check the type")
        return world_origin_lat, world_origin_lon
    

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
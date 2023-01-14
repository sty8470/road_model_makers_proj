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


class EditWorldProjectionWindow(QDialog):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.initUI()
        

    def initUI(self):
        self.setModal = True
        self.setWindowTitle('Edit World Projection')

        if self.config is not None:
            self.txtSpheroid = QLineEdit(self.config['spheroid'], self)
            self.txtLatitude = QLineEdit(self.config['latitude_of_orign'], self)
            self.txtCentral = QLineEdit(self.config['central_meridian'], self)
            self.txtScale = QLineEdit(self.config['scale_factor'], self)
            self.txtFalseEasting = QLineEdit(self.config['false_easting'], self)
            self.txtFalseNorthing = QLineEdit(self.config['false_northing'], self)
        else:
            self.txtSpheroid = QLineEdit('WGS84', self)
            self.txtLatitude = QLineEdit('38.0', self)
            self.txtCentral = QLineEdit('127.0', self)
            self.txtScale = QLineEdit('1.0', self)
            self.txtFalseEasting = QLineEdit('0', self)
            self.txtFalseNorthing = QLineEdit('0', self)

        self.btnOk = QPushButton('OK', self)
        self.btnOk.clicked.connect(self.onOkButtonClicked) 
        
        self.lbSpheroid = QLabel('& Spheroid : ')
        self.lbSpheroid.setBuddy(self.txtSpheroid)
        self.lbLatitude = QLabel('& Latitude of orign : ')
        self.lbLatitude.setBuddy(self.txtLatitude)
        self.lbCentral = QLabel('& Central Meridian : ')
        self.lbCentral.setBuddy(self.txtCentral)
        self.lbScale = QLabel('& Scale Factor : ')
        self.lbScale.setBuddy(self.txtScale)
        self.lbFalseEasting = QLabel('& False Easting : ')
        self.lbFalseEasting.setBuddy(self.txtFalseEasting)
        self.lbFalseNorthing = QLabel('& False Northing : ')
        self.lbFalseNorthing.setBuddy(self.txtFalseNorthing)

        gridLayout = QGridLayout()
        gridLayout.addWidget(self.lbSpheroid, 0,0)
        gridLayout.addWidget(self.txtSpheroid, 0,1)
        gridLayout.addWidget(self.lbLatitude, 1,0)
        gridLayout.addWidget(self.txtLatitude, 1,1)
        gridLayout.addWidget(self.lbCentral, 2,0)
        gridLayout.addWidget(self.txtCentral, 2,1)
        gridLayout.addWidget(self.lbScale, 3,0)
        gridLayout.addWidget(self.txtScale, 3,1)
        gridLayout.addWidget(self.lbFalseEasting, 4,0)
        gridLayout.addWidget(self.txtFalseEasting, 4,1)
        gridLayout.addWidget(self.lbFalseNorthing, 5,0)
        gridLayout.addWidget(self.txtFalseNorthing, 5,1)

        gridLayout.addWidget(self.btnOk, 6,1)

        self.setLayout(gridLayout)
    

    def onOkButtonClicked(self):
        self.accept()


    def getParameters(self):
        spheroid = self.txtSpheroid.text()
        
        latitude_of_origin = float(self.txtLatitude.text()) if self.isFloat(self.txtLatitude.text()) == True else QMessageBox.warning(self, "Type Error", "Please check the type")
        central_meridian = float(self.txtCentral.text()) if self.isFloat(self.txtCentral.text()) == True else QMessageBox.warning(self, "Type Error", "Please check the type")
        scale_factor = float(self.txtScale.text()) if self.isFloat(self.txtScale.text()) == True else QMessageBox.warning(self, "Type Error", "Please check the type")
        false_easting = float(self.txtFalseEasting.text()) if self.isFloat(self.txtFalseEasting.text()) == True else QMessageBox.warning(self, "Type Error", "Please check the type")
        false_northing = float(self.txtFalseNorthing.text()) if self.isFloat(self.txtFalseNorthing.text()) == True else QMessageBox.warning(self, "Type Error", "Please check the type")
        
        return spheroid, latitude_of_origin, central_meridian, scale_factor, false_easting, false_northing
   
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
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


class FindNodeWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        

    def initUI(self):
        self.setWindowIcon(QIcon(os.path.join(opengl_path, 'map.ico')))

        self.setModal = True
        
        self.setWindowTitle('Find Node')

        self.width = 500
        self.height = 200

        self.cbNodeID = QCheckBox('', self)
        self.cbNodeID.toggle()
        self.cbOnStopLine = QCheckBox('', self)

        self.txtNodeID = QLineEdit('', self)
        self.cbValOnStopLine = QCheckBox('', self)
            
        self.btnOk = QPushButton('Find', self)
        self.btnOk.clicked.connect(self.onOkButtonClicked)        
        self.btnCancel = QPushButton('Cancel', self)
        self.btnCancel.clicked.connect(self.onCancelButtonClicked) 

        self.lbNodeID = QLabel('Node ID : ')
        self.lbNodeID.setBuddy(self.txtNodeID)        
        self.lbOnStopLine = QLabel('On Stop Line :')
        self.lbOnStopLine.setBuddy(self.cbValOnStopLine)
        
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.cbNodeID, 0, 0)
        gridLayout.addWidget(self.lbNodeID, 0, 1)
        gridLayout.addWidget(self.txtNodeID, 0, 2)

        gridLayout.addWidget(self.cbOnStopLine, 1, 0)
        gridLayout.addWidget(self.lbOnStopLine, 1, 1)
        gridLayout.addWidget(self.cbValOnStopLine, 1, 2)

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
        node_id = ''
        on_stop_line = False

        if self.cbNodeID.isChecked():
            node_id = self.txtNodeID.text()

        if self.cbOnStopLine.isChecked():
            on_stop_line = self.cbValOnStopLine.isChecked()

        search_conditions = {
            'node_id': {
                'checked': self.cbNodeID.isChecked(),
                'val': node_id
            },
            'on_stop_line':{
                'checked': self.cbOnStopLine.isChecked(),
                'val': on_stop_line
            },
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
            
    # def accept(self):
    #     if self.txtNodeID.text() == '':
    #         QMessageBox.warning(self, "Value Error", "Please enter the ID")
    #     else:
    #         self.done(1)


if __name__ == '__main__':
    pass
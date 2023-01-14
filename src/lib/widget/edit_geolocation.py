import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import json
from lib.common.logger import Logger

from PyQt5.QtCore    import *
from PyQt5.QtWidgets import *


class EditGeolocation(QDialog):
    def __init__(self, old_origin):
        super().__init__()
        self.isRetainGlobalPosition = True
        self.coordText = ''
        self.old_origin = old_origin
        self.initUI()
        
    

    def initUI(self):
        # ui 구성
        self.setGeometry(500, 200, 200, 200)
        
        old_origin_str = '{:.9f}, {:.9f}, {:.9f}'.format(self.old_origin[0], self.old_origin[1], self.old_origin[2])

        self.rbtn_global = QRadioButton('Retain global position \n(local position will change accordingly)', self)
        self.rbtn_no_global = QRadioButton('Do NOT retain global position \n(position of local origin w.r.t. \n global coordinate system will change only)', self)
        lb_location = QLabel('Location :')
        self.txt_location = QLineEdit(old_origin_str)
        btn_OK = QPushButton('OK')
        
        textEditLayout = QHBoxLayout()
        textEditLayout.addWidget(lb_location)
        textEditLayout.addWidget(self.txt_location)

        widgetLayout = QVBoxLayout()
        widgetLayout.addWidget(self.rbtn_global)
        widgetLayout.addWidget(self.rbtn_no_global)
        widgetLayout.addSpacing(30)
        widgetLayout.addLayout(textEditLayout)
        widgetLayout.addSpacing(10)
        widgetLayout.addWidget(btn_OK)
        self.setLayout(widgetLayout)


        self.rbtn_global.setChecked(True)

        self.setWindowTitle('Edit Geolocation')

        # event
        self.rbtn_global.clicked.connect(self.radioButtonClicked)
        self.rbtn_no_global.clicked.connect(self.radioButtonClicked)
        btn_OK.clicked.connect(self.accept)

    def radioButtonClicked(self):
        if self.rbtn_global.isChecked():
            self.isRetainGlobalPosition = True
        else:
            self.isRetainGlobalPosition = False
    

    def accept(self):
        self.coordText = self.txt_location.text()
        if self.coordText == '':
            QMessageBox.warning(self, "Validation Error", "Please enter the location.")
            return
        
        self.done(1)
    
    def close(self):
        self.done(0)
    
    def showDialog(self):
        return super().exec_()



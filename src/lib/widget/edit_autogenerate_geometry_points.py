import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

# from typing import DefaultDict
# from numpy.lib.twodim_base import diag
from PyQt5.QtWidgets import *
from PyQt5.Qt import *


class EditAutogenerateGeometryPoints(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.type = 'paramPoly3'
        self.value= ''
    
    def initUI(self):
        # self.setGeometry(500, 200, 200, 200)
        self.setWindowTitle('Auto-Generate Geometry Points')

        self.rbtn_poly3 = QRadioButton('poly3', self)
        self.rbtn_parampoly3 = QRadioButton('paramPoly3', self)
        self.rbtn_parampoly3.setChecked(True)

        lbValue = QLabel('Value :')
        self.txtValue = QLineEdit()
        btn_OK = QPushButton('OK')

        textEditLayout = QHBoxLayout()
        textEditLayout.addWidget(lbValue)
        textEditLayout.addWidget(self.txtValue)

        widgetLayout = QVBoxLayout()
        widgetLayout.addWidget(self.rbtn_poly3)
        widgetLayout.addWidget(self.rbtn_parampoly3)
        widgetLayout.addSpacing(10)
        widgetLayout.addLayout(textEditLayout)
        widgetLayout.addSpacing(10)
        widgetLayout.addWidget(btn_OK)

        self.setLayout(widgetLayout)

        # event
        self.rbtn_poly3.clicked.connect(self.radioButtonClicked)
        self.rbtn_parampoly3.clicked.connect(self.radioButtonClicked)
        btn_OK.clicked.connect(self.accept)

    def radioButtonClicked(self):
        if self.rbtn_poly3.isChecked():
            self.type = 'poly3'
            self.txtValue.setDisabled(False)
        else:
            self.type = 'paramPoly3'
            self.txtValue.setDisabled(True)
    
    def accept(self):
        self.value = self.txtValue.text()
        self.done(1)
    
    def close(self):
        self.done(0)
    
    def showDialog(self):
        return super().exec_()
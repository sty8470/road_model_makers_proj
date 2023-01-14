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


class EditAddMaxSpeedLink(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.type = None
        self.value= None
    
    def initUI(self):
        self.setWindowTitle('Add Max Speed on Links')

        self.all_links = QRadioButton('add max speed to all links', self)
        self.selected_links = QRadioButton('add max speed to selected links', self)
        self.all_links.setChecked(True)

        lbValue = QLabel('Value :')
        self.txtValue = QLineEdit()
        btn_OK = QPushButton('OK')

        textEditLayout = QHBoxLayout()
        textEditLayout.addWidget(lbValue)
        textEditLayout.addWidget(self.txtValue)

        widgetLayout = QVBoxLayout()
        widgetLayout.addWidget(self.all_links)
        widgetLayout.addWidget(self.selected_links)
        widgetLayout.addSpacing(10)
        widgetLayout.addLayout(textEditLayout)
        widgetLayout.addSpacing(10)
        widgetLayout.addWidget(btn_OK)

        self.setLayout(widgetLayout)

        # event
        self.all_links.clicked.connect(self.radioButtonClicked)
        self.selected_links.clicked.connect(self.radioButtonClicked)
        btn_OK.clicked.connect(self.accept)

    def radioButtonClicked(self):
        if self.all_links.isChecked():
            self.txtValue.setDisabled(False)
        else:
            self.txtValue.setDisabled(False)
    
    def accept(self):
        self.value = self.txtValue.text()
        if self.all_links.isChecked():
            self.type = 'all_links'
        else:
            self.type = 'selected_links'
        self.done(1)
    
    def close(self):
        self.done(0)
    
    def showDialog(self):
        return super().exec_()
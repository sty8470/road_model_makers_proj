# Waypoint Text Files

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.common.logger import Logger
from lib.mgeo.class_defs.mgeo_item import MGeoItem

import numpy as np
import json
import shutil

from PyQt5.QtWidgets import *
from PyQt5.Qt import *

class SelectExportPathCSV(QDialog):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.check1 = False
        self.check2 = False

    def initUI(self):

        widgetLayout = QGridLayout()
        
        groupbox = QGroupBox('Output format') # 바꾸기
        vbox = QVBoxLayout()

        self.btn_check1 = QRadioButton('List<Link>', self)
        self.btn_check1.setChecked(True)
        self.btn_check2 = QRadioButton('List<Point> (ENU) (m)', self)
        self.btn_check3 = QRadioButton('List<Point> (LL) (deg)', self)

        vbox.addWidget(self.btn_check1)
        vbox.addWidget(self.btn_check2)
        vbox.addWidget(self.btn_check3)
        groupbox.setLayout(vbox)
        
        widgetLayout.addWidget(groupbox, 0, 0)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        widgetLayout.addWidget(self.buttonbox, 2, 0)
        
        self.setLayout(widgetLayout)
        self.setWindowTitle('CSV Output Format')  # 바꾸기

        # self.show()

    def showDialog(self):
        return super().exec_()
        
    def accept(self):
        self.checkBoxStateChanged()
        self.done(1)

    def close(self):
        self.checkBoxStateChanged()
        self.done(0)

    def checkBoxStateChanged(self):
        self.check1 = self.btn_check1.isChecked()
        self.check2 = self.btn_check2.isChecked()
        self.check3 = self.btn_check3.isChecked()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SelectExportPathCSV()
    ex.showDialog()
    sys.exit(app.exec_())
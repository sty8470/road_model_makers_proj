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

class SelectWaypointFileType(QDialog):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        widgetLayout = QGridLayout()
        
        groupbox = QGroupBox('Waypoint File Type')
        vbox = QVBoxLayout()

        self.txt_file = QRadioButton('.txt', self)
        self.txt_file.setChecked(True)
        self.shp_file = QRadioButton('.shp', self)

        vbox.addWidget(self.txt_file)
        vbox.addWidget(self.shp_file)
        groupbox.setLayout(vbox)
        
        widgetLayout.addWidget(groupbox, 0, 0)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        widgetLayout.addWidget(self.buttonbox, 2, 0)
        
        self.setLayout(widgetLayout)
        self.setWindowTitle('Select Waypoint File Type')   

        # self.show()

    def showDialog(self):
        return super().exec_()
        
    def accept(self):
        self.done(1)

    def close(self):
        self.done(0)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SelectWaypointFileType()
    ex.showDialog()
    sys.exit(app.exec_())
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

class SelectLineTypeWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        widgetLayout = QGridLayout()
        
        groupbox = QGroupBox('Select Line Type')
        vbox = QVBoxLayout()

        self.link = QRadioButton(MGeoItem.LINK.name, self)
        self.link.setChecked(True)
        self.lane = QRadioButton(MGeoItem.LANE_BOUNDARY.name, self)

        vbox.addWidget(self.link)
        vbox.addWidget(self.lane)
        groupbox.setLayout(vbox)
        
        widgetLayout.addWidget(groupbox, 0, 0)
        
        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        widgetLayout.addWidget(self.buttonbox, 2, 0)
        
        self.setLayout(widgetLayout)
        self.setWindowTitle('Select Line Type')   

        # self.show()

    def showDialog(self):
        return super().exec_()
        
    def accept(self):
        self.done(1)

    def close(self):
        self.done(0)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SelectLineTypeWindow()
    ex.showDialog()
    sys.exit(app.exec_())
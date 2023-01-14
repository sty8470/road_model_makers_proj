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

class SelectNodeTypeWindow(QDialog):

    def __init__(self, threshold=True):
        super().__init__()
        self.threshold = threshold
        self.initUI()

    def initUI(self):

        widgetLayout = QGridLayout()
        
        groupbox = QGroupBox('Select Node Type')
        vbox = QVBoxLayout()

        self.node = QRadioButton(MGeoItem.NODE.name, self)
        self.node.setChecked(True)
        self.lane_node = QRadioButton(MGeoItem.LANE_NODE.name, self)

        vbox.addWidget(self.node)
        vbox.addWidget(self.lane_node)
        groupbox.setLayout(vbox)
        
        widgetLayout.addWidget(groupbox, 0, 0)
        
        if self.threshold:
            inputbox = QGroupBox('Input distance threshold value')
            hbox = QHBoxLayout()
            label = QLabel(self)
            label.setText('Value')
            self.dist_threshold = QLineEdit(self)
            validator = QRegExpValidator(QRegExp(r'[0-9].+'))
            self.dist_threshold.setValidator(validator)
            self.dist_threshold.setText('0.1')

            hbox.addWidget(label)
            hbox.addWidget(self.dist_threshold)
            inputbox.setLayout(hbox)
            widgetLayout.addWidget(inputbox, 1, 0)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        widgetLayout.addWidget(self.buttonbox, 2, 0)
        
        self.setLayout(widgetLayout)
        self.setWindowTitle('Select Node Type')   

        # self.show()

    def showDialog(self):
        return super().exec_()
        
    def accept(self):
        self.done(1)

    def close(self):
        self.done(0)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SelectNodeTypeWindow(threshold = False)
    ex.showDialog()
    sys.exit(app.exec_())
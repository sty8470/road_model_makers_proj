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

class SelectFillPointsWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.initUI()


    def initUI(self):
        widgetLayout = QGridLayout()
        groupbox = QGroupBox('Choose the point creation option')
        vbox = QVBoxLayout()
        # 기존 데이터 보존
        # 기존 데이터 삭제
        # 간격 입력
        self.erasing_points = QRadioButton('Remove existing points', self)
        self.erasing_points.setChecked(True)
        self.no_erasing_points = QRadioButton('Keep existing points', self)

        vbox.addWidget(self.erasing_points)
        vbox.addWidget(self.no_erasing_points)
        groupbox.setLayout(vbox)
        widgetLayout.addWidget(groupbox, 0, 0)

        inputbox = QGroupBox('Enter step length')
        hbox = QHBoxLayout()
        label = QLabel(self)
        label.setText('Value')
        self.step_length = QLineEdit(self)
        validator = QRegExpValidator(QRegExp(r'[0-9].+'))
        self.step_length.setValidator(validator)
        self.step_length.setText('0.5')

        hbox.addWidget(label)
        hbox.addWidget(self.step_length)
        inputbox.setLayout(hbox)
        widgetLayout.addWidget(inputbox, 1, 0)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        widgetLayout.addWidget(self.buttonbox, 2, 0)
        
        self.setLayout(widgetLayout)
        self.setWindowTitle('Select the point creation condition')   

        # self.show()

    def showDialog(self):
        return super().exec_()
        
    def accept(self):
        self.done(1)

    def close(self):
        self.done(0)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SelectFillPointsWindow()
    ex.showDialog()
    sys.exit(app.exec_())
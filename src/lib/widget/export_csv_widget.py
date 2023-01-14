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

class ExportCSVWidget(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.isLink = True
        self.isLaneMarking = True
        self.isMergeAlldata = False

    
    def initUI(self):
        # UI 구성
        self.setGeometry(500, 200, 300, 300)

        self.gb_select_primitives = QGroupBox('Select Primitives', self)

        self.cb_link = QCheckBox('Link', self)
        self.cb_link.setChecked(True)
        self.cb_lane_marking = QCheckBox('Lane Marking', self)
        self.cb_lane_marking.setChecked(True)

        check_group_layout = QVBoxLayout()
        check_group_layout.addWidget(self.cb_link)
        check_group_layout.addWidget(self.cb_lane_marking)

        self.gb_select_primitives.setLayout(check_group_layout)

        self.gb_other_option = QGroupBox('Other Options', self)
        self.cb_merge_all_data = QCheckBox('Merge all data into single file')

        other_group_layout = QVBoxLayout()
        other_group_layout.addWidget(self.cb_merge_all_data)

        self.gb_other_option.setLayout(other_group_layout)

        button = QPushButton('OK', self)
        button.move(120, 270)

        self.setWindowTitle('Export CSV File Option')
        
        widgetLayout = QVBoxLayout()
        widgetLayout.addWidget(self.gb_select_primitives)
        widgetLayout.addWidget(self.gb_other_option)
        
        widgetLayout.addWidget(button)

        self.setLayout(widgetLayout)

        # event 연결
        self.cb_link.stateChanged.connect(self.checkBoxStateChanged)
        self.cb_lane_marking.stateChanged.connect(self.checkBoxStateChanged)
        self.cb_merge_all_data.stateChanged.connect(self.checkBoxStateChanged)
        button.clicked.connect(self.accept)
        
    def checkBoxStateChanged(self):
        self.isLink = self.cb_link.isChecked()
        self.isLaneMarking = self.cb_lane_marking.isChecked()
        self.isMergeAlldata = self.cb_merge_all_data.isChecked()

    def accept(self):
        self.done(1)
    
    def close(self):
        self.done(0)
    
    def showDialog(self):
        return super().exec_()


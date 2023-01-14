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
from lib.mgeo.class_defs import *

class EditSetMaxSpeedLink(QDialog):
    def __init__(self, mgeo_map_dict):
        super().__init__()
        self.type = None
        self.value= None
        self.mgeo_map_dict = mgeo_map_dict
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Set Max Speed')

        self.all_links = QRadioButton('set max speed to all links', self)
        self.selected_links = QRadioButton('set max speed to empty links', self)
        # combine setChecked with initial type
        self.all_links.setChecked(True)
        self.type = 'all_links'

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
            self.type = 'all_links'
        elif self.selected_links.isChecked():
            self.type = 'empty_links'
        else:
            pass
            # add error code
    
    def accept(self):
        """Set_max_speed_link"""
        self.value = self.txtValue.text()
        self.done(1)
    
    def close(self):
        self.done(0)
    
    def showDialog(self):
        return super().exec_()
    
    def set_max_speed_to_all_links(self):
        # Default value
        mgeo_key = list(self.mgeo_map_dict.keys())[0]
        mgeo_planner_map = self.mgeo_map_dict[mgeo_key]
        
        for link_id in mgeo_planner_map.link_set.lines:
            mgeo_planner_map.link_set.lines[link_id].max_speed = self.value
    
    def set_max_speed_to_empty_links(self):
        mgeo_key = list(self.mgeo_map_dict.keys())[0]
        mgeo_planner_map = self.mgeo_map_dict[mgeo_key]
        
        for link_id in mgeo_planner_map.link_set.lines:
            if mgeo_planner_map.link_set.lines[link_id].max_speed == '' or mgeo_planner_map.link_set.lines[link_id].max_speed == None or mgeo_planner_map.link_set.lines[link_id].max_speed == 0 or mgeo_planner_map.link_set.lines[link_id].max_speed == '0':
                mgeo_planner_map.link_set.lines[link_id].max_speed = self.value
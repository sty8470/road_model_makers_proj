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

import iso3166

class EditChangeRegionLocalization(QDialog):
    def __init__(self, mgeo_planner_map = None):
        super().__init__()
        
        self.mgeo_planner_map = mgeo_planner_map
        self.traffic_dir = ''
        self.country = ''
        self.road_type = ''
        self.road_type_def = ''

        self.initUI()
    
    def initUI(self):
        # UI 구성
        self.setGeometry(800, 200, 300, 300)

        gb_traffic_dir = QGroupBox('Traffic Dir', self)
        # gb_traffic_dir.move(10, 20)
        gb_traffic_dir.resize(280, 70)

        self.rbtn_Empty = QRadioButton('(Empty)', self)
        self.rbtn_RHT = QRadioButton('RHT', self)
        # self.rbtn_RHT.move(20, 40)
        self.rbtn_LHT = QRadioButton('LHT', self)
        # self.rbtn_LHT.move(20, 60)

        self.rbtn_Empty.setChecked(True)

        rbt_group_layout = QVBoxLayout()
        rbt_group_layout.addWidget(self.rbtn_Empty)
        rbt_group_layout.addWidget(self.rbtn_RHT)
        rbt_group_layout.addWidget(self.rbtn_LHT)
        
        
        gb_traffic_dir.setLayout(rbt_group_layout)
        
        gb_country = QGroupBox('Country', self)
        # self.gb_country.move(10, 90)
        gb_country.resize(280, 60)
       
        self.cb_country_name = QComboBox(self)
        # self.cb_country_name.move(20, 110)
        self.cb_country_name.resize(240, 20)
        country_group_layout = QVBoxLayout()
        country_group_layout.addWidget(self.cb_country_name)
        gb_country.setLayout(country_group_layout)
        
        self.cb_country_name.addItem('(Empty)')
        for c in iso3166.countries:
            self.cb_country_name.addItem(c.name)
        
        gb_road_type = QGroupBox('Road Type', self)
        # self.gb_road_type.move(10, 150)
        gb_road_type.resize(280, 60)

        self.cb_road_type = QComboBox(self)
        self.cb_road_type.addItem('(Empty)')
        self.cb_road_type.addItem('town')

        roadtype_group_layout = QVBoxLayout()
        roadtype_group_layout.addWidget(self.cb_road_type)
        gb_road_type.setLayout(roadtype_group_layout)

        # self.cb_road_type.move(20, 170)

        gb_road_type_def = QGroupBox('Road Type Definition', self)
        # self.gb_road_type_def.move(10, 210)
        gb_road_type_def.resize(280, 60)

        self.cb_road_type_def = QComboBox(self)
        self.cb_road_type_def.addItem('(Empty)')
        self.cb_road_type_def.addItem('OpenDRIVE')
        self.cb_road_type_def.move(20, 230)

        roadtypedef_group_layout = QVBoxLayout()
        roadtypedef_group_layout.addWidget(self.cb_road_type_def)
        gb_road_type_def.setLayout(roadtypedef_group_layout)

        button = QPushButton('OK', self)
        button.move(120, 270)

        self.setWindowTitle('Change Region Localization')
        
        widgetLayout = QVBoxLayout()
        widgetLayout.addWidget(gb_traffic_dir)
        widgetLayout.addWidget(gb_country)
        widgetLayout.addWidget(gb_road_type)
        widgetLayout.addWidget(gb_road_type_def)
        widgetLayout.addWidget(button)

        self.setLayout(widgetLayout)

        # event 연결
        self.rbtn_Empty.clicked.connect(self.radioButtonClicked)
        self.rbtn_RHT.clicked.connect(self.radioButtonClicked)
        self.rbtn_LHT.clicked.connect(self.radioButtonClicked)
        self.cb_country_name.currentIndexChanged.connect(self.country_cb_IndexChanged)
        self.cb_road_type.currentIndexChanged.connect(self.road_type_IndexChanged)
        self.cb_road_type_def.currentIndexChanged.connect(self.road_type_def_IndexChanged)
        button.clicked.connect(self.accept)

        self.set_data()
        

    def set_data(self):
        if self.mgeo_planner_map.traffic_dir is not None:
            if self.mgeo_planner_map.traffic_dir == 'RHT':
                self.rbtn_RHT.setChecked(True)
                self.traffic_dir = 'RHT'
            elif self.mgeo_planner_map.traffic_dir == 'LHT':
                self.rbtn_LHT.setChecked(True)
                self.traffic_dir = 'LHT'
            else: # Emtpy
                self.rbtn_Empty.setChecked(True)
                self.traffic_dir = ''
        
        if self.mgeo_planner_map.country is not None:
            country = self.mgeo_planner_map.country
            if country == '':
                self.cb_country_name.setCurrentIndex(0)
            else:
                idx = self.cb_country_name.findText(country)
                if idx > 0:
                    self.cb_country_name.setCurrentText(country)
        
        if self.mgeo_planner_map.road_type is not None:
            if self.mgeo_planner_map.road_type == 'town':
                self.cb_road_type.setCurrentIndex(1)
            else:
                self.cb_road_type.setCurrentIndex(0)
        
        if self.mgeo_planner_map.road_type_def is not None:
            if self.mgeo_planner_map.road_type_def == 'OpenDRIVE':
                self.cb_road_type_def.setCurrentIndex(1)
            else:
                self.cb_road_type_def.setCurrentIndex(0)
       

    def radioButtonClicked(self):
        if self.rbtn_RHT.isChecked():
            self.traffic_dir = "RHT"
            
        elif self.rbtn_LHT.isChecked():
            self.traffic_dir = "LHT"

        else:
            self.traffic_dir = ""
            
    
    def country_cb_IndexChanged(self):
        if self.cb_country_name.currentIndex() == 0:
            self.country = ''
        else:
            self.country = str(self.cb_country_name.currentText())
        
    
    def road_type_IndexChanged(self):
        if self.cb_road_type.currentIndex() == 0:
            self.road_type = ''
        else:
            self.road_type = str(self.cb_road_type.currentText())
    

    def road_type_def_IndexChanged(self):
        if self.cb_road_type_def.currentIndex() == 0:
            self.road_type_def = ''
        else:
            self.road_type_def = str(self.cb_road_type_def.currentText())


    def showDialog(self):
        return super().exec_()


    def accept(self):
        # NOTE: 로드한 MGeo 데이터가 Emtpy 일 때 
        # if self.traffic_dir == '':
        #     self.traffic_dir = 'RHT'

        self.done(1)


    def close(self):
        self.done(0)
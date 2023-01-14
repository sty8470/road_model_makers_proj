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

class EditExtractBoundary(QDialog):
    """
    지도 데이터 Import 시 자를 영역을 설정할 수 있는 창 생성
    """
    def __init__(self):
        super().__init__()
        self.extract_region_config = None
        self.config_file_path = ''
        
    def initUI(self):
        # 이전 설정이 없으면 기본 설정을 만든다.
        if not os.path.exists(self.config_file_path):
            self.extract_region_config = {}
            self.extract_region_config['extract_type'] = 'all'
            self.extract_region_config['longitude_min'] = '0'
            self.extract_region_config['longitude_max'] = '0'
            self.extract_region_config['latitude_min'] = '0'
            self.extract_region_config['latitude_max'] = '0'
        else:
            with open(self.config_file_path, 'r') as f:
                self.extract_region_config = json.load(f)
        
            if self.extract_region_config is None:
                raise BaseException('Failed to initialize. Cannot find config_file_io.json')

        # UI 구성
        self.rbtn_extract_all = QRadioButton('All data', self)
        self.rbtn_extract_region = QRadioButton('Extract Boundary', self)
        self.rbtn_extract_all.clicked.connect(self.radio_button_clicked)
        self.rbtn_extract_region.clicked.connect(self.radio_button_clicked)

        radio_layout = QVBoxLayout()
        radio_layout.addWidget(self.rbtn_extract_all)
        radio_layout.addWidget(self.rbtn_extract_region)

        self.longitude_spacer = QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.label_longitude = QLabel('Longitude', self)
        self.label_longitude_min = QLabel('min', self)
        self.edit_longitude_min = QLineEdit('', self)
        self.longitude_spacer2 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.label_longitude_max = QLabel('max', self)
        self.edit_longitude_max = QLineEdit('', self)
        longitude_layout = QHBoxLayout()
        longitude_layout.addItem(self.longitude_spacer)
        longitude_layout.addWidget(self.label_longitude)
        longitude_layout.addWidget(self.label_longitude_min)
        longitude_layout.addWidget(self.edit_longitude_min)
        longitude_layout.addItem(self.longitude_spacer2)
        longitude_layout.addWidget(self.label_longitude_max)
        longitude_layout.addWidget(self.edit_longitude_max)

        self.latitude_spacer = QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.label_latitude = QLabel('Latitude   ', self)
        self.label_latitude_min = QLabel('min', self)
        self.edit_latitude_min = QLineEdit('', self)
        self.latitude_spacer2 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.label_latitude_max = QLabel('max', self)
        self.edit_latitude_max = QLineEdit('', self)
        latitude_layout = QHBoxLayout()
        latitude_layout.addItem(self.latitude_spacer)
        latitude_layout.addWidget(self.label_latitude)
        latitude_layout.addWidget(self.label_latitude_min)
        latitude_layout.addWidget(self.edit_latitude_min)
        latitude_layout.addItem(self.latitude_spacer2)
        latitude_layout.addWidget(self.label_latitude_max)
        latitude_layout.addWidget(self.edit_latitude_max)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        widgetLayout = QVBoxLayout()
        widgetLayout.addLayout(radio_layout)
        widgetLayout.addLayout(longitude_layout)
        widgetLayout.addLayout(latitude_layout)
        widgetLayout.addWidget(self.buttonbox)

        self.setLayout(widgetLayout)
        self.setWindowTitle('Extract boundary setting')

        # 이전 설정 반영
        if self.extract_region_config['extract_type'] == 'all':
            self.rbtn_extract_all.setChecked(True)
        elif self.extract_region_config['extract_type'] == 'region':
            self.rbtn_extract_region.setChecked(True)
        self.radio_button_clicked()

        self.edit_longitude_min.setText(self.extract_region_config['longitude_min'])
        self.edit_longitude_max.setText(self.extract_region_config['longitude_max'])
        self.edit_latitude_min.setText(self.extract_region_config['latitude_min'])
        self.edit_latitude_max.setText(self.extract_region_config['latitude_max'])


    def radio_button_clicked(self):
        extract_region = True
        if self.rbtn_extract_all.isChecked():
            extract_region = False

        self.edit_longitude_min.setEnabled(extract_region)
        self.edit_longitude_max.setEnabled(extract_region)
        self.edit_latitude_min.setEnabled(extract_region)
        self.edit_latitude_max.setEnabled(extract_region)
            

    def update_config(self):
        self.extract_region_config = {}

        self.extract_region_config['extract_type'] = 'all' if self.rbtn_extract_all.isChecked() else 'region'
        self.extract_region_config['longitude_min'] = self.edit_longitude_min.text()
        self.extract_region_config['longitude_max'] = self.edit_longitude_max.text()
        self.extract_region_config['latitude_min'] = self.edit_latitude_min.text()
        self.extract_region_config['latitude_max'] = self.edit_latitude_max.text()     


    def set_config(self, config):
        self.extract_region_config = config


    def get_config(self):
        return self.extract_region_config


    def showDialog(self):
        return super().exec_()


    def accept(self):
        self.update_config()
        with open(self.config_file_path, 'w') as output:            
            json.dump(self.extract_region_config, output, indent=2)
                    
        self.done(1)


    def close(self):
        self.done(0)
    
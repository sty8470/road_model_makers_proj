from ctypes import alignment
import os
import sys

from xodr_lane_section import OdrLaneSection
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.common.logger import Logger
from lib.mgeo.class_defs import *

import numpy as np
import json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QRegExp
from PyQt5.Qt import *
class ODREditor(QDialog):
    """
    OpenDRIVE 생성 시 옵션을 선Q택할 수 있는 창 생성

    가장 바깥 차선에 적용할 extra width: float
    Sidewalk 생성 여부 On/Off
    Signal 포함

    """
    def __init__(self):
        super().__init__()
        self.mgeo_planner_map = MGeo(NodeSet(), LineSet(), JunctionSet(), SignalSet(), SignalSet())
        self.odr_param = None
        self.config_file_path = None
        self.smoothing_road = False
        self.signal_state = None
        self.matching_road = None
        self.disable_lane_link = False
        self.superelevation = False
        self.add_virtual_shoulder = False
        self.version_type_figure = None
        self.virtual_shoulder_input = QLineEdit(self)
        float_regexp = r"(([+]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"
        regexp = "(float)?( +float)* *".replace("float", float_regexp)
        validator = QRegExpValidator(QRegExp(regexp))
        self.virtual_shoulder_input.setValidator(validator)
        self.virtual_shoulder_value = ''
        self.odr_lane_obj = OdrLaneSection()

    def getOpenDRIVEConversionConfig(self):
        # config 파일을 자동으로 load 할 때, 호출되는 변수들을 채워준다. 
        # 예: converter.MGeoToOdrDataConverter.get_instance().get_config('virtual_shoulder')
        config = {}
        
        config['smoothing_road'] = self.checkStateToBoolean(
            self.odr_param['SMOOTHING']['ROAD'])
        
        config['include_signal'] = self.checkStateToBoolean(
            self.odr_param['SIGNAL']['STATE'])

        config['fix_signal_road_id'] = self.checkStateToBoolean(
            self.odr_param['MATCHING_ROAD']['STATE'])

        config['disable_lane_link'] = self.checkStateToBoolean(
            self.odr_param['DISABLE_LANE_LINK']['STATE'])
        
        config['virtual_shoulder'] = self.checkStateToBoolean(
            self.odr_param['VIRTUAL']['SHOULDER'])

        config['superelevation'] = self.checkStateToBoolean(
            self.odr_param['SUPERELEVATION']['STATE'])
        
        config['version_type'] = self.odr_param['VERSION']['TYPE']
        
        config['shoulder_width'] = self.odr_param['SHOULDER']['WIDTH']
        
        config['width_threshold'] = self.odr_param['WIDTH']['THRESHOLD']
        
        config['s_offset_detection_threshold'] = self.odr_param['DETECTION']['THRESHOLD']
        
        config['reference_line_fitting'] = self.odr_param['REFERENCE']['LINE']['FITTING']

        return config

    def checkStateToBoolean(self, value):
        if value == 0:
            return False
        elif value == 2:
            return True
        else:
            raise BaseException('ERROR @ widgetCheckStateToBoolean: unexpected check state value: {}'.format(value))        

    def initUI(self):
        """
        □ Signal
        □ Search for Matching Road (When Signals Included)
        □ Search for Matching Road (When Signals Included)
        [Load Default Values(Reset)] << 버튼
        전체 디폴트값이 있고, 사용자가 수정한 값은 OK 누를때 별도 config 파일에 저장
        """
        self.signal_state = self.odr_param['SIGNAL']['STATE']
        self.matching_road = self.odr_param['MATCHING_ROAD']['STATE']
        self.disable_lane_link = self.odr_param['DISABLE_LANE_LINK']['STATE']
        self.superelevation = self.odr_param['SUPERELEVATION']['STATE']
        self.smoothing_road = self.odr_param['SMOOTHING']['ROAD']
        self.v_widgetLayout = QVBoxLayout()
        self.version_h_widgetLayout = QHBoxLayout()
        self.ref_line_fit_h_widgetLayout = QHBoxLayout()
        widgetLayout = QGridLayout()
        
        self.version_title = QLabel('OpenDRIVE Version', self)
        self.version_type = QComboBox(self)
        self.version_type.addItem('1.4')
        self.version_type.addItem('1.5')
        self.version_type.addItem('1.6')
         
        self.version_h_widgetLayout.addWidget(self.version_title)
        self.version_h_widgetLayout.addWidget(self.version_type)
        
        self.ref_line_title = QLabel("Reference Line Fitting")
        self.ref_line_title.setFont(QFont('Arial', 12))
        self.ref_line_fit_type = QComboBox(self)
        self.ref_line_fit_type.addItem('Optimized')
        self.ref_line_fit_type.addItem('Conservative')
        
        self.smoothing_road_check = QCheckBox('Smoothing road', self)
        self.smoothing_road_check.setCheckState(self.smoothing_road)
        self.smoothing_road_check.stateChanged.connect(
            lambda:self.setState('SMOOTHING_ROAD', self.smoothing_road_check))
        
        self.ref_line_fit_h_widgetLayout.addWidget(self.ref_line_title)
        self.ref_line_fit_h_widgetLayout.addWidget(self.ref_line_fit_type)
        
        self.lane_expansion_parameters = QLabel("Lane Expansion Parameters")
        self.lane_expansion_parameters.setFont(QFont('Arial', 12))
        self.width_threshold = QLabel("Width threshold %")
        self.width_threshold_input = QLineEdit(self)
        self.width_threshold_input.setText('100')
        
        self.s_offset_detection_threshold = QLabel("S-offset detection threshold")
        self.s_offset_detection_threshold_input = QLineEdit(self)
        self.s_offset_detection_threshold_input.setText('50')

        self.sg_check = QCheckBox('Signal', self)
        self.sg_check.setCheckState(self.signal_state)
        self.sg_check.stateChanged.connect(
            lambda:self.setState('SIGNAL', self.sg_check))

        self.mr_check = QCheckBox('Search for Matching Road (When Signals Included)', self)
        self.mr_check.setCheckState(self.matching_road)
        self.mr_check.stateChanged.connect(
            lambda:self.setState('MATCHING_ROAD', self.mr_check))

        self.disable_lane_link_check = QCheckBox('Disable Predecessor/Successor Link between Lanes', self)
        self.disable_lane_link_check.setCheckState(self.disable_lane_link)
        self.disable_lane_link_check.stateChanged.connect(
            lambda:self.setState('DISABLE_LANE_LINK', self.disable_lane_link_check))
        
        self.superelevation_check = QCheckBox('Include Superelevation', self)
        self.superelevation_check.setCheckState(self.superelevation)
        self.superelevation_check.stateChanged.connect(
            lambda:self.setState('SUPERELEVATION', self.superelevation_check))
        
        # QCheckBox를 만들어 준다
        self.add_virtual_shoulder_check = QCheckBox('Add virtual shoulder', self)
        # QCheckBox의 초기 체크상태를 False로 지정한다.
        self.add_virtual_shoulder_check.setCheckState(self.add_virtual_shoulder)
        # QCheckBox의 체크상태가 바뀌면, lambda callback 함수를 실행한다. 
        # QCheckBox의 체크 상태를 반영해준다.
        self.add_virtual_shoulder_check.stateChanged.connect(
            lambda:self.setState('ADD_VIRTUAL_SHOULDER', self.add_virtual_shoulder_check))
        
        self.extra_spacing = QLabel()
        
        reset_btn = QPushButton('Load Default Values', self)
        reset_btn.clicked.connect(self.resetJson)
        
        self.v_widgetLayout.addLayout(self.version_h_widgetLayout)
        self.v_widgetLayout.addLayout(self.ref_line_fit_h_widgetLayout)
        widgetLayout.addWidget(self.smoothing_road_check)
        widgetLayout.addWidget(QLabel())
        widgetLayout.addWidget(self.lane_expansion_parameters)
        widgetLayout.addWidget(self.width_threshold, 3, 0)
        widgetLayout.addWidget(self.width_threshold_input, 3, 1)
        widgetLayout.addWidget(self.s_offset_detection_threshold, 4, 0)
        widgetLayout.addWidget(self.s_offset_detection_threshold_input, 4, 1)
        widgetLayout.addWidget(QLabel())
        widgetLayout.addWidget(self.sg_check, 6, 0)
        widgetLayout.addWidget(self.mr_check, 7, 0)
        widgetLayout.addWidget(self.disable_lane_link_check, 8, 0)
        widgetLayout.addWidget(self.superelevation_check, 9, 0)
        widgetLayout.addWidget(self.add_virtual_shoulder_check, 10, 0)
        widgetLayout.addWidget(self.virtual_shoulder_input, 10, 1, Qt.AlignCenter)
        widgetLayout.addWidget(reset_btn, 11, 1, Qt.AlignRight)
        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.v_widgetLayout.addLayout(widgetLayout)
        self.v_widgetLayout.addWidget(self.buttonbox)
        self.v_widgetLayout.sizeHint() # PyQt5.QtCore.QSize(498, 210)
        self.v_widgetLayout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(self.v_widgetLayout) 
        self.setWindowTitle('Export OpenDRIVE')

    def resetJson(self):
        '''
        "Load Default Values" 버튼이 클릭되었을때, 모든 필드들을 초기화 한다.
        '''
        default_file = os.path.join(self.config_file_path, 'GUI/config_odr_param_default.json')
        config_default = None
        with open(default_file, 'r') as f:
            config_default = json.load(f)
        self.smoothing_road_check.setCheckState(config_default['SMOOTHING']['ROAD'])
        self.sg_check.setCheckState(config_default['SIGNAL']['STATE'])
        self.mr_check.setCheckState(config_default['MATCHING_ROAD']['STATE'])
        self.disable_lane_link_check.setCheckState(config_default['DISABLE_LANE_LINK']['STATE'])
        self.superelevation_check.setCheckState(config_default['SUPERELEVATION']['STATE'])
        self.add_virtual_shoulder_check.setCheckState(config_default['VIRTUAL']['SHOULDER'])
        self.virtual_shoulder_input.setText("")
        self.virtual_shoulder_input.setEnabled(False)
    
    def setState(self, data, state):
        '''
        체크박스의 버튼이 클릭되었을때, 각 필드의 상태를 저장해준다.
        '''
        if state.isChecked() == True:
            new_state = Qt.Checked
        else:
            new_state = Qt.Unchecked
        if data == "SMOOTHING_ROAD":
            self.smoothing_road = new_state
        if data == 'SIGNAL':
            self.signal_state = new_state

        elif data == 'MATCHING_ROAD':
            self.matching_road = new_state

        elif data == 'DISABLE_LANE_LINK':
            self.disable_lane_link = new_state

        elif data == 'SUPERELEVATION':
            self.superelevation = new_state
             
        elif data == 'ADD_VIRTUAL_SHOULDER':
            if new_state == Qt.Unchecked:
                self.virtual_shoulder_input.setEnabled(False)
                self.virtual_shoulder_input.setText("")
            else:
                self.virtual_shoulder_input.setEnabled(True)
            self.add_virtual_shoulder = new_state  
            
    def isCorrect(self, data):
        """새로운 데이터 타입 input이 양의 실수인지를 확인한다."""
        try:
            float(data)
            if float(data) >= 0:
                return True
            else:
                return False
        except ValueError:
            return False

    def showDialog(self):
        return super().exec_()
    
    def extract_valid_output(self):
        self.version_type_figure = self.version_type.currentText()
        file_path = os.path.join(self.config_file_path, 'config_odr_param.json')
        # 타당한 input(양의 실수)가 들어왔을 경우에만, config 파일들을 채워 넣어줍니다.
        with open(file_path, 'w') as output:
            self.odr_param['SMOOTHING']['ROAD'] = self.smoothing_road
            self.odr_param['SIGNAL']['STATE'] = self.signal_state
            self.odr_param['MATCHING_ROAD']['STATE'] = self.matching_road
            self.odr_param['DISABLE_LANE_LINK']['STATE'] = self.disable_lane_link
            self.odr_param['SUPERELEVATION']['STATE'] = self.superelevation
            self.odr_param['VIRTUAL']['SHOULDER'] = self.add_virtual_shoulder
            self.odr_param['VERSION']['TYPE'] = self.version_type_figure
            self.odr_param['SHOULDER']['WIDTH'] = self.virtual_shoulder_input.text()
            self.odr_param['WIDTH']['THRESHOLD'] = self.width_threshold_input.text()
            self.odr_param['DETECTION']['THRESHOLD'] = self.s_offset_detection_threshold_input.text()
            self.odr_param['REFERENCE']['LINE']['FITTING'] = True if self.ref_line_fit_type.currentText() == 'Optimized' else False
            json.dump(self.odr_param, output, indent=2)

    def accept(self):
        '''
        최종 Okay 버튼이 눌러졌을 때, 일어나는 동작들을 기술한다.
        '''

        # 만약 체크박스 활성화시에 add_virtual_shoulder input이 없으면 , 경고문을 출력해줍니다.
        if self.add_virtual_shoulder_check == Qt.Checked:
            if self.virtual_shoulder_input.text() == '':
                QMessageBox.warning(self, "Type Error", "Please fill up the value!")
                return
            if not self.isCorrect(self.virtual_shoulder_input.text()):
                QMessageBox.warning(self, "Type Error", "Please enter positive integer/float value!")
                return
            if self.isCorrect(self.virtual_shoulder_input.text()):
                self.extract_valid_output()
                self.done(1)
        else:
            self.extract_valid_output()
            self.done(1)

    def close(self):
        self.done(0)
        
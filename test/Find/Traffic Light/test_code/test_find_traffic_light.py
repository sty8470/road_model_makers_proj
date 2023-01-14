import json
import os
import pytest
import sys
import time

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Traffic Light/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.widget.find_traffic_light_window import FindTrafficLightWindow
from lib.mgeo.utils.mgeo_find import find_traffic_light
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link
from PyQt5.QtWidgets import *

class TestFindTrafficLight:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls,'link_set')
        cls.global_info_set = cls.load_json_data(cls,'global_info')
        cls.tl_set = cls.load_json_data(cls, 'traffic_light_set')
        cls.search_conditions = None
        cls.mgeo_type = MGeoItem.TRAFFIC_LIGHT
    
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
        
    @pytest.fixture
    def expected_link_set(self):
        tested_node_set, tested_link_set, tested_junction_set = load_node_and_link(self.node_set, self.link_set, self.global_info_set)
        return tested_link_set
    
    @pytest.fixture
    def expected_tl_set(self, expected_link_set):
        tested_tl_set = MGeo.load_signal_data(self.tl_set, expected_link_set)
        return tested_tl_set
    
    @pytest.fixture
    def tl_mock_app_empty(self, qtbot):
        test_ui = FindTrafficLightWindow()
        test_ui.txtTrafficLightID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def tl_mock_app_invalid(self, qtbot):
        test_ui = FindTrafficLightWindow()
        test_ui.txtTrafficLightID.setText('asdasdkjkl@$@^@.,,v,v,')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def tl_mock_app_valid(self, qtbot):
        test_ui = FindTrafficLightWindow()
        test_ui.txtTrafficLightID.setText('SN000000')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture 
    def find_traffic_light_idx_empty(self, expected_tl_set, tl_mock_app_empty):
        return find_traffic_light(self.search_conditions, expected_tl_set, is_primitive=False)
    
    @pytest.fixture 
    def find_traffic_light_idx_invalid(self, expected_tl_set, tl_mock_app_invalid):
        return find_traffic_light(self.search_conditions, expected_tl_set, is_primitive=False)
    
    @pytest.fixture 
    def find_traffic_light_idx_valid(self, expected_tl_set, tl_mock_app_valid):
        return find_traffic_light(self.search_conditions, expected_tl_set, is_primitive=False)
    

    # --------------- Start: MGeo 데이터의 Traffic Light의 id 값이 유저입력으로부터 Traffic Light ID를 받아서 찾을 Traffic Light의 인스턴스의 id값과 같은지 확인한다,  ---------------
    # 1
    def test_find_tl_idx_empty_string(self, find_traffic_light_idx_empty):
        assert list(self.search_conditions['traffic_light_id']['val']) == find_traffic_light_idx_empty    
        
    def test_find_tl_idx_invalid_string(self, find_traffic_light_idx_invalid):
        assert self.search_conditions['traffic_light_id']['val'] != find_traffic_light_idx_invalid    
    
    def test_find_tl_idx_valid_string(self, find_traffic_light_idx_valid):
        assert self.search_conditions['traffic_light_id']['val'] == find_traffic_light_idx_valid[0]['id']    
    # --------------- Finish: MGeo 데이터의 Traffic Light의 id 값이 유저입력으로부터 Traffic Light ID를 받아서 찾을 Traffic Light의 인스턴스의 id값과 같은지 확인한다,  ---------------
 
   
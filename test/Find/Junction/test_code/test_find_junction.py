import json
import os
import pytest
import sys
import time

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Junction/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.widget.find_junction_window import FindJunctionWindow
from lib.mgeo.utils.mgeo_find import find_junction
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link
from PyQt5.QtWidgets import *

class TestFindJunction:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls,'link_set')
        cls.global_info_set = cls.load_json_data(cls,'global_info')
        cls.search_conditions = None
        cls.mgeo_type = MGeoItem.JUNCTION
    
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
        
    @pytest.fixture
    def expected_junction_set(self):
        tested_node_set, tested_link_set, tested_junction_set = load_node_and_link(self.node_set, self.link_set, self.global_info_set)
        return tested_junction_set
    
    @pytest.fixture
    def junction_mock_app_empty(self, qtbot):
        test_ui = FindJunctionWindow()
        test_ui.txtJunctionID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def junction_mock_app_invalid(self, qtbot):
        test_ui = FindJunctionWindow()
        test_ui.txtJunctionID.setText('adkjal<>>>!!@&&')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def junction_mock_app_valid(self, qtbot):
        test_ui = FindJunctionWindow()
        test_ui.txtJunctionID.setText('1000039')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture 
    def find_junction_idx_empty(self, expected_junction_set, junction_mock_app_empty):
        return find_junction(self.search_conditions, expected_junction_set, is_primitive=False)
    
    @pytest.fixture 
    def find_junction_idx_invalid(self, expected_junction_set, junction_mock_app_invalid):
        return find_junction(self.search_conditions, expected_junction_set, is_primitive=False)
    
    @pytest.fixture 
    def find_junction_idx_valid(self, expected_junction_set, junction_mock_app_valid):
        return find_junction(self.search_conditions, expected_junction_set, is_primitive=False)

    # # --------------- Start: MGeo 데이터의 Junction의 id 값이 유저입력으로부터 Junction ID를 받아서 찾을 Junction의 인스턴스의 id값과 같은지 확인한다.  ---------------
    # 1
    def test_find_junction_idx_empty_string(self, find_junction_idx_empty):
        assert list(self.search_conditions['junction_id']['val']) == find_junction_idx_empty
    
    def test_find_junction_idx_invalid_string(self, find_junction_idx_invalid):
        assert self.search_conditions['junction_id']['val'] != find_junction_idx_invalid
    
    def test_find_junction_idx_valid_string(self, find_junction_idx_valid):
        assert self.search_conditions['junction_id']['val'] == find_junction_idx_valid[0]['id']
    
    # # --------------- Finish: MGeo 데이터의 Junction의 id 값이 유저입력으로부터 Junction ID를 받아서 찾을 Junction의 인스턴스의 id값과 같은지 확인한다.  ---------------
 
   
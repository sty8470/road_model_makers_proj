import json
import os
import pytest
import sys
import time

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Node/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.utils.mgeo_find import find_node
from lib.widget.find_node_window import FindNodeWindow
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestFindNode:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls,'link_set')
        cls.global_info_set = cls.load_json_data(cls,'global_info')
        cls.mgeo_type = MGeoItem.NODE
        cls.search_conditions = None
    
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
        
    @pytest.fixture
    def expected_node_set(self):
        tested_node_set, tested_link_set, tested_junction_set = load_node_and_link(self.node_set, self.link_set, self.global_info_set)
        return tested_node_set
    
    @pytest.fixture
    def node_mock_app_empty(self, qtbot):
        test_ui = FindNodeWindow()
        test_ui.txtNodeID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def node_mock_app_invalid(self, qtbot):
        test_ui = FindNodeWindow()
        test_ui.txtNodeID.setText('xxxxyyyyzzzzaaasssbbb')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def node_mock_app_valid(self, qtbot):
        test_ui = FindNodeWindow()
        test_ui.txtNodeID.setText('Node1')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def node_mock_app_on_stop_line(self, qtbot):
        test_ui = FindNodeWindow()
        test_ui.txtNodeID.setText('Node2')
        test_ui.cbOnStopLine.setChecked(True)
        test_ui.cbValOnStopLine.setChecked(True)
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture 
    def find_node_idx_empty(self, expected_node_set, node_mock_app_empty):
        return find_node(self.search_conditions, expected_node_set, is_primitive=False)
    
    @pytest.fixture 
    def find_node_idx_invalid(self, expected_node_set, node_mock_app_invalid):
        return find_node(self.search_conditions, expected_node_set, is_primitive=False)
    
    @pytest.fixture 
    def find_node_idx_valid(self, expected_node_set, node_mock_app_valid):
        return find_node(self.search_conditions, expected_node_set, is_primitive=False)
    
    @pytest.fixture 
    def find_node_idx_on_stop_line(self, expected_node_set, node_mock_app_on_stop_line):
        return find_node(self.search_conditions, expected_node_set, is_primitive=False)

    # --------------- Start: 사용자가 직접 입력한 node_id 박스의 체크여부와 값을 직접 MGeo 메모리 안에 있는 node들과 비교해서 찾는다. ---------------
    # 1
    def test_find_node_idx_empty_string(self, expected_node_set, find_node_idx_empty):
        assert list(self.search_conditions['node_id']['val']) == find_node_idx_empty
    
    def test_find_node_idx_invalid_string(self, expected_node_set, find_node_idx_invalid):
        assert self.search_conditions['node_id']['val'] != find_node_idx_invalid

    def test_find_node_idx_valid_string(self, expected_node_set, find_node_idx_valid):
        assert self.search_conditions['node_id']['val'] == find_node_idx_valid[0]['id']
    
    def test_find_node_idx_valid_string_with_on_stop_line(self, expected_node_set, find_node_idx_on_stop_line):
        assert self.search_conditions['node_id']['checked'] == True 
        assert self.search_conditions['on_stop_line']['checked'] == True 
        assert self.search_conditions['on_stop_line']['val'] == True
        assert self.search_conditions['node_id']['val'] == find_node_idx_on_stop_line[0]['id']
   
   # --------------- Finish: 사용자가 직접 입력한 node_id 박스의 체크여부와 값을 직접 MGeo 메모리 안에 있는 node들과 비교해서 찾는다. ---------------
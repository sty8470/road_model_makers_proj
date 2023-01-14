import json
import os
import pytest
import sys
import time

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Link/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)


from lib.mgeo.utils.mgeo_find import find_link
from lib.widget.find_link_window import FindLinkWindow
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestFindLink:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls,'link_set')
        cls.global_info_set = cls.load_json_data(cls,'global_info')
        cls.mgeo_type = MGeoItem.LINK
        cls.search_conditions = None
    
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
        
    @pytest.fixture
    def expcted_link_set(self):
        tested_node_set, tested_link_set, tested_junction_set = load_node_and_link(self.node_set, self.link_set, self.global_info_set)
        return tested_link_set
    
    @pytest.fixture
    def link_mock_app_empty(self, qtbot):
        test_ui = FindLinkWindow()
        test_ui.cbLinkID.setChecked(True)
        test_ui.txtLinkID.setText('')
        test_ui.cbMaxSpeedLow.setChecked(True)
        test_ui.txtMaxSpeedLow.setText('0')
        test_ui.cbMaxSpeedHigh.setChecked(True)
        test_ui.txtMaxSpeedHigh.setText('80')
        test_ui.cbLinkType.setChecked(True)
        test_ui.txtLinkType.setText('driving')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def link_mock_app_invalid(self, qtbot):
        test_ui = FindLinkWindow()
        test_ui.cbLinkID.setChecked(True)
        test_ui.txtLinkID.setText('asdsadlkj3292@#^$&...N>N>')
        test_ui.cbMaxSpeedLow.setChecked(True)
        test_ui.txtMaxSpeedLow.setText('0')
        test_ui.cbMaxSpeedHigh.setChecked(True)
        test_ui.txtMaxSpeedHigh.setText('80')
        test_ui.cbLinkType.setChecked(True)
        test_ui.txtLinkType.setText('driving')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def link_mock_app_valid(self, qtbot):
        test_ui = FindLinkWindow()
        test_ui.cbLinkID.setChecked(True)
        test_ui.txtLinkID.setText('LN000000')
        test_ui.cbMaxSpeedLow.setChecked(True)
        test_ui.txtMaxSpeedLow.setText('0')
        test_ui.cbMaxSpeedHigh.setChecked(True)
        test_ui.txtMaxSpeedHigh.setText('80')
        test_ui.cbLinkType.setChecked(True)
        test_ui.txtLinkType.setText('driving')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def link_mock_app_valid_with_other_parameters(self, qtbot):
        test_ui = FindLinkWindow()
        test_ui.cbLinkID.setChecked(True)
        test_ui.txtLinkID.setText('LN000000')
        test_ui.cbMaxSpeedLow.setChecked(True)
        test_ui.txtMaxSpeedLow.setText('20')
        test_ui.cbMaxSpeedHigh.setChecked(True)
        test_ui.txtMaxSpeedHigh.setText('140')
        test_ui.cbLinkType.setChecked(True)
        test_ui.txtLinkType.setText('driving')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture 
    def find_link_idx_empty(self, expcted_link_set, link_mock_app_empty):
        return find_link(self.search_conditions, expcted_link_set, is_primitive=False)
    
    @pytest.fixture 
    def find_link_idx_invalid(self, expcted_link_set, link_mock_app_invalid):
        return find_link(self.search_conditions, expcted_link_set, is_primitive=False)
    
    @pytest.fixture 
    def find_link_idx_valid(self, expcted_link_set, link_mock_app_valid):
        return find_link(self.search_conditions, expcted_link_set, is_primitive=False)
    
    @pytest.fixture 
    def find_link_idx_valid_with_other_parameters(self, expcted_link_set, link_mock_app_valid_with_other_parameters):
        return find_link(self.search_conditions, expcted_link_set, is_primitive=False)


    # --------------- Start: 사용자가 직접 입력한 link_id 박스의 체크여부와 값을 직접 MGeo 메모리 안에 있는 node들과 비교해서 찾는다. ---------------
    # 1
    def test_find_link_idx_empty_string(self, find_link_idx_empty):
        assert list(self.search_conditions['link_id']['val']) == find_link_idx_empty
    
    def test_find_link_idx_invalid_string(self, find_link_idx_invalid):
        assert self.search_conditions['link_id']['val'] != find_link_idx_invalid
    
    def test_find_link_idx_valid_string(self, find_link_idx_valid):
        assert self.search_conditions['link_id']['val'] == find_link_idx_valid[0]['id']
    
    def test_find_link_idx_valid_with_other_parameters(self, find_link_idx_valid_with_other_parameters):
        assert self.search_conditions['link_id']['checked'] == True
        assert self.search_conditions['link_id']['val'] == 'LN000000'
        assert self.search_conditions['max_speed_low'] == 20
        assert self.search_conditions['max_speed_high'] == 140
        assert self.search_conditions['link_type'] == 'driving'
        
    # --------------- Finish: 사용자가 직접 입력한 link_id 박스의 체크여부와 값을 직접 MGeo 메모리 안에 있는 node들과 비교해서 찾는다. ---------------
      
        
   
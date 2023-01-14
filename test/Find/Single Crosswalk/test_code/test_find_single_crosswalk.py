import json
import os
import pytest
import sys
import time

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Single Crosswalk/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)


from lib.mgeo.utils.mgeo_find import find_single_crosswalk
from lib.widget.find_single_crosswalk_window import FindSingleCrosswalkWindow
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestFindSingleCrosswalk:
    
    @classmethod
    def setup_class(cls):
        cls.scw_set = cls.load_json_data(cls, 'singlecrosswalk_set')
        cls.mgeo_type = MGeoItem.SINGLECROSSWALK
        cls.search_conditions = None
        
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
        
    @pytest.fixture
    def expected_scw_set(self):
        tested_scw_set = MGeo.load_single_crosswalk_data(self.scw_set)
        return tested_scw_set
    
    @pytest.fixture
    def scw_mock_app_empty(self, qtbot):
        test_ui = FindSingleCrosswalkWindow()
        test_ui.txtSingleCrosswalkID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def scw_mock_app_invalid(self, qtbot):
        test_ui = FindSingleCrosswalkWindow()
        test_ui.txtSingleCrosswalkID.setText('asdfasdf!@%$^%$&GFG')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def scw_mock_app_valid(self, qtbot):
        test_ui = FindSingleCrosswalkWindow()
        test_ui.txtSingleCrosswalkID.setText('B319BS010058')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture 
    def find_single_crosswalk_idx_empty(self, expected_scw_set, scw_mock_app_empty):
        return find_single_crosswalk(self.search_conditions, expected_scw_set, is_primitive=False)
    
    @pytest.fixture 
    def find_single_crosswalk_idx_invalid(self, expected_scw_set, scw_mock_app_invalid):
        return find_single_crosswalk(self.search_conditions, expected_scw_set, is_primitive=False)
    
    @pytest.fixture 
    def find_single_crosswalk_idx_valid(self, expected_scw_set, scw_mock_app_valid):
        return find_single_crosswalk(self.search_conditions, expected_scw_set, is_primitive=False)
    

    # # --------------- Start: MGeo 데이터의 singlecrosswalk id 값이 유저입력으로부터 singlecrosswalk ID를 받아서 찾을 singlecrosswalk 인스턴스의 id값과 같은지 확인한다.  ---------------
    # 1
    def test_find_single_crosswalk_idx_empty_string(self, find_single_crosswalk_idx_empty):
        assert list(self.search_conditions['single_crosswalk_id']['val']) == find_single_crosswalk_idx_empty
    
    def test_find_single_crosswalk_idx_invalid_string(self, find_single_crosswalk_idx_invalid):
        assert self.search_conditions['single_crosswalk_id']['val'] != find_single_crosswalk_idx_invalid
    
    def test_find_single_crosswalk_idx_valid_string(self, find_single_crosswalk_idx_valid):
        assert self.search_conditions['single_crosswalk_id']['val'] == find_single_crosswalk_idx_valid[0]['id']
        
    # # --------------- Finish: MGeo 데이터의 singlecrosswalk id 값이 유저입력으로부터 singlecrosswalk ID를 받아서 찾을 singlecrosswalk 인스턴스의 id값과 같은지 확인한다.  ---------------
      
        
   
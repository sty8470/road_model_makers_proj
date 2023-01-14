import json
import os
import pytest
import sys
import time

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Crosswalk/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)


from lib.mgeo.utils.mgeo_find import find_crosswalk
from lib.widget.find_crosswalk_window import FindCrosswalkWindow
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestFindCrosswalk:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls,'link_set')
        cls.global_info_set = cls.load_json_data(cls,'global_info')
        cls.tl_set = cls.load_json_data(cls, 'traffic_light_set')
        cls.cw_set = cls.load_json_data(cls, 'crosswalk_set')
        cls.scw_set = cls.load_json_data(cls, 'singlecrosswalk_set')
        cls.mgeo_type = MGeoItem.CROSSWALK
        cls.search_conditions = None
        
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
    def expected_scw_set(self):
        tested_scw_set = MGeo.load_single_crosswalk_data(self.scw_set)
        return tested_scw_set
    
    @pytest.fixture 
    def expected_cw_set(self, expected_scw_set, expected_tl_set):
        tested_cw_set = MGeo.load_crosswalk_data(self.cw_set, expected_scw_set, expected_tl_set)
        return tested_cw_set
    
    @pytest.fixture
    def cw_mock_app_empty(self, qtbot):
        test_ui = FindCrosswalkWindow()
        test_ui.txtCrosswalkID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def cw_mock_app_invalid(self, qtbot):
        test_ui = FindCrosswalkWindow()
        test_ui.txtCrosswalkID.setText('asdfasdf!#!@#N4268568')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def cw_mock_app_valid(self, qtbot):
        test_ui = FindCrosswalkWindow()
        test_ui.txtCrosswalkID.setText('CW000008')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture 
    def find_crosswalk_idx_empty(self, expected_cw_set, cw_mock_app_empty):
        return find_crosswalk(self.search_conditions, expected_cw_set, is_primitive=False)
    
    @pytest.fixture 
    def find_crosswalk_idx_invalid(self, expected_cw_set, cw_mock_app_invalid):
        return find_crosswalk(self.search_conditions, expected_cw_set, is_primitive=False)
    
    @pytest.fixture 
    def find_crosswalk_idx_valid(self, expected_cw_set, cw_mock_app_valid):
        return find_crosswalk(self.search_conditions, expected_cw_set, is_primitive=False)

    # # --------------- Start: MGeo 데이터의 singlecrosswalk id 값이 유저입력으로부터 singlecrosswalk ID를 받아서 찾을 singlecrosswalk 인스턴스의 id값과 같은지 확인한다.  ---------------
    # 1
    def test_find_crosswalk_idx_empty_string(self, find_crosswalk_idx_empty):
        assert list(self.search_conditions['crosswalk_id']['val']) == find_crosswalk_idx_empty
    
    def test_find_crosswalk_idx_invalid_string(self, find_crosswalk_idx_invalid):
        assert self.search_conditions['crosswalk_id']['val'] != find_crosswalk_idx_invalid
    
    def test_find_crosswalk_idx_valid_string(self, find_crosswalk_idx_valid):
        assert self.search_conditions['crosswalk_id']['val'] == find_crosswalk_idx_valid[0]['id']
        
    # # --------------- Finish: MGeo 데이터의 singlecrosswalk id 값이 유저입력으로부터 singlecrosswalk ID를 받아서 찾을 singlecrosswalk 인스턴스의 id값과 같은지 확인한다.  ---------------
      
        
   
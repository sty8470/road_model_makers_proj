import json
import os
import pytest
import sys
import time

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Lane Marking/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)


from lib.mgeo.utils.mgeo_find import find_lane_boundary
from lib.widget.find_lane_boundary_window import FindLaneBoundaryWindow
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestFindLaneMarking:
    
    @classmethod
    def setup_class(cls):
        cls.lane_node_set = cls.load_json_data(cls, 'lane_node_set')
        cls.lane_boundary_set = cls.load_json_data(cls, 'lane_boundary_set')
        cls.mgeo_type = MGeoItem.LANE_BOUNDARY
        cls.search_conditions = None
        
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
        
    @pytest.fixture
    def expected_lane_boundary_set(self):
        tested_lane_set, tested_node_set = MGeo.load_lane_boundary_data(self.lane_node_set, self.lane_boundary_set)
        return tested_lane_set
    
    @pytest.fixture
    def lane_marking_mock_app_empty(self, qtbot):
        test_ui = FindLaneBoundaryWindow()
        test_ui.txtLaneBoundaryID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def lane_marking_mock_app_invalid(self, qtbot):
        test_ui = FindLaneBoundaryWindow()
        test_ui.txtLaneBoundaryID.setText('asdfasdf23262363%^^@#%$$$#')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture
    def lane_marking_mock_app_valid(self, qtbot):
        test_ui = FindLaneBoundaryWindow()
        test_ui.txtLaneBoundaryID.setText('B219BS011485')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(1)
        return test_ui
    
    @pytest.fixture 
    def find_lane_boundary_idx_empty(self, expected_lane_boundary_set, lane_marking_mock_app_empty):
        return find_lane_boundary(self.search_conditions, expected_lane_boundary_set, is_primitive=False)
    
    @pytest.fixture 
    def find_lane_boundary_idx_invalid(self, expected_lane_boundary_set, lane_marking_mock_app_invalid):
        return find_lane_boundary(self.search_conditions, expected_lane_boundary_set, is_primitive=False)
    
    @pytest.fixture 
    def find_lane_boundary_idx_valid(self, expected_lane_boundary_set, lane_marking_mock_app_valid):
        return find_lane_boundary(self.search_conditions, expected_lane_boundary_set, is_primitive=False)

    # # --------------- Start: MGeo 데이터의 lane boundary id 값이 유저입력으로부터 lane boundary ID를 받아서 찾을 lane boundary 인스턴스의 id값과 같은지 확인한다.  ---------------
    # 1
    def test_find_lane_boundary_idx_empty_string(self, find_lane_boundary_idx_empty):
        assert list(self.search_conditions['lane_boundary_id']['val']) == find_lane_boundary_idx_empty        
    
    def test_find_lane_boundary_idx_invalid_string(self, find_lane_boundary_idx_invalid):
        assert self.search_conditions['lane_boundary_id']['val'] != find_lane_boundary_idx_invalid        
        
    def test_find_lane_boundary_idx_valid_string(self, find_lane_boundary_idx_valid):
        assert self.search_conditions['lane_boundary_id']['val'] == find_lane_boundary_idx_valid[0]['id']
    # # --------------- Finish: MGeo 데이터의 lane boundary id 값이 유저입력으로부터 lane boundary ID를 받아서 찾을 lane boundary 인스턴스의 id값과 같은지 확인한다.  ---------------
    
      
        
   
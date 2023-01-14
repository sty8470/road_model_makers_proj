import json
import os
import pytest
import sys
import time

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Find (from all primitives)/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.widget.find_mgeo_item_window import FindMGeoItemWindow
from lib.mgeo.utils.mgeo_find import *
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link
from PyQt5.QtWidgets import *

class TestFindPrimitives:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls,'link_set')
        cls.global_info_set = cls.load_json_data(cls,'global_info')
        cls.ts_set = cls.load_json_data(cls, 'traffic_sign_set')
        cls.tl_set = cls.load_json_data(cls, 'traffic_light_set')
        cls.lane_node_set = cls.load_json_data(cls, 'lane_node_set')
        cls.lane_boundary_set = cls.load_json_data(cls, 'lane_boundary_set')
        cls.search_conditions = None
        cls.scw_set = cls.load_json_data(cls, 'singlecrosswalk_set')
        cls.cw_set = cls.load_json_data(cls, 'crosswalk_set') 
        cls.mgeo_type = MGeoItem.NODE
    
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
    def expected_link_set(self):
        tested_node_set, tested_link_set, tested_junction_set = load_node_and_link(self.node_set, self.link_set, self.global_info_set)
        return tested_link_set
    
    @pytest.fixture
    def expected_ts_set(self, expected_link_set):
        tested_sign_set = MGeo.load_signal_data(self.ts_set, expected_link_set)
        return tested_sign_set
    
    @pytest.fixture
    def expected_tl_set(self, expected_link_set):
        tested_tl_set = MGeo.load_signal_data(self.tl_set, expected_link_set)
        return tested_tl_set
    
    @pytest.fixture
    def expected_junction_set(self, expected_link_set):
        tested_node_set, tested_link_set, tested_junction_set = load_node_and_link(self.node_set, self.link_set, self.global_info_set)
        return tested_junction_set
    
    @pytest.fixture
    def expected_lane_boundary_set(self):
        tested_lane_set, tested_node_set = MGeo.load_lane_boundary_data(self.lane_node_set, self.lane_boundary_set)
        return tested_lane_set
    
    @pytest.fixture
    def expected_scw_set(self):
        tested_scw_set = MGeo.load_single_crosswalk_data(self.scw_set)
        return tested_scw_set
    
    @pytest.fixture 
    def expected_cw_set(self, expected_scw_set, expected_tl_set):
        tested_cw_set = MGeo.load_crosswalk_data(self.cw_set, expected_scw_set, expected_tl_set)
        return tested_cw_set
    
    @pytest.fixture
    def node_mock_app_empty(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def node_mock_app_invalid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('aaaabbbbbcccccc')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def node_mock_app_valid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('A119BS010141')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def link_mock_app_empty(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def link_mock_app_invalid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('zzzzzxxxxxxxx121212')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def link_mock_app_valid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('A219BS010444')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def ts_mock_app_empty(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def ts_mock_app_invalid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('lkji989002396326asdvg')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def ts_mock_app_valid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('B119BS010005')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture  
    def tl_mock_app_empty(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def tl_mock_app_invalid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('bn123890b,zmcblz/!@%@$')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def tl_mock_app_valid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('C119BS010053')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui

    @pytest.fixture  
    def junction_mock_app_empty(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def junction_mock_app_invalid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('^&#%&#%&#!Xccxbsd`11144')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def junction_mock_app_valid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('1000042')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture  
    def lane_marking_mock_app_empty(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def lane_marking_mock_app_invalid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('NH%&*CCC12536347#%&#%')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def lane_marking_mock_app_valid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('LM000248')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture 
    def single_crosswalk_mock_app_empty(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def single_crosswalk_mock_app_invalid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('2218522?<><sd223t')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def single_crosswalk_mock_app_valid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('B319BS010063')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture 
    def crosswalk_mock_app_empty(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def crosswalk_mock_app_invalid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('sadfdas12/1^@$../.<B>?<>?<MV')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture
    def crosswalk_mock_app_valid(self, qtbot):
        test_ui = FindMGeoItemWindow()
        test_ui.txtMGeoItemID.setText('CW000014')
        self.search_conditions = test_ui.getParameters()
        test_ui.show()
        time.sleep(0.5)
        return test_ui
    
    @pytest.fixture 
    def find_mgeo_node_idx_empty(self, expected_node_set, node_mock_app_empty):
        return find_node(self.search_conditions, expected_node_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_node_idx_invalid(self, expected_node_set, node_mock_app_invalid):
        return find_node(self.search_conditions, expected_node_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_node_idx_valid(self, expected_node_set, node_mock_app_valid):
        return find_node(self.search_conditions, expected_node_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_link_idx_empty(self, expected_link_set, link_mock_app_empty):
        return find_link(self.search_conditions, expected_link_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_link_idx_invalid(self, expected_link_set, link_mock_app_invalid):
        return find_link(self.search_conditions, expected_link_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_link_idx_valid(self, expected_link_set, link_mock_app_valid):
        return find_link(self.search_conditions, expected_link_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_ts_idx_empty(self, expected_ts_set, ts_mock_app_empty):
        return find_traffic_sign(self.search_conditions, expected_ts_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_ts_idx_invalid(self, expected_ts_set, ts_mock_app_invalid):
        return find_traffic_sign(self.search_conditions, expected_ts_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_ts_idx_valid(self, expected_ts_set, ts_mock_app_valid):
        return find_traffic_sign(self.search_conditions, expected_ts_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_tl_idx_empty(self, expected_tl_set, tl_mock_app_empty):
        return find_traffic_light(self.search_conditions, expected_tl_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_tl_idx_invalid(self, expected_tl_set, tl_mock_app_invalid):
        return find_traffic_light(self.search_conditions, expected_tl_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_tl_idx_valid(self, expected_tl_set, tl_mock_app_valid):
        return find_traffic_light(self.search_conditions, expected_tl_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_junction_idx_empty(self, expected_junction_set, junction_mock_app_empty):
        return find_junction(self.search_conditions, expected_junction_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_junction_idx_invalid(self, expected_junction_set, junction_mock_app_invalid):
        return find_junction(self.search_conditions, expected_junction_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_junction_idx_valid(self, expected_junction_set, junction_mock_app_valid):
        return find_junction(self.search_conditions, expected_junction_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_lane_marking_idx_empty(self, expected_lane_boundary_set, lane_marking_mock_app_empty):
        return find_lane_boundary(self.search_conditions, expected_lane_boundary_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_lane_marking_idx_invalid(self, expected_lane_boundary_set, lane_marking_mock_app_invalid):
        return find_lane_boundary(self.search_conditions, expected_lane_boundary_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_lane_marking_idx_valid(self, expected_lane_boundary_set, lane_marking_mock_app_valid):
        return find_lane_boundary(self.search_conditions, expected_lane_boundary_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_single_crosswalk_idx_empty(self, expected_scw_set, single_crosswalk_mock_app_empty):
        return find_single_crosswalk(self.search_conditions, expected_scw_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_single_crosswalk_idx_invalid(self, expected_scw_set, single_crosswalk_mock_app_invalid):
        return find_single_crosswalk(self.search_conditions, expected_scw_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_single_crosswalk_idx_valid(self, expected_scw_set, single_crosswalk_mock_app_valid):
        return find_single_crosswalk(self.search_conditions, expected_scw_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_crosswalk_idx_empty(self, expected_cw_set, crosswalk_mock_app_empty):
        return find_crosswalk(self.search_conditions, expected_cw_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_crosswalk_idx_invalid(self, expected_cw_set, crosswalk_mock_app_invalid):
        return find_crosswalk(self.search_conditions, expected_cw_set, is_primitive=True)
    
    @pytest.fixture 
    def find_mgeo_crosswalk_idx_valid(self, expected_cw_set, crosswalk_mock_app_valid):
        return find_crosswalk(self.search_conditions, expected_cw_set, is_primitive=True)

    ############################################################################################################
    # # --------------- Start: MGeo 데이터의 id 값이 유저입력으로부터 ID를 받아서 찾을 MGeo 인스턴스의 id값과 같은지 확인한다.  ---------------
    # 1
    
    def test_find_mgeo_node_idx_empty_string(self, find_mgeo_node_idx_empty, node_mock_app_empty):
        assert list(self.search_conditions['mgeo_item_id']['val']) == find_mgeo_node_idx_empty
    
    def test_find_mgeo_node_idx_invalid_string(self, find_mgeo_node_idx_invalid, node_mock_app_invalid):
        assert self.search_conditions['mgeo_item_id']['val'] != find_mgeo_node_idx_invalid
      
    def test_find_mgeo_node_idx_valid_string(self, find_mgeo_node_idx_valid, node_mock_app_valid):
        assert self.search_conditions['mgeo_item_id']['val'] == find_mgeo_node_idx_valid[0]['id']
        
    def test_find_mgeo_link_idx_empty_string(self, find_mgeo_link_idx_empty, link_mock_app_empty):
        assert list(self.search_conditions['mgeo_item_id']['val']) == find_mgeo_link_idx_empty
    
    def test_find_mgeo_link_idx_invalid_string(self, find_mgeo_link_idx_invalid, link_mock_app_invalid):
        assert self.search_conditions['mgeo_item_id']['val'] != find_mgeo_link_idx_invalid
      
    def test_find_mgeo_link_idx_valid_string(self, find_mgeo_link_idx_valid, link_mock_app_valid):
        assert self.search_conditions['mgeo_item_id']['val'] == find_mgeo_link_idx_valid[0]['id']
    
    def test_find_mgeo_ts_idx_empty_string(self, find_mgeo_ts_idx_empty, ts_mock_app_empty):
        assert list(self.search_conditions['mgeo_item_id']['val']) == find_mgeo_ts_idx_empty
    
    def test_find_mgeo_ts_idx_invalid_string(self, find_mgeo_ts_idx_invalid, ts_mock_app_invalid):
        assert self.search_conditions['mgeo_item_id']['val'] != find_mgeo_ts_idx_invalid
      
    def test_find_mgeo_ts_idx_valid_string(self, find_mgeo_ts_idx_valid, ts_mock_app_valid):
        assert self.search_conditions['mgeo_item_id']['val'] == find_mgeo_ts_idx_valid[0]['id']
        
    def test_find_mgeo_tl_idx_empty_string(self, find_mgeo_tl_idx_empty, tl_mock_app_empty):
        assert list(self.search_conditions['mgeo_item_id']['val']) == find_mgeo_tl_idx_empty
    
    def test_find_mgeo_tl_idx_invalid_string(self, find_mgeo_tl_idx_invalid, tl_mock_app_invalid):
        assert self.search_conditions['mgeo_item_id']['val'] != find_mgeo_tl_idx_invalid
      
    def test_find_mgeo_tl_idx_valid_string(self, find_mgeo_tl_idx_valid, tl_mock_app_valid):
        assert self.search_conditions['mgeo_item_id']['val'] == find_mgeo_tl_idx_valid[0]['id']
    
    def test_find_mgeo_junction_idx_empty_string(self, find_mgeo_junction_idx_empty, junction_mock_app_empty):
        assert list(self.search_conditions['mgeo_item_id']['val']) == find_mgeo_junction_idx_empty
    
    def test_find_mgeo_junction_idx_invalid_string(self, find_mgeo_junction_idx_invalid, junction_mock_app_invalid):
        assert self.search_conditions['mgeo_item_id']['val'] != find_mgeo_junction_idx_invalid
      
    def test_find_mgeo_junction_idx_valid_string(self, find_mgeo_junction_idx_valid, junction_mock_app_valid):
        assert self.search_conditions['mgeo_item_id']['val'] == find_mgeo_junction_idx_valid[0]['id']
    
    def test_find_mgeo_lane_marking_idx_empty_string(self, find_mgeo_lane_marking_idx_empty, lane_marking_mock_app_empty):
        assert list(self.search_conditions['mgeo_item_id']['val']) == find_mgeo_lane_marking_idx_empty
    
    def test_find_mgeo_lane_marking_idx_invalid_string(self, find_mgeo_lane_marking_idx_invalid, lane_marking_mock_app_invalid):
        assert self.search_conditions['mgeo_item_id']['val'] != find_mgeo_lane_marking_idx_invalid
      
    def test_find_mgeo_lane_marking_idx_valid_string(self, find_mgeo_lane_marking_idx_valid, lane_marking_mock_app_valid):
        assert self.search_conditions['mgeo_item_id']['val'] == find_mgeo_lane_marking_idx_valid[0]['id']
    
    def test_find_mgeo_single_crosswalk_idx_empty_string(self, find_mgeo_single_crosswalk_idx_empty, single_crosswalk_mock_app_empty):
        assert list(self.search_conditions['mgeo_item_id']['val']) == find_mgeo_single_crosswalk_idx_empty
    
    def test_find_mgeo_single_crosswalk_idx_invalid_string(self, find_mgeo_single_crosswalk_idx_invalid, single_crosswalk_mock_app_invalid):
        assert self.search_conditions['mgeo_item_id']['val'] != find_mgeo_single_crosswalk_idx_invalid
      
    def test_find_mgeo_single_crosswalk_idx_valid_string(self, find_mgeo_single_crosswalk_idx_valid, single_crosswalk_mock_app_valid):
        assert self.search_conditions['mgeo_item_id']['val'] == find_mgeo_single_crosswalk_idx_valid[0]['id']
    
    def test_find_mgeo_crosswalk_idx_empty_string(self, find_mgeo_crosswalk_idx_empty, crosswalk_mock_app_empty):
        assert list(self.search_conditions['mgeo_item_id']['val']) == find_mgeo_crosswalk_idx_empty
    
    def test_find_mgeo_crosswalk_idx_invalid_string(self, find_mgeo_crosswalk_idx_invalid, crosswalk_mock_app_invalid):
        assert self.search_conditions['mgeo_item_id']['val'] != find_mgeo_crosswalk_idx_invalid
      
    def test_find_mgeo_crosswalk_idx_valid_string(self, find_mgeo_crosswalk_idx_valid, crosswalk_mock_app_valid):
        assert self.search_conditions['mgeo_item_id']['val'] == find_mgeo_crosswalk_idx_valid[0]['id']
    
    
    
    
    
    
    
    
    
    
    # def test_highlight_mgeo_item(self, find_mgeo_node_idx, node_mock_app):
    #     assert {'key': 'test_data', 'type': [], 'id': []} == {'key': test_data_folder_path.split('\\')[-1], 'type': find_mgeo_node_idx[0]['type'], 'id': find_mgeo_node_idx[0]['id']}
    
    # def test_trans_point_by_id(self):
    #     #  IN DEVELOPMENT
    #     # item = {'key': 'test_data', 'type': <MGeoItem.NODE: 1>, 'id': 'A119BS010290'}
    #     # self.xTran = 18.734041597985197
    #     # self.yTran = -1869.25599779794
    #     # get_point = 
    #     pass
        
    # # --------------- Finish: MGeo 데c이터의 Junction의 id 값이 유저입력으로부터 Junction ID를 받아서 찾을 Junction의 인스턴스의 id값과 같은지 확인한다.  ---------------
 
   
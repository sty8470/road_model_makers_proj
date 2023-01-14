'''
Test하고 싶은 것(5개): synced_traffic_light_set.json안에 있는 idx, link_id_list, point, intersection_controller_id 그리고 signal_id_list들의 값
'''
import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/6_synced_traffic_light_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestLoadSyncedTrafficLight:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls,'link_set')
        cls.global_info_set = cls.load_json_data(cls,'global_info')
        cls.tl_set = cls.load_json_data(cls, 'traffic_light_set')
        cls.synced_tl_set = cls.load_json_data(cls, 'synced_traffic_light_set')
    
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
    def expected_synced_tl_set(self, expected_link_set, expected_tl_set):
        tested_synced_tl_set = MGeo.load_synced_traffic_light_data(self.synced_tl_set, expected_link_set, expected_tl_set)
        return tested_synced_tl_set

    # --------------- Start: MGeo 메모리에 있는 `synced_tl_set`과 `synced_traffic_light_set.json`들의 항목들을 비교한다. ---------------
    # 1
    def test_synced_traffic_light_idx_mgeo(self, expected_synced_tl_set):
        for i in range(len(self.synced_tl_set)):
            assert self.synced_tl_set[i]['idx'] in expected_synced_tl_set.synced_signals
    # 2
    def test_synced_traffic_light_link_id_list_mgeo(self, expected_synced_tl_set):
        for i in range(len(self.synced_tl_set)):
            assert self.synced_tl_set[i]['link_id_list'] == expected_synced_tl_set.synced_signals[self.synced_tl_set[i]['idx']].link_id_list
    # 3
    def test_synced_traffic_light_point_mgeo(self, expected_synced_tl_set):
        for i in range(len(self.synced_tl_set)):
            assert self.synced_tl_set[i]['point'] == expected_synced_tl_set.synced_signals[self.synced_tl_set[i]['idx']].point.tolist()
    # 4
    def test_synced_traffic_light_intersection_controller_id_mgeo(self, expected_synced_tl_set):
        for i in range(len(self.synced_tl_set)):
            assert self.synced_tl_set[i]['intersection_controller_id'] == expected_synced_tl_set.synced_signals[self.synced_tl_set[i]['idx']].intersection_controller_id
    # 5
    def test_synced_traffic_light_signal_id_list_mgeo(self, expected_synced_tl_set):
        for i in range(len(self.synced_tl_set)):
            assert self.synced_tl_set[i]['signal_id_list'] == expected_synced_tl_set.synced_signals[self.synced_tl_set[i]['idx']].signal_id_list

    # ---------- Finish `synced_traffic_light_set.json` test ----------
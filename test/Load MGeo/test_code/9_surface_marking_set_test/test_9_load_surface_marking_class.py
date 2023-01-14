'''
Test하고 싶은 것(6개): surface_marking_set.json안에 있는 idx, points, link_id_list, road_id, type, 그리고 sub_type들의 값
'''
import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/9_surface_marking_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestSaveSurfaceMarking:
    
    @classmethod
    def setup_class(cls):
        
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls,'link_set')
        cls.global_info_set = cls.load_json_data(cls,'global_info')
        cls.sm_set = cls.load_json_data(cls, 'surface_marking_set')

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
    def expected_sm_set(self, expected_link_set):
        tested_sm_set = MGeo.load_surface_marking_data(self.sm_set, expected_link_set)
        return tested_sm_set

    # --------------- Start: MGeo 메모리에 있는 `expected_sm_set`과 `surface_marking_set.json`들의 항목들을 비교한다. ---------------
    # 1
    def test_sm_idx_mgeo(self, expected_sm_set):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['idx'] in expected_sm_set.data
    # 2
    def test_sm_points_mgeo(self, expected_sm_set):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['points'] == expected_sm_set.data[self.sm_set[i]['idx']].points.tolist()
    # 3     
    def test_sm_link_id_list_mgeo(self, expected_sm_set):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['link_id_list'] == expected_sm_set.data[self.sm_set[i]['idx']].link_id_list
    # 4
    def test_sm_road_id_mgeo(self, expected_sm_set):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['road_id'] == expected_sm_set.data[self.sm_set[i]['idx']].road_id
    # 5
    def test_sm_type_mgeo(self, expected_sm_set):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['type'] == expected_sm_set.data[self.sm_set[i]['idx']].type
    # 6
    def test_sm_sub_type_mgeo(self, expected_sm_set):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['sub_type'] == expected_sm_set.data[self.sm_set[i]['idx']].sub_type
    
    # --------------- Finish: MGeo 메모리에 있는 `expected_sm_set`과 `surface_marking_set.json`들의 항목들을 비교한다. ---------------
'''
Test하고 싶은 것(16개): traffic_light_set.json안에 있는 idx, link_id_list, road_id, type ... 그리고 heading들의 값
'''
import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/4_traffic_sign_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestLoadTrafficLight:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls,'link_set')
        cls.global_info_set = cls.load_json_data(cls,'global_info')
        cls.tl_set = cls.load_json_data(cls, 'traffic_light_set')
    
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

    # --------------- Start: MGeo 메모리에 있는 `tested_tl_set`과 `traffic_light_set.json`들의 항목들을 비교한다. ---------------
    # 1
    def test_traffic_sign_idx_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['idx'] in expected_tl_set.signals
    # 2
    def test_traffic_sign_link_id_list_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['link_id_list'] == expected_tl_set.signals[self.tl_set[i]['idx']].link_id_list
    # 3
    def test_traffic_sign_road_id_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['road_id'] == expected_tl_set.signals[self.tl_set[i]['idx']].road_id
    # 4
    def test_traffic_sign_type_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['type'] == expected_tl_set.signals[self.tl_set[i]['idx']].type
    # 5
    def test_traffic_sign_sub_type_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['sub_type'] == expected_tl_set.signals[self.tl_set[i]['idx']].sub_type
    # 6
    def test_traffic_sign_dynamic_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['dynamic'] == expected_tl_set.signals[self.tl_set[i]['idx']].dynamic
    # 7
    def test_traffic_sign_orientation_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['orientation'] == expected_tl_set.signals[self.tl_set[i]['idx']].orientation
    # 8
    def test_traffic_sign_point_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['point'] == expected_tl_set.signals[self.tl_set[i]['idx']].point.tolist()
    # 9
    def test_traffic_sign_value_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['value'] == expected_tl_set.signals[self.tl_set[i]['idx']].value
    # 10
    def test_traffic_sign_country_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['country'] == expected_tl_set.signals[self.tl_set[i]['idx']].country
    # 11
    def test_traffic_sign_z_offset_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['z_offset'] == expected_tl_set.signals[self.tl_set[i]['idx']].z_offset
    # 12
    def test_traffic_sign_height_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['height'] == expected_tl_set.signals[self.tl_set[i]['idx']].height
    # 13
    def test_traffic_sign_width_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['width'] == expected_tl_set.signals[self.tl_set[i]['idx']].width
    # 14
    def test_traffic_sign_type_def_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['type_def'] == expected_tl_set.signals[self.tl_set[i]['idx']].type_def
    # 15
    def test_traffic_sign_ref_crosswalk_id_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['ref_crosswalk_id'] == expected_tl_set.signals[self.tl_set[i]['idx']].ref_crosswalk_id
    # 16
    def test_traffic_sign_heading_mgeo(self, expected_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['heading'] == expected_tl_set.signals[self.tl_set[i]['idx']].heading

    # --------------- Finish: MGeo 메모리에 있는 `tested_tl_set`과 `traffic_light_set.json`들의 항목들을 비교한다. ---------------
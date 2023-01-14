import json
import os
import pytest
import sys
import shutil

'''
Test하고 싶은 것: node_set.json안에 있는 idx, node_type, junction, point 그리고 on_stop_line들의 값
 '''

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/4_traffic_sign_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestSaveTrafficSignMGeo:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set', True)
        cls.link_set = cls.load_json_data(cls,'link_set', True)
        cls.global_info_set = cls.load_json_data(cls,'global_info', True)
        cls.ts_set = cls.load_json_data(cls, 'traffic_sign_set', True)
        cls.output_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_output_folder'))
        if not os.path.exists(cls.output_folder_path):
            os.makedirs(cls.output_folder_path, exist_ok=True)
    
    def load_json_data(self, file_name, saved_before = True):
        if not saved_before:
            test_json_file = os.path.normpath(os.path.join(self.output_folder_path, f'{file_name}.json'))
        else:
            test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
        
    @pytest.fixture
    def expected_link_set(self):
        tested_node_set, tested_link_set, tested_junction_set = load_node_and_link(self.node_set, self.link_set, self.global_info_set)
        return tested_link_set
    
    @pytest.fixture
    def expected_ts_set(self, expected_link_set):
        tested_sign_set = MGeo.load_signal_data(self.ts_set, expected_link_set)
        return tested_sign_set
    
    def test_save_mgeo_ts(self, expected_ts_set):
        return MGeo.save_traffic_sign(self.output_folder_path, expected_ts_set)
       
    @pytest.fixture
    def saved_ts_set(self):
        return self.load_json_data('traffic_sign_set', saved_before=False)
    # 1
    def test_ts_idx_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['idx'] in expected_ts_set.signals
    # 2
    def test_ts_link_id_list_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['link_id_list'] == expected_ts_set.signals[saved_ts_set[i]['idx']].link_id_list
    # 3
    def test_ts_road_id_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['road_id'] == expected_ts_set.signals[saved_ts_set[i]['idx']].road_id
    # 4
    def test_ts_type_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['type'] == expected_ts_set.signals[saved_ts_set[i]['idx']].type
    # 5
    def test_ts_sub_type_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['sub_type'] == expected_ts_set.signals[saved_ts_set[i]['idx']].sub_type
    # 6
    def test_ts_dynamic_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['dynamic'] == expected_ts_set.signals[saved_ts_set[i]['idx']].dynamic
    # 7
    def test_ts_orientation_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['orientation'] == expected_ts_set.signals[saved_ts_set[i]['idx']].orientation
    # 8
    def test_ts_point_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['point'] == expected_ts_set.signals[saved_ts_set[i]['idx']].point.tolist()
    # 9
    def test_ts_value_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['value'] == expected_ts_set.signals[saved_ts_set[i]['idx']].value
    # 10
    def test_ts_country_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['country'] == expected_ts_set.signals[saved_ts_set[i]['idx']].country
    # 11
    def test_ts_z_offset_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['z_offset'] == expected_ts_set.signals[saved_ts_set[i]['idx']].z_offset
    # 12
    def test_ts_height_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['height'] == expected_ts_set.signals[saved_ts_set[i]['idx']].height
    # 13
    def test_ts_width_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['width'] == expected_ts_set.signals[saved_ts_set[i]['idx']].width
    # 14
    def test_ts_type_def_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['type_def'] == expected_ts_set.signals[saved_ts_set[i]['idx']].type_def
    # 15
    def test_ts_ref_crosswalk_id_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['ref_crosswalk_id'] == expected_ts_set.signals[saved_ts_set[i]['idx']].ref_crosswalk_id
    # 16
    def test_ts_heading_mgeo(self, saved_ts_set, expected_ts_set):
        for i in range(len(saved_ts_set)):
            assert saved_ts_set[i]['heading'] == expected_ts_set.signals[saved_ts_set[i]['idx']].heading
    # 17
    def test_ts_idx_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['idx'] == saved_ts_set[i]['idx']
    # 18
    def test_ts_link_id_list_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['link_id_list'] == saved_ts_set[i]['link_id_list']
    # 19
    def test_ts_road_id_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['road_id'] == saved_ts_set[i]['road_id']
    # 20
    def test_ts_type_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['type'] == saved_ts_set[i]['type']
    # 21
    def test_ts_sub_type_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['sub_type'] == saved_ts_set[i]['sub_type']
    # 22
    def test_ts_dynamic_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['dynamic'] == saved_ts_set[i]['dynamic']
    # 23
    def test_ts_orientation_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['orientation'] == saved_ts_set[i]['orientation']
    # 24
    def test_ts_point_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['point'] == saved_ts_set[i]['point']
    # 25
    def test_ts_value_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['value'] == saved_ts_set[i]['value']
    # 26
    def test_ts_country_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['country'] == saved_ts_set[i]['country']
    # 27
    def test_ts_z_offset_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['z_offset'] == saved_ts_set[i]['z_offset']
    # 28
    def test_ts_height_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['height'] == saved_ts_set[i]['height']
    # 29
    def test_ts_width_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['width'] == saved_ts_set[i]['width']
    # 30
    def test_ts_type_def_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['type_def'] == saved_ts_set[i]['type_def']
    # 31
    def test_ts_ref_crosswalk_id_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['ref_crosswalk_id'] == saved_ts_set[i]['ref_crosswalk_id']
    # 32
    def test_ts_heading_json(self, saved_ts_set):
        for i in range(len(self.ts_set)):
            assert self.ts_set[i]['heading'] == saved_ts_set[i]['heading']
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.output_folder_path, ignore_errors=True)
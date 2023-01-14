import json
import os
import pytest
import sys
import shutil

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/5_traffic_light_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestSaveTrafficLightMGeo:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set', True)
        cls.link_set = cls.load_json_data(cls,'link_set', True)
        cls.global_info_set = cls.load_json_data(cls,'global_info', True)
        cls.tl_set = cls.load_json_data(cls, 'traffic_light_set', True)
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
    def expected_tl_set(self, expected_link_set):
        tested_light_set = MGeo.load_signal_data(self.tl_set, expected_link_set)
        return tested_light_set
    
    def test_save_mgeo_tl(self, expected_tl_set):
        return MGeo.save_traffic_light(self.output_folder_path, expected_tl_set)
       
    @pytest.fixture
    def saved_tl_set(self):
        return self.load_json_data('traffic_light_set', saved_before=False)
    # 1
    def test_tl_idx_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['idx'] in expected_tl_set.signals
    # 2
    def test_tl_link_id_list_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['link_id_list'] == expected_tl_set.signals[saved_tl_set[i]['idx']].link_id_list
    # 3
    def test_tl_road_id_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['road_id'] == expected_tl_set.signals[saved_tl_set[i]['idx']].road_id
    # 4
    def test_tl_type_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['type'] == expected_tl_set.signals[saved_tl_set[i]['idx']].type
    # 5
    def test_tl_sub_type_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['sub_type'] == expected_tl_set.signals[saved_tl_set[i]['idx']].sub_type
    # 6
    def test_tl_dynamic_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['dynamic'] == expected_tl_set.signals[saved_tl_set[i]['idx']].dynamic
    # 7
    def test_tl_orientation_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['orientation'] == expected_tl_set.signals[saved_tl_set[i]['idx']].orientation
    # 8
    def test_tl_point_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['point'] == expected_tl_set.signals[saved_tl_set[i]['idx']].point.tolist()
    # 9
    def test_tl_value_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['value'] == expected_tl_set.signals[saved_tl_set[i]['idx']].value
    # 10
    def test_tl_country_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['country'] == expected_tl_set.signals[saved_tl_set[i]['idx']].country
    # 11
    def test_tl_z_offset_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['z_offset'] == expected_tl_set.signals[saved_tl_set[i]['idx']].z_offset
    # 12
    def test_tl_height_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['height'] == expected_tl_set.signals[saved_tl_set[i]['idx']].height
    # 13
    def test_tl_width_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['width'] == expected_tl_set.signals[saved_tl_set[i]['idx']].width
    # 14
    def test_tl_type_def_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['type_def'] == expected_tl_set.signals[saved_tl_set[i]['idx']].type_def
    # 15
    def test_tl_ref_crosswalk_id_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['ref_crosswalk_id'] == expected_tl_set.signals[saved_tl_set[i]['idx']].ref_crosswalk_id
    # 16
    def test_tl_heading_mgeo(self, saved_tl_set, expected_tl_set):
        for i in range(len(saved_tl_set)):
            assert saved_tl_set[i]['heading'] == expected_tl_set.signals[saved_tl_set[i]['idx']].heading
    # 17
    def test_tl_idx_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['idx'] == saved_tl_set[i]['idx']
    # 18
    def test_tl_link_id_list_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['link_id_list'] == saved_tl_set[i]['link_id_list']
    # 19
    def test_tl_road_id_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['road_id'] == saved_tl_set[i]['road_id']
    # 20
    def test_tl_type_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['type'] == saved_tl_set[i]['type']
    # 21
    def test_tl_sub_type_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['sub_type'] == saved_tl_set[i]['sub_type']
    # 22
    def test_tl_dynamic_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['dynamic'] == saved_tl_set[i]['dynamic']
    # 23
    def test_tl_orientation_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['orientation'] == saved_tl_set[i]['orientation']
    # 24
    def test_tl_point_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['point'] == saved_tl_set[i]['point']
    # 25
    def test_tl_value_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['value'] == saved_tl_set[i]['value']
    # 26
    def test_tl_country_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['country'] == saved_tl_set[i]['country']
    # 27
    def test_tl_z_offset_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['z_offset'] == saved_tl_set[i]['z_offset']
    # 28
    def test_tl_height_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['height'] == saved_tl_set[i]['height']
    # 29
    def test_tl_width_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['width'] == saved_tl_set[i]['width']
    # 30
    def test_tl_type_def_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['type_def'] == saved_tl_set[i]['type_def']
    # 31
    def test_tl_ref_crosswalk_id_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['ref_crosswalk_id'] == saved_tl_set[i]['ref_crosswalk_id']
    # 32
    def test_tl_heading_json(self, saved_tl_set):
        for i in range(len(self.tl_set)):
            assert self.tl_set[i]['heading'] == saved_tl_set[i]['heading']
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.output_folder_path, ignore_errors=True)
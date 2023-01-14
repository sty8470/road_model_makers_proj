import json
import os
import pytest
import sys
import shutil

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/8_surface_marking_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestSaveSurfaceMarkingMGeo:
    
    @classmethod
    def setup_class(cls):
        
        cls.node_set = cls.load_json_data(cls,'node_set', True)
        cls.link_set = cls.load_json_data(cls,'link_set', True)
        cls.global_info_set = cls.load_json_data(cls,'global_info', True)
        cls.sm_set = cls.load_json_data(cls, 'surface_marking_set', True)
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
    def expected_sm_set(self, expected_link_set):
        tested_sm_set = MGeo.load_surface_marking_data(self.sm_set, expected_link_set)
        return tested_sm_set
        
    def test_save_mgeo_sm(self, expected_sm_set):
        return MGeo.save_surface_marking(self.output_folder_path, expected_sm_set)
    
    @pytest.fixture
    def saved_sm_data(self):
        return self.load_json_data('surface_marking_set', saved_before=False)
    # 1
    def test_sm_idx_mgeo(self, saved_sm_data, expected_sm_set):
        for i in range(len(saved_sm_data)):
            assert saved_sm_data[i]['idx'] in expected_sm_set.data
    # 2
    def test_sm_points_mgeo(self, saved_sm_data, expected_sm_set):
        for i in range(len(saved_sm_data)):
            assert saved_sm_data[i]['points'] == expected_sm_set.data[self.sm_set[i]['idx']].points.tolist()
    # 3     
    def test_sm_link_id_list_mgeo(self, saved_sm_data, expected_sm_set):
        for i in range(len(saved_sm_data)):
            assert saved_sm_data[i]['link_id_list'] == expected_sm_set.data[self.sm_set[i]['idx']].link_id_list
    # 4
    def test_sm_road_id_mgeo(self, saved_sm_data, expected_sm_set):
        for i in range(len(saved_sm_data)):
            assert saved_sm_data[i]['road_id'] == expected_sm_set.data[self.sm_set[i]['idx']].road_id
    # 5
    def test_sm_type_mgeo(self, saved_sm_data, expected_sm_set):
        for i in range(len(saved_sm_data)):
            assert saved_sm_data[i]['type'] == expected_sm_set.data[self.sm_set[i]['idx']].type
    # 6
    def test_sm_sub_type_mgeo(self, saved_sm_data, expected_sm_set):
        for i in range(len(saved_sm_data)):
            assert saved_sm_data[i]['sub_type'] == expected_sm_set.data[self.sm_set[i]['idx']].sub_type    
    # 7
    def test_sm_idx_json(self, saved_sm_data):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['idx'] == saved_sm_data[i]['idx']
    # 8
    def test_sm_points_json(self, saved_sm_data):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['points'] == saved_sm_data[i]['points']
    # 9
    def test_sm_link_id_list_json(self, saved_sm_data):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['link_id_list'] == saved_sm_data[i]['link_id_list']
    # 10
    def test_sm_road_id_json(self, saved_sm_data):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['road_id'] == saved_sm_data[i]['road_id']
    # 11
    def test_sm_type_json(self, saved_sm_data):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['type'] == saved_sm_data[i]['type']
    # 12
    def test_sm_sub_type_json(self, saved_sm_data):
        for i in range(len(self.sm_set)):
            assert self.sm_set[i]['sub_type'] == saved_sm_data[i]['sub_type']
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.output_folder_path, ignore_errors=True)
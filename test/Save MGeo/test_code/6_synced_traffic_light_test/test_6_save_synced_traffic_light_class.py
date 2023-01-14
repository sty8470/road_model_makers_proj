import json
import os
import pytest
import sys
import shutil

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/6_synced_traffic_light_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestSaveSyncedTrafficLightMGeo:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set', True)
        cls.link_set = cls.load_json_data(cls,'link_set', True)
        cls.global_info_set = cls.load_json_data(cls,'global_info', True)
        cls.tl_set = cls.load_json_data(cls, 'traffic_light_set', True)
        cls.synced_tl_set = cls.load_json_data(cls, 'synced_traffic_light_set', True)
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
    
    @pytest.fixture
    def expected_synced_tl_set(self, expected_link_set, expected_tl_set):
        tested_synced_light_set = MGeo.load_synced_traffic_light_data(self.synced_tl_set, expected_link_set, expected_tl_set)
        return tested_synced_light_set
    
    def test_save_mgeo_synced_tl(self, expected_synced_tl_set):
        return MGeo.save_synced_traffic_light(self.output_folder_path, expected_synced_tl_set)
       
    @pytest.fixture
    def saved_synced_tl_set(self):
        return self.load_json_data('synced_traffic_light_set', saved_before=False)
    # 1
    def test_synced_tl_idx_mgeo(self, saved_synced_tl_set, expected_synced_tl_set):
        for i in range(len(saved_synced_tl_set)):
            assert saved_synced_tl_set[i]['idx'] in expected_synced_tl_set.synced_signals
    # 2
    def test_synced_tl_link_id_list_mgeo(self, saved_synced_tl_set, expected_synced_tl_set):
        for i in range(len(saved_synced_tl_set)):
            assert saved_synced_tl_set[i]['link_id_list'] == expected_synced_tl_set.synced_signals[saved_synced_tl_set[i]['idx']].link_id_list
    # 3
    def test_synced_tl_point_mgeo(self, saved_synced_tl_set, expected_synced_tl_set):
        for i in range(len(saved_synced_tl_set)):
            assert saved_synced_tl_set[i]['point'] == expected_synced_tl_set.synced_signals[saved_synced_tl_set[i]['idx']].point.tolist()
    # 4
    def test_synced_tl_intersection_controller_id_mgeo(self, saved_synced_tl_set, expected_synced_tl_set):
        for i in range(len(saved_synced_tl_set)):
            assert saved_synced_tl_set[i]['intersection_controller_id'] == expected_synced_tl_set.synced_signals[saved_synced_tl_set[i]['idx']].intersection_controller_id
    # 5
    def test_synced_tl_signal_id_list_mgeo(self, saved_synced_tl_set, expected_synced_tl_set):
        for i in range(len(saved_synced_tl_set)):
            assert saved_synced_tl_set[i]['signal_id_list'] == expected_synced_tl_set.synced_signals[saved_synced_tl_set[i]['idx']].signal_id_list
    # 6
    def test_synced_tl_idx_json(self, saved_synced_tl_set):
        for i in range(len(self.synced_tl_set)):
            assert self.synced_tl_set[i]['idx'] == saved_synced_tl_set[i]['idx']
    # 7
    def test_synced_tl_link_id_list_json(self, saved_synced_tl_set):
        for i in range(len(self.synced_tl_set)):
            assert self.synced_tl_set[i]['link_id_list'] == saved_synced_tl_set[i]['link_id_list']
    # 8
    def test_synced_tl_point_json(self, saved_synced_tl_set):
        for i in range(len(self.synced_tl_set)):
            assert self.synced_tl_set[i]['point'] == saved_synced_tl_set[i]['point']
    # 9
    def test_synced_tl_intersection_controller_id_json(self, saved_synced_tl_set):
        for i in range(len(self.synced_tl_set)):
            assert self.synced_tl_set[i]['intersection_controller_id'] == saved_synced_tl_set[i]['intersection_controller_id']
    # 10
    def test_synced_tl_signal_id_list_json(self, saved_synced_tl_set):
        for i in range(len(self.synced_tl_set)):
            assert self.synced_tl_set[i]['signal_id_list'] == saved_synced_tl_set[i]['signal_id_list']
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.output_folder_path, ignore_errors=True)
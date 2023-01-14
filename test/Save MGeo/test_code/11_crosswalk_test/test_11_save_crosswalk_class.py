import json
import os
import pytest
import sys
import shutil

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/11_crosswalk_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestSaveCrosswalkMGeo:
    
    @classmethod
    def setup_class(cls):
        
        cls.node_set = cls.load_json_data(cls,'node_set', True)
        cls.link_set = cls.load_json_data(cls,'link_set', True)
        cls.global_info_set = cls.load_json_data(cls,'global_info', True)
        cls.tl_set = cls.load_json_data(cls, 'traffic_light_set', True)
        cls.cw_set = cls.load_json_data(cls, 'crosswalk_set')
        cls.scw_set = cls.load_json_data(cls, 'singlecrosswalk_set')
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
    def saved_cw_set(self):
        return self.load_json_data('crosswalk_set', saved_before=False)
    
    def test_save_mgeo_cw(self, expected_cw_set):
        return MGeo.save_crosswalk(self.output_folder_path, expected_cw_set)
    # 1
    def test_cw_idx_mgeo(self, saved_cw_set, expected_cw_set):
        for i in range(len(saved_cw_set)):
            assert saved_cw_set[i]['idx'] in expected_cw_set.data
    # 2
    def test_cw_single_crosswalk_list_mgeo(self, saved_cw_set, expected_cw_set):
        for i in range(len(saved_cw_set)):
            for j in range(len(saved_cw_set[i]['single_crosswalk_list'])):
                assert saved_cw_set[i]['single_crosswalk_list'][j] == expected_cw_set.data[saved_cw_set[i]['idx']].single_crosswalk_list[j].idx
    # 3
    def test_cw_ref_traffic_light_list_mgeo(self, saved_cw_set, expected_cw_set):
        for i in range(len(saved_cw_set)):
            for j in range(len(saved_cw_set[i]['ref_traffic_light_list'])):
                assert saved_cw_set[i]['ref_traffic_light_list'][j] == expected_cw_set.data[saved_cw_set[i]['idx']].ref_traffic_light_list[j].idx
    # 4
    def test_cw_idx_json(self, saved_cw_set):
        for i in range(len(self.cw_set)):
            assert self.cw_set[i]['idx'] == saved_cw_set[i]['idx']
    # 5
    def test_cw_single_crosswalk_list_json(self, saved_cw_set):
        for i in range(len(self.cw_set)):
            assert self.cw_set[i]['single_crosswalk_list'] == saved_cw_set[i]['single_crosswalk_list']
    # 6
    def test_cw_ref_traffic_light_list_json(self, saved_cw_set):
        for i in range(len(self.cw_set)):
            assert self.cw_set[i]['ref_traffic_light_list'] == saved_cw_set[i]['ref_traffic_light_list']
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.output_folder_path, ignore_errors=True)
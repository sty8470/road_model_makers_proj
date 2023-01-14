import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/10_single_crosswalk_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestSaveCrosswalkMGeo:
    
    @classmethod
    def setup_class(cls):
        cls.scw_set = cls.load_json_data(cls, 'singlecrosswalk_set')
    
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
    
    @pytest.fixture
    def expected_scw_set(self):
        tested_scw_set = MGeo.load_single_crosswalk_data(self.scw_set)
        return tested_scw_set

    # --------------- Start: MGeo 메모리에 있는 `expected_scw_set`과 `singlecrosswalk_set.json`들의 항목들을 비교한다. ----------------
    # 1
    def test_scw_idx_mgeo(self, expected_scw_set):
        for i in range(len(self.scw_set)):
            assert self.scw_set[i]['idx'] in expected_scw_set.data
    # 2
    def test_scw_points_mgeo(self, expected_scw_set):
        for i in range(len(self.scw_set)):
            assert self.scw_set[i]['points'] == expected_scw_set.data[self.scw_set[i]['idx']].points
    # 3     
    def test_scw_sign_type_mgeo(self, expected_scw_set):
        for i in range(len(self.scw_set)):
            assert self.scw_set[i]['sign_type'] == expected_scw_set.data[self.scw_set[i]['idx']].sign_type
    # 4
    def test_scw_ref_crosswalk_id_mgeo(self, expected_scw_set):
        for i in range(len(self.scw_set)):
            assert self.scw_set[i]['ref_crosswalk_id'] == expected_scw_set.data[self.scw_set[i]['idx']].ref_crosswalk_id
    # 5
    def test_scw_link_id_list_mgeo(self, expected_scw_set):
        for i in range(len(self.scw_set)):
            assert self.scw_set[i]['link_id_list'] == expected_scw_set.data[self.scw_set[i]['idx']].link_id_list
            
    # --------------- Finish: MGeo 메모리에 있는 `expected_scw_set`과 `singlecrosswalk_set.json`들의 항목들을 비교한다. ----------------
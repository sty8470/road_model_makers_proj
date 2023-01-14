'''
Test하고 싶은 것(2개): intersection_controller_set.json안에 있는 idx와 TL들의 값
'''
import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/7_intersection_controller_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestLoadIntersectionController:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls,'link_set')
        cls.global_info_set = cls.load_json_data(cls,'global_info')
        cls.tl_set = cls.load_json_data(cls, 'traffic_light_set')
        cls.ic_set = cls.load_json_data(cls, 'intersection_controller_set')

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
        tested_light_set = MGeo.load_signal_data(self.tl_set, expected_link_set)
        return tested_light_set
    
    @pytest.fixture
    def expected_ic_set(self, expected_tl_set):
        tested_ic_set = MGeo.load_intersection_controller_data(self.ic_set, expected_tl_set)
        return tested_ic_set

    # --------------- Start: MGeo 메모리에 있는 `expected_ic_set`과 `intersection_controller_set.json`들의 항목들을 비교한다. ---------------
    # 1
    def test_intersection_controller_idx_mgeo(self, expected_ic_set):
        for i in range(len(self.ic_set)):
            assert self.ic_set[i]['idx'] in expected_ic_set.intersection_controllers
    # 2
    def test_intersection_controller_tl_mgeo(self, expected_ic_set):
        for i in range(len(self.ic_set)):
            assert self.ic_set[i]['TL'] == expected_ic_set.intersection_controllers[self.ic_set[i]['idx']].TL
    
    # --------------- Finish: MGeo 메모리에 있는 `expected_ic_set`과 `intersection_controller_set.json`들의 항목들을 비교한다. ---------------
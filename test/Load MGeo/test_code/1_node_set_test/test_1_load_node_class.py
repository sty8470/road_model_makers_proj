'''
Test하고 싶은 것(5개): node_set.json안에 있는 idx, node_type, junction, point 그리고 on_stop_line들의 값
'''
import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/1_node_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestLoadNode:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls,'link_set')
        cls.global_info_set = cls.load_json_data(cls,'global_info')
    
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
        
    @pytest.fixture
    def expected_node_set(self):
        tested_node_set, tested_link_set, tested_junction_set = load_node_and_link(self.node_set, self.link_set, self.global_info_set)
        return tested_node_set

    # --------------- Start: MGeo 메모리에 있는 `tested_node_set`과 `node_set.json`들의 항목들을 비교한다. ---------------
    # 1
    def test_node_idx_mgeo(self, expected_node_set):
        for i in range(len(self.node_set)):
            assert self.node_set[i]['idx'] in expected_node_set.nodes
    # 2
    def test_node_type_mgeo(self, expected_node_set):
        for i in range(len(self.node_set)):
            assert self.node_set[i]['node_type'] == expected_node_set.nodes[self.node_set[i]['idx']].node_type
    # 3
    def test_node_junctions_mgeo(self, expected_node_set):
        for i in range(len(self.node_set)):
            assert self.node_set[i]['junction'] == expected_node_set.nodes[self.node_set[i]['idx']].junctions
    # 4
    def test_node_point_mgeo(self, expected_node_set):
        for i in range(len(self.node_set)):
            assert self.node_set[i]['point'] == expected_node_set.nodes[self.node_set[i]['idx']].point.tolist()
    # 5
    def test_node_on_stop_line_mgeo(self, expected_node_set):
        for i in range(len(self.node_set)):
            assert self.node_set[i]['on_stop_line'] == expected_node_set.nodes[self.node_set[i]['idx']].on_stop_line

    # --------------- Finish: MGeo 메모리에 있는 `tested_node_set`과 `node_set.json`들의 항목들을 비교한다. ---------------
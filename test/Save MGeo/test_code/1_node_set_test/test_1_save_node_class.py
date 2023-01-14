import json
import os
import pytest
import sys
import shutil

'''
Test하고 싶은 것: node_set.json안에 있는 idx, node_type, junction, point 그리고 on_stop_line들의 값
 '''

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/1_node_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestSaveNodeMGeo:
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set', True)
        cls.link_set = cls.load_json_data(cls,'link_set', True)
        cls.global_info_set = cls.load_json_data(cls,'global_info', True)
        
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
    def expected_node_set(self):
        tested_node_set, tested_link_set, tested_junction_set = load_node_and_link(self.node_set, self.link_set, self.global_info_set)
        return tested_node_set
    
    def test_save_mgeo_node(self, expected_node_set):
        return MGeo.save_node(self.output_folder_path, expected_node_set)
    
    @pytest.fixture
    def saved_node_set(self):
        return self.load_json_data('node_set', saved_before=False)
    
    # --------------- Start: MGeo 메모리에 있는 `tested_node_set`과 `saved_node_set.json`들의 항목들을 비교한다. ---------------
    # 1
    def test_node_idx_mgeo(self, saved_node_set, expected_node_set):
        for i in range(len(saved_node_set)):
            assert saved_node_set[i]['idx'] in expected_node_set.nodes
    # 2       
    def test_node_type_mgeo(self, saved_node_set, expected_node_set):
        for i in range(len(saved_node_set)):
            assert saved_node_set[i]['node_type'] == expected_node_set.nodes[saved_node_set[i]['idx']].node_type
    # 3        
    def test_node_junction_mgeo(self, saved_node_set, expected_node_set):
        for i in range(len(saved_node_set)):
            assert saved_node_set[i]['junction'] == expected_node_set.nodes[saved_node_set[i]['idx']].junctions
    # 4
    def test_node_point_mgeo(self, saved_node_set, expected_node_set):
        for i in range(len(saved_node_set)):
            assert saved_node_set[i]['point'] == expected_node_set.nodes[saved_node_set[i]['idx']].point.tolist()
    # 5
    def test_node_no_stop_line_mgeo(self, saved_node_set, expected_node_set):
        for i in range(len(saved_node_set)):
            assert saved_node_set[i]['on_stop_line'] == expected_node_set.nodes[saved_node_set[i]['idx']].on_stop_line
    
    # --------------- Finish: MGeo 메모리에 있는 `tested_node_set`과 `saved_node_set.json`들의 항목들을 비교한다. ---------------
    
    
    
    # --------------- Start: 원래있던 `node_set.json`과 저장된 `saved_node_set.json`과 들의 항목들을 비교한다. ---------------
    # 6
    def test_node_idx_json(self, saved_node_set):
        for i in range(len(self.node_set)):
            assert self.node_set[i]['idx'] == saved_node_set[i]['idx']    
    # 7
    def test_node_type_json(self, saved_node_set):
        for i in range(len(self.node_set)):
            assert self.node_set[i]['node_type'] == saved_node_set[i]['node_type']
    # 8
    def test_node_junction_json(self, saved_node_set):
        for i in range(len(self.node_set)):
            assert self.node_set[i]['junction'] == saved_node_set[i]['junction']
    # 9
    def test_point_json(self, saved_node_set):
        for i in range(len(self.node_set)):
            assert self.node_set[i]['point'] == saved_node_set[i]['point']
    # 10
    def test_on_stop_line_json(self, saved_node_set):
        for i in range(len(self.node_set)):
            assert self.node_set[i]['on_stop_line'] == saved_node_set[i]['on_stop_line']  
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.output_folder_path, ignore_errors=True)
    
    # --------------- Finish: 원래있던 `node_set.json`과 저장된 `saved_node_set.json`과 들의 항목들을 비교한다. ---------------
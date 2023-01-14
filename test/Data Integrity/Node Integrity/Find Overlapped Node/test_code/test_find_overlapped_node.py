import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Find Overlapped Node/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)


from lib.mgeo.utils.error_fix import search_overlapped_node
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestFindOverlappedNode:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls, 'link_set')
        cls.global_info_set = cls.load_json_data(cls, 'global_info')
        cls.dist_threshold = 1.2
    
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
    
    @pytest.fixture
    def expected_node_set(self):
        tested_node_set, tested_link_set, tested_junction_set = load_node_and_link(self.node_set, self.link_set, self.global_info_set)
        return tested_node_set
    
    @pytest.fixture
    def expected_searched_overlapped_node(self, expected_node_set):
        return search_overlapped_node(expected_node_set, self.dist_threshold)
    

    # @pytest.fixture
    # def mock_app(self, qtbot):
    #     test_ui = EditGeolocation(self.old_origin)
    #     test_ui.showDialog()
    #     qtbot.addWidget(test_ui)
    #     return test_ui

    # --------------- Start: `MGeo 메모리안에서 load된 2개의 overlapped Node가 search_overlapped_node 함수를 거쳐서 return되는 overlapped Node들과 일치한지 검사한다---------------    # 1
    def test_searched_overlapped_node(self, expected_node_set, expected_searched_overlapped_node):
        for i in range(len(expected_node_set.nodes)):
            assert expected_node_set.nodes[self.node_set[i]['idx']] == expected_searched_overlapped_node[0][i]
    
    # --------------- Finish: `MGeo 메모리안에서 load된 2개의 overlapped Node가 search_overlapped_node 함수를 거쳐서 return되는 overlapped Node들과 일치한지 검사한다---------------
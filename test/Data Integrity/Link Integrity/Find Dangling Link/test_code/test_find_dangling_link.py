import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Find Dangling Link/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

# E:\road_model_maker\src\lib\mgeo\utils
# from lib.mgeo.edit.funcs.edit_mgeo_planner_map import change_origin
# from lib.widget.edit_geolocation import EditGeolocation
# from lib.mgeo.class_defs.mgeo import MGeo

from lib.mgeo.utils.error_fix import find_dangling_links
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestFindDanglingLink:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.link_set = cls.load_json_data(cls, 'link_set')
        cls.global_info_set = cls.load_json_data(cls, 'global_info')
    
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
    def expected_find_dangling_links(self, expected_link_set):
        return find_dangling_links(expected_link_set)
    
    # @pytest.fixture
    # def mock_app(self, qtbot):
    #     test_ui = EditGeolocation(self.old_origin)
    #     test_ui.showDialog()
    #     qtbot.addWidget(test_ui)
    #     return test_ui

    # --------------- Start: `find_dangling_links 함수를 거친 2개의 dangling links가 MGeo 메모리안에 존재하는 2개의 dangling link들과 일치한지 비교한다. ---------------
    # 1
    def test_find_dangling_link_1(self, expected_link_set, expected_find_dangling_links):
        assert expected_link_set.lines['to_missing'] == expected_find_dangling_links[0]
    # 2
    def test_find_dangling_node_2(self, expected_link_set, expected_find_dangling_links):
        assert expected_link_set.lines['from_missing'] == expected_find_dangling_links[1]
        
    # --------------- Start: `find_dangling_links 함수를 거친 2개의 dangling links가 MGeo 메모리안에 존재하는 2개의 dangling link들과 일치한지 비교한다. ---------------
import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Find Mismatch Lange Change Link/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from proj_mgeo_editor_morai_opengl.GUI.feature_sets_error_fix import ErrorFix
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestFindMismatchLaneChangeLink:
    
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
    def expected_mismatch_lane_change_link(self, expected_link_set):
        return ErrorFix.find_mismatch_lane_change(expected_link_set)
    
    # @pytest.fixture
    # def mock_app(self, qtbot):
    #     test_ui = EditGeolocation(self.old_origin)
    #     test_ui.showDialog()
    #     qtbot.addWidget(test_ui)
    #     return test_ui

    # --------------- Start: `find_dangling_links 함수를 거친 2개의 dangling links가 MGeo 메모리안에 존재하는 2개의 dangling link들과 일치한지 비교한다. ---------------
    # 1
    def test_find_mismatch_lane_change_link(self, expected_link_set, expected_mismatch_lane_change_link):
        assert expected_link_set.lines == expected_mismatch_lane_change_link[0]
        
    # --------------- Start: `find_dangling_links 함수를 거친 2개의 dangling links가 MGeo 메모리안에 존재하는 2개의 dangling link들과 일치한지 비교한다. ---------------
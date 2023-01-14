import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Change World Origin/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.edit.funcs.edit_mgeo_planner_map import change_origin
# from lib.widget.edit_geolocation import EditGeolocation
from lib.mgeo.class_defs.mgeo import MGeo

class TestChangeWorldOrigin:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.mgeo_planner_map = MGeo.create_instance_from_json(test_data_folder_path)
        cls.old_origin = [-7.081154551613622e-10, -7.081154551613622e-10, 0.0]
        cls.new_origin = [200, 200, 0.0]
        cls.global_info = cls.load_json_data(cls, 'global_info')
        cls.is_retain_global_position = True
        cls.moved_node_1_point = [-199.00000000070813, -199.00000000070813, 1.0]
        cls.moved_node_2_point = [-198.00000000070813, -198.00000000070813, 2.0]

    
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
    
    @pytest.fixture
    def expected_world_origin(self):
        return change_origin(self.mgeo_planner_map, self.new_origin, self.is_retain_global_position)
    
    # @pytest.fixture
    # def mock_app(self, qtbot):
    #     test_ui = EditGeolocation(self.old_origin)
    #     test_ui.showDialog()
    #     qtbot.addWidget(test_ui)
    #     return test_ui

    # --------------- Start: `change_origin 함수를 거친 new_origin이 mgeo_planner_map에 있는 변경된 local_origin_in_global과 동일한지 비교한다 ---------------
    # 1
    # 최종 origin이 어디로 옮겨졌는지 ..
    def test_changed_origin(self, expected_world_origin):
        assert self.mgeo_planner_map.local_origin_in_global.tolist() == self.new_origin
    # --------------- Finish: `change_origin 함수를 거친 new_origin이 mgeo_planner_map에 있는 변경된 local_origin_in_global과 동일한지 비교한다 ---------------
    
    
    # --------------- Start: `tested_node_set`에 있는 node 2개들이 change_world_position 함수를 거치고 `node_set.json`들의 항목들과 비교한다. ---------------
    # 2
    def test_changed_node_1_point(self, expected_world_origin):
        assert self.mgeo_planner_map.node_set.nodes[self.node_set[0]['idx']].point.tolist() == self.moved_node_1_point
    
    # 3
    def test_changed_node_2_point(self, expected_world_origin):
        assert self.mgeo_planner_map.node_set.nodes[self.node_set[1]['idx']].point.tolist() == self.moved_node_2_point
    # --------------- Finish: `tested_node_set`에 있는 node 2개들이 change_world_position 함수를 거치고 `node_set.json`들의 항목들과 비교한다. ---------------
    
    # --------------- Start: 사용자가 EditGeolocation UI에 나타나는 value들을 설정후에 OK버튼을 누른뒤 저장되는 값들을 체크한다---------------
    # # 4
    # def test_changed_retain_global_position(self, mock_app):
    #     assert self.is_retain_global_position == mock_app.isRetainGlobalPosition
    
    # # 5
    # def test_changed_location(self, mock_app):
    #     assert self.new_origin == list(map(int, mock_app.coordText.split(',')))
    # --------------- Finish: 사용자가 EditGeolocation UI에 나타나는 value들을 설정후에 OK버튼을 누른뒤 저장되는 값들을 체크한다---------------
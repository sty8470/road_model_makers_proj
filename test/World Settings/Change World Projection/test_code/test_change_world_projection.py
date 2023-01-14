import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Change World Projection/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.edit.funcs.edit_mgeo_planner_map import change_world_projection
from lib.widget.edit_change_world_projection import EditChangeWorldProjection
from lib.mgeo.class_defs.mgeo import MGeo

class TestChangeWorldProjection:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set')
        cls.mgeo_planner_map = MGeo.create_instance_from_json(test_data_folder_path)
        cls.is_retain_global_position = True
        cls.is_not_retain_global_position = True
        cls.projection_type_proj4 = 'proj4'
        cls.projection_type_utm = 'utm'
        cls.projection_type_tmerc_params = 'tmerc params'
        cls.projection_type_undefined = 'undefined'
        cls.proj4_string = '+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +units=m +no_defs'
        cls.changed_node_1_point = [-1.651538827456534, 39991858.12021591, 1.0]
        cls.changed_node_2_point = [-3.303077654913068, 39991856.46867605, 2.0]
            
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data
    
    @pytest.fixture
    def expected_world_projection(self):
        return change_world_projection(self.mgeo_planner_map, self.proj4_string)
    
    # @pytest.fixture
    # def mock_app(self, qtbot):
    #     test_ui = EditChangeWorldProjection(self.proj4_string)
    #     test_ui.showDialog()
    #     qtbot.addWidget(test_ui)
    #     return test_ui
    
    # def run_mock_app(self, mock_app):
    #     mock_app

    # --------------- Start: `node_set.json`에 있는 node 2개들이 change_world_position 함수를 거치고난 후 변경되어서 출력되는 값들과 비교한다. ---------------    # 1
    # 1
    def test_changed_node_1_point(self, expected_world_projection):
        assert self.mgeo_planner_map.node_set.nodes[self.node_set[0]['idx']].point.tolist() == self.changed_node_1_point
    
    # 2
    def test_changed_node_2_point(self, expected_world_projection):
        assert self.mgeo_planner_map.node_set.nodes[self.node_set[1]['idx']].point.tolist() == self.changed_node_2_point
            
    # --------------- Finish: `node_set.json`에 있는 node 2개들이 change_world_position 함수를 거치고난 후 변경되어서 출력되는 값들과 비교한다. ---------------

    # --------------- Start: 사용자가 EditChangeWorldProjection UI에 나타나는 value들을 설정후에 OK버튼을 누른뒤 저장되는 값들을 체크한다---------------
    # #3
    # def test_changed_retain_global_position(self, mock_app):
    #     assert self.is_retain_global_position == mock_app.isRetainGlobalPosition
    # #4
    # def test_changed_projection_type(self, mock_app):
    #     assert self.projection_type_proj4 == mock_app.projectionType
    # #5
    # def test_changed_proj4_string(self, mock_app):
    #     assert self.proj4_string == mock_app.proj4String
    
    # --------------- Finish: 사용자가 EditChangeWorldProjection UI에 나타나는 value들을 설정후에 OK버튼을 누른뒤 저장되는 값들을 체크한다---------------
   
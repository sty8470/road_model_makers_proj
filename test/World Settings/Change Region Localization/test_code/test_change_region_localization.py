import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../Change Region Localization/test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.widget.edit_change_region_localization import EditChangeRegionLocalization
from proj_mgeo_editor_morai_opengl.GUI.opengl_canvas import OpenGLCanvas
from lib.mgeo.class_defs.mgeo import MGeo

class TestChangeRegionLocalization:
    '''
    EditChangeRegionLocalization에서 User가 넣어주는 input을 미리 정의해서, 그 Widget Class에 넣어준 뒤에, 
    OpenGLCanvas.change_region_localization 함수가 실행되었을때, 그 값이 잘 들어왔는지 확인한다
    '''
    
    @classmethod
    def setup_class(cls):
        cls.mgeo_planner_map = MGeo.create_instance_from_json(test_data_folder_path)
        cls.traffic_dir = 'RHT'
        cls.country = 'Korea, Republic of'
        cls.road_type = 'town'
        cls.road_type_def = 'OpenDRIVE'
    
    @pytest.fixture
    def mock_app(self, qtbot):
        test_ui = EditChangeRegionLocalization(self.mgeo_planner_map)
        test_ui.showDialog()
        qtbot.addWidget(test_ui)
        return test_ui


    # --------------- Start: `EditChangeRegionLocalization`에서 유저가 입력한 traffic_dir, country, road_type, 그리고 road_type_def의 값들이 잘 들어왔는지 확인한다. ---------------
    # # 1
    # def test_changed_traffic_dir(self, mock_app):
    #     assert self.traffic_dir == mock_app.traffic_dir
    # # 2
    # def test_changed_country(self, mock_app):
    #     assert self.country == mock_app.country
    # # 3
    # def test_changed_road_type(self, mock_app):
    #     assert self.road_type == mock_app.road_type    
    # # 4
    # def test_changed_road_type_def(self, mock_app):
    #     assert self.road_type_def == mock_app.road_type_def

    # --------------- Finish: `EditChangeRegionLocalization`에서 유저가 입력한 traffic_dir, country, road_type, 그리고 road_type_def의 값들이 잘 들어왔는지 확인한다. ---------------

import json
import os
import pytest
import sys
import time

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../test_data/'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from proj_mgeo_editor_morai_opengl.mgeo_odr_converter import MGeoToOdrDataConverter

class TestCreateRoadPreliminary:
    
    @classmethod
    def setup_class(cls):
        cls.odr_data_roads = {'4000000': 1, '4000001': 2, '4000002': 3, '4000015':4, '4000003': 5, '4000008': 6}
    
    @pytest.fixture
    def expected_mgeo_obj(self):
        return MGeo.create_instance_from_json(test_data_folder_path)
 
    @pytest.fixture 
    def expected_odr_data(self, expected_mgeo_obj):
        return MGeoToOdrDataConverter.create_preliminary_odr_roads(self, expected_mgeo_obj)
    
    ############################################################################################################
    # # --------------- Start: MGeo 데이터의 id 값이 유저입력으로부터 ID를 받아서 찾을 MGeo 인스턴스의 id값과 같은지 확인한다.  ---------------
    # 1
    
    def test_odr_data(self, expected_odr_data):
        assert '4000000' in expected_odr_data.roads
    
    # # --------------- Finish: MGeo 데c이터의 Junction의 id 값이 유저입력으로부터 Junction ID를 받아서 찾을 Junction의 인스턴스의 id값과 같은지 확인한다.  ---------------
 
   
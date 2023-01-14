'''
Test하고 싶은 것(5개): intersection_controller_data.json안에 있는 idx, TLState의 duration, lightcolor, yellowduration과 PSState의 값 
'''
import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/8_intersection_controller_data'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo

class TestSaveIntersectionControllerDataMGeo:
    
    @classmethod
    def setup_class(cls):
        cls.ic_data = cls.load_json_data(cls, 'intersection_controller_data')
    
    def load_json_data(self, file_name):
        test_json_file = os.path.normpath(os.path.join(test_data_folder_path, f'{file_name}.json'))
        with open(test_json_file) as data:
            json_data = json.load(data)
            return json_data

    @pytest.fixture
    def expected_ic_data(self):
        tested_ic_data = MGeo.load_intersection_controller_state_data(self.ic_data)
        return tested_ic_data

    # --------------- Start: MGeo 메모리에 있는 `expected_ic_data`과 `intersection_controller_data.json`들의 항목들을 비교한다. ---------------
    # 1
    def test_ic_data_idx_mgeo(self, expected_ic_data):
        for i in range(len(self.ic_data)):
            assert self.ic_data[i]['idx'] in expected_ic_data
    # 2
    def test_intersection_controller_TLState_duration_mgeo(self, expected_ic_data):
        for i in range(len(self.ic_data)):
            for j in range(len(self.ic_data[i]['TLState'])):
                assert self.ic_data[i]['TLState'][j]['duration'] == expected_ic_data[self.ic_data[i]['idx']]['TLState'][j]['duration']
    # 3
    def test_intersection_controller_TLState_lightcolor_mgeo(self, expected_ic_data):
        for i in range(len(self.ic_data)):
                for j in range(len(self.ic_data[i]['TLState'])):
                    assert self.ic_data[i]['TLState'][j]['lightcolor'] == expected_ic_data[self.ic_data[i]['idx']]['TLState'][j]['lightcolor']
    # 4
    def test_intersection_controller_yelloduration_mgeo(self, expected_ic_data):
        for i in range(len(self.ic_data)):
            self.ic_data[i]['yelloduration'] == expected_ic_data[self.ic_data[i]['idx']]['yelloduration']
    # 5
    def test_intersection_controller_PSState_mgeo(self, expected_ic_data):
        for i in range(len(self.ic_data)):
            self.ic_data[i]['PSState'] == expected_ic_data[self.ic_data[i]['idx']]['PSState']

    # --------------- Start: MGeo 메모리에 있는 `expected_ic_data`과 `intersection_controller_data.json`들의 항목들을 비교한다. ---------------
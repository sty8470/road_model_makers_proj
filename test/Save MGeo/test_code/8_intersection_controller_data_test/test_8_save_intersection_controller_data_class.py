import json
import os
import pytest
import sys
import shutil

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
        cls.ic_data = cls.load_json_data(cls, 'intersection_controller_data', True)
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
    def expected_ic_data(self):
        tested_ic_data = MGeo.load_intersection_controller_state_data(self.ic_data)
        return tested_ic_data
    
    def test_save_mgeo_ic(self, expected_ic_data):
        return MGeo.save_intersection_state(self.output_folder_path, expected_ic_data)
       
    @pytest.fixture
    def saved_ic_data(self):
        return self.load_json_data('intersection_controller_data', saved_before=False)
    # 1
    def test_ic_data_idx_mgeo(self, saved_ic_data, expected_ic_data):
        for i in range(len(saved_ic_data)):
            assert saved_ic_data[i]['idx'] in expected_ic_data
    # 2
    def test_ic_TLState_duration_mgeo(self, saved_ic_data, expected_ic_data):
        for i in range(len(saved_ic_data)):
            for j in range(len(saved_ic_data[i]['TLState'])):
                assert saved_ic_data[i]['TLState'][j]['duration'] == expected_ic_data[saved_ic_data[i]['idx']]['TLState'][j]['duration']
    # 3
    def test_ic_TLState_lightcolor_mgeo(self, saved_ic_data, expected_ic_data):
        for i in range(len(saved_ic_data)):
            for j in range(len(saved_ic_data[i]['TLState'])):
                assert saved_ic_data[i]['TLState'][j]['lightcolor'] == expected_ic_data[saved_ic_data[i]['idx']]['TLState'][j]['lightcolor']
    # 4
    def test_ic_yellowduration_mgeo(self, saved_ic_data, expected_ic_data):
         for i in range(len(saved_ic_data)):
            assert saved_ic_data[i]['yelloduration'] == expected_ic_data[saved_ic_data[i]['idx']]['yelloduration']
    # 5
    def test_ic_PSState_mgeo(self, saved_ic_data, expected_ic_data):
         for i in range(len(saved_ic_data)):
            assert saved_ic_data[i]['PSState'] == expected_ic_data[saved_ic_data[i]['idx']]['PSState']
    # 6
    def test_ic_data_idx_json(self, saved_ic_data):
        for i in range(len(self.ic_data)):
            assert self.ic_data[i]['idx'] == saved_ic_data[i]['idx']
    # 7
    def test_ic_TLState_duration_json(self, saved_ic_data):
        for i in range(len(self.ic_data)):
            for j in range(len(self.ic_data[i]['TLState'])):
                assert self.ic_data[i]['TLState'][j]['duration'] == saved_ic_data[i]['TLState'][j]['duration']
    # 8
    def test_ic_TLState_lightcolor_json(self, saved_ic_data):
        for i in range(len(self.ic_data)):
            for j in range(len(self.ic_data[i]['TLState'])):
                assert self.ic_data[i]['TLState'][j]['lightcolor'] == saved_ic_data[i]['TLState'][j]['lightcolor']
    # 9
    def test_ic_yellowduration_json(self, saved_ic_data):
         for i in range(len(self.ic_data)):
            assert self.ic_data[i]['yelloduration'] == saved_ic_data[i]['yelloduration']
    # 10
    def test_ic_PSState_json(self, saved_ic_data):
         for i in range(len(self.ic_data)):
            assert self.ic_data[i]['PSState'] == saved_ic_data[i]['PSState']           
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.output_folder_path, ignore_errors=True)
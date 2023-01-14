import json
import os
import pytest
import sys
import shutil

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/3_lane_boundary_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo

class TestSaveLaneBoundaryMGeo:
    
    @classmethod
    def setup_class(cls):
        cls.lane_node_set = cls.load_json_data(cls, 'lane_node_set', True)
        cls.lane_boundary_set = cls.load_json_data(cls, 'lane_boundary_set',True)
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
    def expected_lane_node_set(self):
        tested_lane_set, tested_node_set = MGeo.load_lane_boundary_data(self.lane_node_set, self.lane_boundary_set)
        return tested_node_set
    
    @pytest.fixture
    def expected_lane_boundary_set(self):
        tested_lane_set, tested_node_set = MGeo.load_lane_boundary_data(self.lane_node_set, self.lane_boundary_set)
        return tested_lane_set
    
    def test_save_lane_node_set(self, expected_lane_node_set):
        return MGeo.save_lane_node(self.output_folder_path, expected_lane_node_set)
    
    def test_save_lane_boundary_set(self, expected_lane_boundary_set):
        return MGeo.save_lane_boundary(self.output_folder_path, expected_lane_boundary_set)
    
    @pytest.fixture
    def saved_lane_node_set(self):
        return self.load_json_data('lane_node_set', saved_before=False)
    
    @pytest.fixture
    def saved_lane_boundary_set(self):
        return self.load_json_data('lane_boundary_set', saved_before=False)
    # 1
    def test_lane_node_idx_mgeo(self, expected_lane_node_set, saved_lane_node_set):
        for i in range(len(saved_lane_node_set)):
            assert saved_lane_node_set[i]['idx'] in expected_lane_node_set.nodes
    # 2
    def test_lane_node_type_mgeo(self, expected_lane_node_set, saved_lane_node_set):
        for i in range(len(saved_lane_node_set)):
            assert saved_lane_node_set[i]['node_type'] == expected_lane_node_set.nodes[saved_lane_node_set[i]['idx']].node_type
    # 3
    def test_lane_node_junction_mgeo(self, expected_lane_node_set, saved_lane_node_set):
        for i in range(len(saved_lane_node_set)):
            assert saved_lane_node_set[i]['junction'] == expected_lane_node_set.nodes[saved_lane_node_set[i]['idx']].junctions
    # 4
    def test_lane_node_point_mgeo(self, expected_lane_node_set, saved_lane_node_set):
        for i in range(len(saved_lane_node_set)):
            assert saved_lane_node_set[i]['point'] == expected_lane_node_set.nodes[saved_lane_node_set[i]['idx']].point.tolist()
    # 5
    def test_lane_node_on_stop_line_mgeo(self, expected_lane_node_set, saved_lane_node_set):
        for i in range(len(saved_lane_node_set)):
            assert saved_lane_node_set[i]['on_stop_line'] == expected_lane_node_set.nodes[saved_lane_node_set[i]['idx']].on_stop_line
    # 6
    def test_lane_node_idx_json(self, saved_lane_node_set):
        for i in range(len(self.lane_node_set)):
            assert self.lane_node_set[i]['idx'] == saved_lane_node_set[i]['idx']
    # 7
    def test_lane_node_type_json(self, saved_lane_node_set):
        for i in range(len(self.lane_node_set)):
            assert self.lane_node_set[i]['node_type'] == saved_lane_node_set[i]['node_type']
    # 8
    def test_lane_node_junction_json(self, saved_lane_node_set):
        for i in range(len(self.lane_node_set)):
            assert self.lane_node_set[i]['junction'] == saved_lane_node_set[i]['junction']
    # 9
    def test_lane_node_point_json(self, saved_lane_node_set):
        for i in range(len(self.lane_node_set)):
            assert self.lane_node_set[i]['point'] == saved_lane_node_set[i]['point']
    # 10
    def test_lane_node_on_stop_line_json(self, saved_lane_node_set):
        for i in range(len(self.lane_node_set)):
            assert self.lane_node_set[i]['on_stop_line'] == saved_lane_node_set[i]['on_stop_line']
    # 11
    def test_lane_boundary_idx_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['idx'] in expected_lane_boundary_set.lanes
    # 12
    def test_lane_boundary_from_node_idx_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['from_node_idx'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].from_node.idx
    # 13
    def test_lane_boundary_to_node_idx_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['to_node_idx'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].to_node.idx
    # 14
    def test_lane_boundary_points_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['points'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].points.tolist()
    # 15
    def test_lane_boundary_lane_type_def_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['lane_type_def'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].lane_type_def
    # 16
    def test_lane_boundary_lane_type_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['lane_type'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].lane_type
    # 17
    def test_lane_boundary_lane_sub_type_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['lane_sub_type'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].lane_sub_type
    # 18
    def test_lane_boundary_lane_color_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['lane_color'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].lane_color
    # 19
    def test_lane_boundary_lane_shape_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['lane_shape'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].lane_shape
    # 20
    def test_lane_boundary_lane_width_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['lane_width'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].lane_width
    # 21
    def test_lane_boundary_dash_interval_L1_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['dash_interval_L1'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].dash_interval_L1
    # 22
    def test_lane_boundary_dash_interval_L2_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['dash_interval_L2'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].dash_interval_L2
    # 23
    def test_lane_boundary_double_line_interval_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['double_line_interval'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].double_line_interval
    # 24
    def test_lane_boundary_geometry_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['geometry'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].geometry
    # 25
    def test_lane_boundary_pass_restr_mgeo(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['pass_restr'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].pass_restr
    # 26
    def test_lane_boundary_lane_type_offset(self, expected_lane_boundary_set, saved_lane_boundary_set):
        for i in range(len(saved_lane_boundary_set)):
            assert saved_lane_boundary_set[i]['lane_type_offset'] == expected_lane_boundary_set.lanes[saved_lane_boundary_set[i]['idx']].lane_type_offset
    # 27
    def test_lane_boundary_idx_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['idx'] in saved_lane_boundary_set[i]['idx']
    # 28
    def test_lane_boundary_from_node_idx_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['from_node_idx'] == saved_lane_boundary_set[i]['from_node_idx']\
    # 29
    def test_lane_boundary_to_node_idx_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['to_node_idx'] == saved_lane_boundary_set[i]['to_node_idx']
    # 30
    def test_lane_boundary_points_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['points'] == saved_lane_boundary_set[i]['points']
    # 31
    def test_lane_boundary_lane_type_def_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_type_def'] == saved_lane_boundary_set[i]['lane_type_def']
    # 32
    def test_lane_boundary_lane_type_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_type'] == saved_lane_boundary_set[i]['lane_type']
    # 33
    def test_lane_boundary_lane_sub_type_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_sub_type'] == saved_lane_boundary_set[i]['lane_sub_type']
    # 34
    def test_lane_boundary_lane_color_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_color'] == saved_lane_boundary_set[i]['lane_color']
    # 35
    def test_lane_boundary_lane_shape_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_shape'] == saved_lane_boundary_set[i]['lane_shape']
    # 36
    def test_lane_boundary_lane_width_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_width'] == saved_lane_boundary_set[i]['lane_width']
    # 37
    def test_lane_boundary_dash_interval_L1_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['dash_interval_L1'] == saved_lane_boundary_set[i]['dash_interval_L1']
    # 38
    def test_lane_boundary_dash_interval_L2_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['dash_interval_L2'] == saved_lane_boundary_set[i]['dash_interval_L2']
    # 39
    def test_lane_boundary_double_line_interval_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['double_line_interval'] == saved_lane_boundary_set[i]['double_line_interval']
    # 40
    def test_lane_boundary_geometry_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['geometry'] == saved_lane_boundary_set[i]['geometry']
    # 41
    def test_lane_boundary_pass_restr_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['pass_restr'] == saved_lane_boundary_set[i]['pass_restr']
    # 42
    def test_lane_boundary_lane_type_offset_json(self, saved_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_type_offset'] == saved_lane_boundary_set[i]['lane_type_offset']
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.output_folder_path, ignore_errors=True)
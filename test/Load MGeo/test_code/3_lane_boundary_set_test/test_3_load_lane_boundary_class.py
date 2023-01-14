'''
Test하고 싶은 것(5개): lane_node_set.json안에 있는 idx, node_type, junction, point 그리고 on_stop_line들의 값
Test하고 싶은 것(16개): lane_boundary_set.json안에 있는 idx, from_node_idx, to_node_idx, points ... 그리고 heading들의 값
'''
import json
import os
import pytest
import sys

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/3_lane_boundary_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo

class TestLoadLaneBoundary:
    
    @classmethod
    def setup_class(cls):
        cls.lane_node_set = cls.load_json_data(cls, 'lane_node_set')
        cls.lane_boundary_set = cls.load_json_data(cls, 'lane_boundary_set')
    
    def load_json_data(self, file_name):
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

    # --------------- Start: MGeo 메모리에 있는 `tested_node_set`과 `lane_node_set.json`들의 항목들을 비교한다. ---------------
    # 1
    def test_lane_node_idx_mgeo(self, expected_lane_node_set):
        for i in range(len(self.lane_node_set)):
            assert self.lane_node_set[i]['idx'] in expected_lane_node_set.nodes
    # 2
    def test_lane_node_type_mgeo(self, expected_lane_node_set):
        for i in range(len(self.lane_node_set)):
            assert self.lane_node_set[i]['node_type'] == expected_lane_node_set.nodes[self.lane_node_set[i]['idx']].node_type
    # 3
    def test_lane_node_junction_mgeo(self, expected_lane_node_set):
        for i in range(len(self.lane_node_set)):
            assert self.lane_node_set[i]['junction'] == expected_lane_node_set.nodes[self.lane_node_set[i]['idx']].junctions
    # 4
    def test_lane_node_point_mgeo(self, expected_lane_node_set):
        for i in range(len(self.lane_node_set)):
            assert self.lane_node_set[i]['point'] == expected_lane_node_set.nodes[self.lane_node_set[i]['idx']].point.tolist()
    # 5
    def test_lane_node_on_stop_line_mgeo(self, expected_lane_node_set):
        for i in range(len(self.lane_node_set)):
            assert self.lane_node_set[i]['on_stop_line'] == expected_lane_node_set.nodes[self.lane_node_set[i]['idx']].on_stop_line

    # --------------- Finish: MGeo 메모리에 있는 `tested_node_set`과 `lane_node_set.json`들의 항목들을 비교한다. ---------------
    #
    #
    #
    # --------------- Start: MGeo 메모리에 있는 `tested_lane_set`과 `lane_boundary_set.json`들의 항목들을 비교한다. ---------------
    # 6
    def test_lane_boundary_idx(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['idx'] in expected_lane_boundary_set.lanes
    # 7
    def test_lane_boundary_from_node_idx(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['from_node_idx'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].from_node.idx
    # 8
    def test_lane_boundary_to_node_idx(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['to_node_idx'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].to_node.idx
    # 9
    def test_lane_boundary_points(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['points'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].points.tolist()
    # 10
    def test_lane_boundary_lane_type_def(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_type_def'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].lane_type_def
    # 11
    def test_lane_boundary_lane_type(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_type'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].lane_type
    # 12
    def test_lane_boundary_lane_sub_type(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_sub_type'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].lane_sub_type
    # 13
    def test_lane_boundary_lane_color(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_color'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].lane_color
    # 14
    def test_lane_boundary_lane_shape(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_shape'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].lane_shape
    # 15
    def test_lane_boundary_lane_width(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_width'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].lane_width
    # 16
    def test_lane_boundary_dash_interval_L1(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['dash_interval_L1'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].dash_interval_L1
    # 17
    def test_lane_boundary_dash_interval_L2(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['dash_interval_L2'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].dash_interval_L2
    # 18
    def test_lane_boundary_double_line_interval(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['double_line_interval'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].double_line_interval
    # 19
    def test_lane_boundary_geometry(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['geometry'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].geometry
    # 20
    def test_lane_boundary_pass_restr(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['pass_restr'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].pass_restr
    # 21
    def test_lane_boundary_lane_type_offset(self, expected_lane_boundary_set):
        for i in range(len(self.lane_boundary_set)):
            assert self.lane_boundary_set[i]['lane_type_offset'] ==  expected_lane_boundary_set.lanes[self.lane_boundary_set[i]['idx']].lane_type_offset

    # --------------- Finish: MGeo 메모리에 있는 `tested_lane_set`과 `lane_boundary_set.json`들의 항목들을 비교한다. ---------------
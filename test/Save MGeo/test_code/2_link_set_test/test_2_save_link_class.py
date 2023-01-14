import json
import os
import pytest
import sys
import shutil

test_code_file_path = os.path.dirname(os.path.realpath(__file__))  
test_data_folder_path = os.path.normpath(os.path.join(test_code_file_path, '../../test_data/2_link_set'))
src_file_path = os.path.normpath(os.path.join(test_code_file_path, '../../../../src'))

sys.path.append(test_code_file_path)
sys.path.append(test_data_folder_path)
sys.path.append(src_file_path)

from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.save_load.subproc_load_link_ver2 import load_node_and_link

class TestSaveLinkMGeo:
    
    @classmethod
    def setup_class(cls):
        cls.node_set = cls.load_json_data(cls,'node_set', True)
        cls.link_set = cls.load_json_data(cls,'link_set', True)
        cls.global_info_set = cls.load_json_data(cls,'global_info', True)
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
    def expected_link_set(self):
        tested_node_set, tested_link_set, tested_junction_set = load_node_and_link(self.node_set, self.link_set, self.global_info_set)
        return tested_link_set
    
    def test_save_mgeo_link(self, expected_link_set):
        return MGeo.save_link(self.output_folder_path, expected_link_set)
    
    @pytest.fixture
    def saved_link_set(self):
        return self.load_json_data('link_set', saved_before=False)
    
    # --------------- Start: MGeo 메모리에 있는 `tested_link_set`과 `saved_link_set.json`들의 항목들을 비교한다. ---------------
    # 1
    def test_link_idx_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['idx'] in expected_link_set.lines
    # 2       
    def test_link_from_node_idx_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['from_node_idx'] == expected_link_set.lines[saved_link_set[i]['idx']].from_node.idx
    # 3        
    def test_link_to_node_idx_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['to_node_idx'] == expected_link_set.lines[saved_link_set[i]['idx']].to_node.idx
    # 4
    def test_link_points_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['points'] == expected_link_set.lines[saved_link_set[i]['idx']].points.tolist()
    # 5
    def test_link_max_speed_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['max_speed'] == expected_link_set.lines[saved_link_set[i]['idx']].max_speed
    # 6
    def test_link_min_speed_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['min_speed'] == expected_link_set.lines[saved_link_set[i]['idx']].min_speed
    # 7
    def test_link_lazy_init_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['lazy_init'] == expected_link_set.lines[saved_link_set[i]['idx']].lazy_point_init
    # 8
    def test_link_can_move_left_lane_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['can_move_left_lane'] == expected_link_set.lines[saved_link_set[i]['idx']].can_move_left_lane
    # 9
    def test_link_can_move_right_lane_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['can_move_right_lane'] == expected_link_set.lines[saved_link_set[i]['idx']].can_move_right_lane          
    # 10
    def test_link_left_lane_change_dst_link_idx_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['left_lane_change_dst_link_idx'] == expected_link_set.lines[saved_link_set[i]['idx']].lane_ch_link_left          
    # 11
    def test_link_right_lane_change_dst_link_idx_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['right_lane_change_dst_link_idx'] == expected_link_set.lines[saved_link_set[i]['idx']].lane_ch_link_right          
    # 12
    def test_link_lane_ch_link_path_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['lane_ch_link_path'] == expected_link_set.lines[saved_link_set[i]['idx']].lane_change_pair_list 
    # 13
    def test_link_link_type_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['link_type'] == expected_link_set.lines[saved_link_set[i]['idx']].link_type 
    # 14
    def test_link_link_type_def_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['link_type_def'] == expected_link_set.lines[saved_link_set[i]['idx']].link_type_def 
    # 15
    def test_link_road_type_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['road_type'] == expected_link_set.lines[saved_link_set[i]['idx']].road_type 
    # 16
    def test_link_road_id_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['road_id'] == expected_link_set.lines[saved_link_set[i]['idx']].road_id 
    # 17
    def test_link_ego_lane_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['ego_lane'] == expected_link_set.lines[saved_link_set[i]['idx']].ego_lane 
    # 18
    def test_link_lane_change_dir_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['lane_change_dir'] == expected_link_set.lines[saved_link_set[i]['idx']].lane_change_dir 
    # 19
    def test_link_hov_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['hov'] == expected_link_set.lines[saved_link_set[i]['idx']].hov 
    # 20
    def test_link_geometry_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['geometry'] == expected_link_set.lines[saved_link_set[i]['idx']].geometry 
    # 21
    def test_link_related_signal_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['related_signal'] == expected_link_set.lines[saved_link_set[i]['idx']].related_signal 
    # 22
    def test_link_its_link_id_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['its_link_id'] == expected_link_set.lines[saved_link_set[i]['idx']].its_link_id
    # 23
    def test_link_force_width_start_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['force_width_start'] == expected_link_set.lines[saved_link_set[i]['idx']].force_width_start
    # 24
    def test_link_width_start_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['width_start'] == expected_link_set.lines[saved_link_set[i]['idx']].width_start
    # 25
    def test_link_force_width_end_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['force_width_end'] == expected_link_set.lines[saved_link_set[i]['idx']].force_width_end
    # 26
    def test_link_width_end_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['width_end'] == expected_link_set.lines[saved_link_set[i]['idx']].width_end
    # 27
    def test_link_enable_side_border_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['enable_side_border'] == expected_link_set.lines[saved_link_set[i]['idx']].enable_side_border
     # 28
    def test_link_lane_mark_left_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['lane_mark_left'] == expected_link_set.lines[saved_link_set[i]['idx']].lane_mark_left
    # 29
    def test_link_lane_mark_right_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['lane_mark_right'] == expected_link_set.lines[saved_link_set[i]['idx']].lane_mark_right
    # 30
    def test_link_opp_traffict_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['opp_traffic'] == expected_link_set.lines[saved_link_set[i]['idx']].opp_traffic
    # 31
    def test_link_is_entrance_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['is_entrance'] == expected_link_set.lines[saved_link_set[i]['idx']].is_entrance
    # 32
    def test_link_is_exit_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['is_exit'] == expected_link_set.lines[saved_link_set[i]['idx']].is_exit
    # 33
    def test_link_speed_unit_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['speed_unit'] == expected_link_set.lines[saved_link_set[i]['idx']].speed_unit
    # 34
    def test_link_speed_list_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['speed_list'] == expected_link_set.lines[saved_link_set[i]['idx']].speed_list
    # 35
    def test_link_recommended_speed_mgeo(self, saved_link_set, expected_link_set):
        for i in range(len(saved_link_set)):
            assert saved_link_set[i]['recommended_speed'] == expected_link_set.lines[saved_link_set[i]['idx']].recommended_speed
    
    # --------------- Finish: MGeo 메모리에 있는 `tested_link_set`과 `saved_link_set.json`들의 항목들을 비교한다. ---------------
    
    
    
    # --------------- Start: 원래있던 `link_set.json`과 저장된 `saved_link_set.json`들의 항목들을 비교한다. ---------------
    # 36
    def test_link_idx_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['idx'] == saved_link_set[i]['idx']
    # 37
    def test_from_node_idx_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['from_node_idx'] == saved_link_set[i]['from_node_idx']
    # 38
    def test_to_node_idx_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['to_node_idx'] == saved_link_set[i]['to_node_idx']
    # 39
    def test_points_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['points'] == saved_link_set[i]['points']
    # 40
    def test_max_speed_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['max_speed'] == saved_link_set[i]['max_speed']
    # 41
    def test_min_speed_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['min_speed'] == saved_link_set[i]['min_speed']
    # 42
    def test_lazy_init_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['lazy_init'] == saved_link_set[i]['lazy_init']
    # 43
    def test_can_move_left_lane_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['can_move_left_lane'] == saved_link_set[i]['can_move_left_lane']
    # 44
    def test_can_move_right_lane_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['can_move_right_lane'] == saved_link_set[i]['can_move_right_lane']
    # 45
    def test_left_lane_change_dst_link_idx_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['left_lane_change_dst_link_idx'] == saved_link_set[i]['left_lane_change_dst_link_idx']
    # 46
    def test_right_lane_change_dst_link_idx_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['right_lane_change_dst_link_idx'] == saved_link_set[i]['right_lane_change_dst_link_idx']
    # 47
    def test_lane_ch_link_path_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['lane_ch_link_path'] == saved_link_set[i]['lane_ch_link_path']
    # 48
    def test_link_type_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['link_type'] == saved_link_set[i]['link_type']
    # 49
    def test_link_type_def_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['link_type_def'] == saved_link_set[i]['link_type_def']
    # 50
    def test_road_type_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['road_type'] == saved_link_set[i]['road_type']
    # 51
    def test_road_id_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['road_id'] == saved_link_set[i]['road_id']
    # 52
    def test_ego_lane_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['ego_lane'] == saved_link_set[i]['ego_lane']
    # 53
    def test_lane_change_dir_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['lane_change_dir'] == saved_link_set[i]['lane_change_dir']
    # 54
    def test_hov_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['hov'] == saved_link_set[i]['hov']
    # 55
    def test_geometry_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['geometry'] == saved_link_set[i]['geometry']
    # 56
    def test_related_signal_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['related_signal'] == saved_link_set[i]['related_signal']
    # 57
    def test_its_link_id_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['its_link_id'] == saved_link_set[i]['its_link_id']
    # 58
    def test_force_width_start_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['force_width_start'] == saved_link_set[i]['force_width_start']
    # 59
    def test_width_start_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['width_start'] == saved_link_set[i]['width_start']
    # 60
    def test_force_width_end_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['force_width_end'] == saved_link_set[i]['force_width_end']
    # 61
    def test_width_end_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['width_end'] == saved_link_set[i]['width_end']
    # 62
    def test_enable_side_border_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['enable_side_border'] == saved_link_set[i]['enable_side_border']
    # 63
    def test_lane_mark_left_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['lane_mark_left'] == saved_link_set[i]['lane_mark_left']
    # 64
    def test_lane_mark_right_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['lane_mark_right'] == saved_link_set[i]['lane_mark_right']
    # 65
    def test_opp_traffic_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['opp_traffic'] == saved_link_set[i]['opp_traffic']
    # 66
    def test_is_entrance_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['is_entrance'] == saved_link_set[i]['is_entrance']
    # 67
    def test_istest_is_exit_json_entrance_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['is_exit'] == saved_link_set[i]['is_exit']
    # 68
    def test_speed_unit_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['speed_unit'] == saved_link_set[i]['speed_unit']
    # 69
    def test_speed_offset_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['speed_offset'] == saved_link_set[i]['speed_offset']
    # 70
    def test_speed_list_json(self, saved_link_set):
        for i in range(len(self.link_set)):
            assert self.link_set[i]['speed_list'] == saved_link_set[i]['speed_list'] 
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.output_folder_path, ignore_errors=True)
    
    # --------------- Finish: 원래있던 `link_set.json`과 저장된 `saved_link_set.json`들의 항목들을 비교한다. ---------------
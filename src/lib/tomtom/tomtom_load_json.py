import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import json
import csv
import numpy as np

from lib.mgeo.class_defs import *
import struct
import uuid
import base64
import re

from lib.tomtom.tomtom_converter import *


from lib.common.logger import Logger


def read_json_files(input_folder_path, filename_to_key_func=None):
    """
    input_folder_path 변수가
    - 파일 이름을 포함하고 있으면 >> #1a 가 실행
    - 폴더 이름이면              >> #1b 가 실행

    TODO(sjhan): list가 아니고, 그냥 파일 이름만 넘어오면, #1b가 실행되는 문제
    """

    
    # input_folder_path가 리스트로 넘어오면 리스트로 사용하고, path 설정
    if type(input_folder_path) == list:
        # ---------- Section #1a ----------
        file_list = []
        for f in input_folder_path:
            file_list.append(os.path.basename(f))
        input_folder_path = os.path.dirname(input_folder_path[0])
        # ---------- Section #1a ----------
    else:
        # ---------- Section #1b ----------
        file_list = os.listdir(input_folder_path)
        # ---------- Section #1b ----------

    data = {}
    filename_map = {}

    for each_file in file_list:
        file_full_path = os.path.join(input_folder_path, each_file)
        
        # 디렉토리는 Skip
        if os.path.isdir(file_full_path):
            continue
        
        # json 체크
        filename, file_extension = os.path.splitext(each_file)
        filename = re.sub('[^A-Za-z]', '', filename)

        if file_extension == '.json':
            if filename_to_key_func is None:
                key = filename
            else:
                key = filename_to_key_func(filename)
            
            # 처리
            with open(file_full_path, 'r', encoding='UTF8') as input_file:
                if key in data:
                    data[key] += json.load(input_file)

                    abs_filename = os.path.normpath(os.path.join(input_folder_path, each_file))
                    filename_map[key] += '/{}'.format(abs_filename)
                else:
                    data[key] = json.load(input_file)

                    abs_filename = os.path.normpath(os.path.join(input_folder_path, each_file))
                    filename_map[key] = abs_filename
    return data

def create_lane_marking_set_from_json(laneBorder, origin):
    node_set = NodeSet()
    lane_set = LaneBoundarySet()

    for line in laneBorder:
        lane_marking_id = line['entity']['id']
        laneGeoPitType, laneGeoPoints = convert_string_to_points_json(line['attributes']['detail_geo'])
        laneColor = line['attributes']['color']
        laneShape = line['attributes']['type']

        points = np.array(laneGeoPoints)
        points -= origin

        start_node = Node(lane_marking_id+'S')
        start_node.point = points[0]
        node_set.nodes[start_node.idx] = start_node

        end_node = Node(lane_marking_id+'E')
        end_node.point = points[-1]
        node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=points, idx=lane_marking_id)
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)

        lane_boundary.lane_color = laneColor.lower()
        lane_boundary = convert_string_to_laneType(laneShape, lane_boundary)
        
        lane_set.lanes[lane_boundary.idx] = lane_boundary

    return node_set, lane_set

def create_node_and_link_from_json(centerlines, origin):
    node_set = NodeSet()
    link_set = LineSet()
    for line in centerlines:

        if line['attributes']['lane_type'] == 'NON_DRIVABLE_LANE':
            continue

        link_id = line['entity']['id']
        points = line['attributes']['detail_geo']
        points = convert_points(points)
        points -= origin

        start_node = Node(link_id+'S')
        start_node.point = points[0]
        node_set.nodes[start_node.idx] = start_node

        end_node = Node(link_id+'E')
        end_node.point = points[-1]
        node_set.nodes[end_node.idx] = end_node

        link = Link(points=points, 
                idx=link_id,
                lazy_point_init=False)
        link.set_from_node(start_node)
        link.set_to_node(end_node)

        link_set.lines[link.idx] = link
    
    # link_set = set_link_change(link_set, centerlines)

    return node_set, link_set



def convert_to_hex(str_input):
    # account for negative int uint values
    int_input = int(str_input)

    if int_input < 0:
        hex_output = format(int_input + 2**64, 'x')
    else:
        hex_output = format(int_input, 'x')
    
    return hex_output


def set_link_lane_change_values_json(link_set, laneGroups):
    # lane group에 associations,
    # 없는 데이터가 너무 많아서......... LaneGroup 범위 확인해야함
    for group in laneGroups:
        associations = group['associations']
        # 시퀀스 작은게 오른쪽, 큰게 왼쪽
        # 5(오른쪽만) 4 3 2 1(왼쪽만)
        lane_change_list = []
        for association in associations:
            entity = convert_ddctType(association['entity']['ddctType'])
            if entity == 'LaneCenterLineOfLaneGroup':
                sequence = association['sequence']
                msb = convert_to_hex(association['otherFeature']['UUID']['mostSigBits'])
                lsb = convert_to_hex(association['otherFeature']['UUID']['leastSigBits'])
                link_id = uuid.UUID(msb + lsb)
                lane_change_list.insert(sequence-1, link_id.hex)
        
        for i in range(len(lane_change_list)-1):
            if i == 0:
                try:
                    current_link = link_set.lines[lane_change_list[i]]
                    try:
                        left_link = link_set.lines[lane_change_list[i+1]]
                        current_link.set_left_lane_change_dst_link(left_link)
                        current_link.can_move_left_lane = True
                    except:
                        continue
                except:
                    # Logger.log_warning('This link ID({}) does not exist.'.format(lane_change_list[i]))
                    continue

            elif i == len(lane_change_list)-1:
                try:
                    current_link = link_set.lines[lane_change_list[i]]

                    try:
                        right_link = link_set.lines[lane_change_list[i-1]]
                        current_link.set_right_lane_change_dst_link(right_link)
                        current_link.can_move_right_lane = True
                    except:
                        continue
                except:
                    # Logger.log_warning('This link ID({}) does not exist.'.format(lane_change_list[i]))
                    continue

            else:
                try:
                    current_link = link_set.lines[lane_change_list[i]]

                    try:
                        right_link = link_set.lines[lane_change_list[i-1]]
                        current_link.set_right_lane_change_dst_link(right_link)
                        current_link.can_move_right_lane = True
                    except:
                        continue

                    try:
                        left_link = link_set.lines[lane_change_list[i+1]]
                        current_link.set_left_lane_change_dst_link(left_link)
                        current_link.can_move_left_lane = True
                    except:
                        continue
                except:
                    # Logger.log_warning('This link ID({}) does not exist.'.format(lane_change_list[i]))
                    continue


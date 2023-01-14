

import os
import sys
import json
import csv

from textwrap import fill

from numpy.lib.function_base import average
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # 프로젝트 Root 경로
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(current_path + '/../../lib/common') # 프로젝트 Root 경로

from lib.common.logger import Logger
local_parent_dir = os.path.normpath(os.path.join(current_path, '../../../'))
jiat_shp_kunsan_txt_dir = os.path.normpath(os.path.join(local_parent_dir, 'data\\hdmap\\jiat_shp_kunsan'))

import numpy as np
import csv

from lib.mgeo.class_defs import *
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common
from lib.common.coord_trans_ll2utm import CoordTrans_LL2UTM
from lib.common.polygon_util import minimum_bounding_rectangle, calculate_centroid

import math
import re
import itertools

from functools import partial
from pyproj import Proj, Transformer

# 좌표변환
transformer = Transformer.from_crs("epsg:5174", "epsg:32652")

def import_jiat_shp(input_path):
    map_info = shp_common.read_shp_files(input_path, encoding_ansi=True)[0]
    # X -'AREA'
    # X - 'ETC_LINE' -> LaneBoundary
    # X - 'ETC_POINT'
    # O - 'LANE_BND' -> LaneBoundary
    # O - 'LANE_CEN' -> Link
    # O - 'LANE_GROUP_BND' -> LaneBoundary
    # O - 'LANE_GROUP_CEN' -> Link
    # O - 'Localization Landmark' -> 정지선(Type : 404000), 노면표시
    
    origin = shp_common.get_first_shp_point(map_info['LANE_CEN'])
    origin[0], origin[1] = transformer.transform(origin[1], origin[0])
    origin = np.array(origin)

    fill_in_lane_cen = __fill_in_lane_cen_attributes(jiat_shp_kunsan_txt_dir)
    fill_in_lane_group_cen = __fill_in_lane_group_cen_attributes(jiat_shp_kunsan_txt_dir)
    fill_in_lane_bnd = __fill_in_lane_bnd_attributes(jiat_shp_kunsan_txt_dir)
    fill_in_lane_group_bnd = __fill_in_lane_group_bnd_attributes(jiat_shp_kunsan_txt_dir)

    average_z_values = []
    lane_node_set, lane_set, average_z_values = __create_lane_boundary_set(map_info['LANE_BND'], origin, fill_in_lane_bnd, average_z_values)
    lane_node_set, lane_set, average_z_values = __add_lane_boundary_set(map_info['LANE_GROUP_BND'], origin, lane_node_set, lane_set, fill_in_lane_group_bnd, average_z_values)
    average_z_value = find_average_z_values(average_z_values)
    lane_node_set, lane_set = __load_lane_boundary_set(map_info['ETC_LINE'], origin, lane_node_set, lane_set, average_z_value)

    link_node_set, link_set, link_id_set = __create_node_and_link_set(map_info['LANE_CEN'], map_info['LANE_GROUP_CEN'], origin, fill_in_lane_cen, fill_in_lane_group_cen, lane_set)
    link_node_set, link_set, junction_set = __create_junction_set(map_info['LANE_GROUP_CEN'], origin, link_node_set, link_set)

    stop_line_node_set, stop_line_lane_set = __create_stop_line(map_info['Localization Landmark'], origin, lane_node_set, lane_set, fill_in_lane_bnd)
    
    __group_ego_lanes(link_set)
    __group_ego_lanes_and_boundaries(link_set, lane_set, fill_in_lane_group_bnd)

    mgeo = MGeo(node_set=link_node_set, link_set = link_set, lane_node_set=lane_node_set, lane_boundary_set=lane_set)
    mgeo.set_origin(origin)
    mgeo.global_coordinate_system = Proj('+proj=utm +zone=52 +datum=WGS84 +units=m +no_defs').srs

    return mgeo

def __create_node_and_link_set(sf_1, sf_2, origin, fill_in_lane_cen, fill_in_lane_group_cen, lane_set):

    link_node_set = NodeSet()
    link_set = LineSet()
    link_id_set = list()

    shapes_1 = sf_1.shapes()
    records_1  = sf_1.records()
    fields_1 = sf_1.fields

    shapes_2 = sf_2.shapes()
    records_2  = sf_2.records()
    fields_2 = sf_2.fields

    # map_info['LANE_CEN'] 정보를 채워넣는다.
    if len(shapes_1) != len(shapes_1):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes_1)):
        shp_rec = shapes_1[i]
        dbf_rec = records_1[i]
        
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        new_points = []
        for point in shp_rec.points:
            new_point = point
            new_point[0], new_point[1] = transformer.transform(point[1], point[0])
            new_points.append(new_point)
        new_points = np.array(new_points)
        
        new_points = np.c_[new_points, shp_rec.z]
        # origin 무조건 전달, 상대좌표로 변경
        new_points -= origin

        link_id = '{}_{}'.format(dbf_rec.LINK_ID, dbf_rec.LANE_IDX)
        link_id_set.append(link_id)
        link = Link(idx=link_id, points=new_points, lazy_point_init=False)
        link.ego_lane = dbf_rec.LANE_IDX
        link.road_id = dbf_rec.GROUP_ID
       
        from_node = Node(link_id+'S')
        from_node.point = new_points[0] 
        link_node_set.append_node(from_node)
        from_node.node_type = 'other'

        to_node = Node(link_id+'E')
        to_node.point = new_points[-1] 
        link_node_set.append_node(to_node)
        to_node.node_type = 'other'

        link.set_from_node(from_node)
        link.set_to_node(to_node)

        fill_in_data = fill_in_lane_cen[link_id]
        
        # map_info['LANE_CEN']
        if fill_in_data['L_BND_IDX'] != '':
            left_lane_idx_lst = fill_in_data['L_BND_IDX']
            if '/' in left_lane_idx_lst:
                for i in left_lane_idx_lst.split('/'):
                    lane_idx = 'LANE{}_{}'.format(dbf_rec.LINK_ID, i)
                    link.set_lane_mark_left(lane_set.lanes[lane_idx])
            else:
                lane_idx = 'LANE{}_{}'.format(dbf_rec.LINK_ID, left_lane_idx_lst)
                link.set_lane_mark_left(lane_set.lanes[lane_idx])
        if fill_in_data['R_BND_IDX'] != '':
            right_lane_idx_lst = fill_in_data['R_BND_IDX']
            if '/' in right_lane_idx_lst:
                for i in right_lane_idx_lst.split('/'):
                    lane_idx = 'LANE{}_{}'.format(dbf_rec.LINK_ID, i)
                    link.set_lane_mark_right(lane_set.lanes[lane_idx])
            else:
                lane_idx = 'LANE{}_{}'.format(dbf_rec.LINK_ID, right_lane_idx_lst)
                link.set_lane_mark_right(lane_set.lanes[lane_idx])
        link.link_type_def = 'other'
        link_set.append_line(link)

    # map_info['LANE_GROUP_BND'] 정보를 채워넣는다.
    if len(shapes_2) != len(shapes_2):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes_2)):
        shp_rec = shapes_2[i]
        dbf_rec = records_2[i]
        
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        new_points = []
        for point in shp_rec.points:
            new_point = point
            new_point[0], new_point[1] = transformer.transform(point[1], point[0])
            new_points.append(new_point)
        new_points = np.array(new_points)
        
        new_points = np.c_[new_points, shp_rec.z]
        # origin 무조건 전달, 상대좌표로 변경
        new_points -= origin

        link_id = 'LANE{}_{}'.format(dbf_rec.GROUP_ID, dbf_rec.LANE_IDX)
        link_id_set.append(link_id)
        link = Link(idx=link_id, points=new_points, lazy_point_init=False)
        link.ego_lane = dbf_rec.LANE_IDX
        link.road_id = dbf_rec.GROUP_ID
       
        from_node = Node(link_id+'S')
        from_node.point = new_points[0] 
        link_node_set.append_node(from_node)
        from_node.node_type = 'other'

        to_node = Node(link_id+'E')
        to_node.point = new_points[-1] 
        link_node_set.append_node(to_node)
        to_node.node_type = 'other'

        link.set_from_node(from_node)
        link.set_to_node(to_node)
        link.link_type ='other'

        fill_in_data = fill_in_lane_group_cen[link_id]
        
        # map_info['LANE_GROUP_CEN']
        if fill_in_data['L_BND_IDX'] != '':
            left_lane_idx_lst = fill_in_data['L_BND_IDX']
            if '/' in left_lane_idx_lst:
                for i in left_lane_idx_lst.split('/'):
                    lane_idx = 'LANE{}_{}'.format(dbf_rec.GROUP_ID, i)
                    link.set_lane_mark_left(lane_set.lanes[lane_idx])
            else:
                lane_idx = 'LANE{}_{}'.format(dbf_rec.GROUP_ID, left_lane_idx_lst)
                link.set_lane_mark_left(lane_set.lanes[lane_idx])
        if fill_in_data['R_BND_IDX'] != '':
            right_lane_idx_lst = fill_in_data['R_BND_IDX']
            if '/' in right_lane_idx_lst:
                for i in right_lane_idx_lst.split('/'):
                    lane_idx = 'LANE{}_{}'.format(dbf_rec.GROUP_ID, i)
                    link.set_lane_mark_right(lane_set.lanes[lane_idx])
            else:
                lane_idx = 'LANE{}_{}'.format(dbf_rec.GROUP_ID, right_lane_idx_lst)
                link.set_lane_mark_right(lane_set.lanes[lane_idx])
        link.link_type_def = 'other'
        link_set.append_line(link)
    
    return link_node_set, link_set, link_id_set

def __group_ego_lanes(link_set):
    road_id_and_link_id_group = dict()
    ### 로직의 설계 ###
    # 1. 모든 링크들의 road_id을 추출한다. 
    # 2. link들을 선회하면서, road_id가 같다면(key), link들을 묶어준다 (value).
    # 3. 한 road_id을 기준으로, ego_lane_idx을 조사한다.
    # 4. ego_lane_idx가 1이면, ego_lane_idx 2가 있으면, lane_ch_link_right에 ego_lane_idx2을 넣어준다.
    # 5. ego_lane_idx가 2 ~ n-1이면, ego_lane_idx의 lane_ch_link_left와 lane_ch_link_right에 각각 넣어준다.
    # 6. 마지막, ego_lane_idx가 n이면, 종료한다.
    for link_id in link_set.lines:
        if link_set.lines[link_id].road_id not in road_id_and_link_id_group.keys():
            road_id_and_link_id_group[link_set.lines[link_id].road_id] = []
        road_id_and_link_id_group[link_set.lines[link_id].road_id].append(link_id)
    
    for ego_lane_id in road_id_and_link_id_group.values():
        if len(ego_lane_id) == 0:
            raise BaseException('[ERROR] len(ego_lane) == 0')
        elif len(ego_lane_id) == 1:
            link_set.lines[ego_lane_id[0]].can_move_left_lane = False
            link_set.lines[ego_lane_id[0]].can_move_right_lane = False
        elif len(ego_lane_id) == 2:
            link_set.lines[ego_lane_id[0]].can_move_left_lane = False
            link_set.lines[ego_lane_id[0]].can_move_right_lane = True
            link_set.lines[ego_lane_id[0]].lane_ch_link_right = link_set.lines[ego_lane_id[1]]
            link_set.lines[ego_lane_id[1]].can_move_left_lane = True
            link_set.lines[ego_lane_id[1]].can_move_right_lane = False
            link_set.lines[ego_lane_id[1]].lane_ch_link_left = link_set.lines[ego_lane_id[0]]
        elif len(ego_lane_id) >= 3:
            link_set.lines[ego_lane_id[0]].can_move_left_lane = False
            link_set.lines[ego_lane_id[0]].can_move_right_lane = True
            link_set.lines[ego_lane_id[0]].lane_ch_link_right = link_set.lines[ego_lane_id[1]]
            for i in range(1, len(ego_lane_id)-1):
                link_set.lines[ego_lane_id[i]].can_move_left_lane = True
                link_set.lines[ego_lane_id[i]].can_move_right_lane = True
                link_set.lines[ego_lane_id[i]].lane_ch_link_left = link_set.lines[ego_lane_id[i-1]]
                link_set.lines[ego_lane_id[i]].lane_ch_link_right = link_set.lines[ego_lane_id[i+1]]
            link_set.lines[ego_lane_id[-1]].can_move_left_lane = True
            link_set.lines[ego_lane_id[-1]].can_move_right_lane = False
            link_set.lines[ego_lane_id[-1]].lane_ch_link_left = link_set.lines[ego_lane_id[-2]]
   


def __group_ego_lanes_and_boundaries(link_set, lane_set, fill_in_lane_group_bnd):
    # LANE_GROUP_CEN 파일에서 가져온 fill_in_lane_group_bnd
    # 모든 link_set들
    # 모든 lane_set들

    # link을 선회하다가, 
    # 시작점:  link (5326650032003770_1) 의 
    # lane_mark_left의 id는 LANE5326650032003770_1, lane_mark_right의 id는 LANE5326650032003770_2
    # 끝 점: link (5326650032003770_3)의
    # lane_mark_left의 id는 LANE5326650032003770_3, lane_mark_right의 id는 LANE5326650032003770_4
    # lane_id (= group_id + bnd_idx)
    
    # valid_lanes = []
    # for lane in fill_in_lane_group_bnd:
    #     # lane = 53266500320039164_2
    #     lane = lane[4:]
    #     if lane in link_set.lines:
    #         valid_lanes.append(lane)

    # valid_lanes_pair = []
    # for lane in valid_lanes:
    #     if valid_lanes_pair and valid_lanes_pair[-1][0][:-2] == lane[:-2]:
    #         valid_lanes_pair[-1].append(lane)
    #     else:
    #         valid_lanes_pair.append([lane])
   

    # for road_chunk in valid_lanes_pair:
    #     for idx in range(len(road_chunk)):
    #         link_set.lines[road_chunk[idx]].set_lane_mark_left = lane_set.lanes['LANE'+ road_chunk[idx]]
    #         link_set.lines[road_chunk[idx]].set_lane_mark_right = lane_set.lanes['LANE'+ road_chunk[idx]+1]
    # print(link_set)


        # left_lane_idx = fill_in_data['L_BND_IDX']
        # left_lane_bnd_idx = 'LANE{}_{}'.format(dbf_rec.LINK_ID, left_lane_idx)
        # if left_lane_bnd_idx in lane_set.lanes:
        #     link.set_lane_mark_left(lane_set.lanes[left_lane_bnd_idx])
        # right_lane_idx = fill_in_data['R_BND_IDX'] 
        # right_lane_bnd_idx = 'LANE{}_{}'.format(dbf_rec.LINK_ID, right_lane_idx)
        # if right_lane_bnd_idx in lane_set.lanes:
        #     link.set_lane_mark_right(lane_set.lanes[right_lane_bnd_idx])
        # link.link_type_def = 'other'
        # link_set.append_line(link)
        pass


def __create_junction_set(sf, origin, node_set, link_set):
    
    junction_set = JunctionSet()

    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]
        
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        new_points = []
        for point in shp_rec.points:
            new_point = point
            new_point[0], new_point[1] = transformer.transform(point[1], point[0])
            new_points.append(new_point)
        new_points = np.array(new_points)
        
        new_points = np.c_[new_points, shp_rec.z]
        # origin 무조건 전달, 상대좌표로 변경
        new_points -= origin

        link_id = '{}_{}'.format(dbf_rec.GROUP_ID, dbf_rec.LANE_IDX)
        link = Link(idx=link_id, points=new_points, lazy_point_init=False)
        # link.ego_lane = dbf_rec.LANE_IDX
        link.road_id = dbf_rec.GROUP_ID
        link_set.append_line(link)

        from_node = Node(link_id+'S')
        from_node.point = new_points[0] 
        node_set.append_node(from_node)
        from_node.node_type = 'other'

        to_node = Node(link_id+'E')
        to_node.point = new_points[-1] 
        node_set.append_node(to_node)
        to_node.node_type = 'other'

        link.set_from_node(from_node)
        link.set_to_node(to_node)

        link.link_type_def = 'other'

    return node_set, link_set, junction_set

def __create_lane_boundary_set(sf, origin, fill_in_lane_bnd, average_z_values):

    lane_node_set = NodeSet()
    lane_set = LaneBoundarySet()

    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]
        
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        new_points = []
        for point in shp_rec.points:
            new_point = point
            new_point[0], new_point[1] = transformer.transform(point[1], point[0])
            new_points.append(new_point)
        new_points = np.array(new_points)
        
        new_points = np.c_[new_points, shp_rec.z]
        average_z_values.append(shp_rec.z)
        # origin 무조건 전달, 상대좌표로 변경
        new_points -= origin

        lane_id = 'LANE{}_{}'.format(dbf_rec.LINK_ID, dbf_rec.BND_IDX)
        lane = LaneBoundary(idx=lane_id, points=new_points)
        # lane.road_id = dbf_rec.GROUP_ID

        from_node = Node(lane_id+'S')
        from_node.point = new_points[0] 
        lane_node_set.append_node(from_node)
        from_node.node_type = 'other'

        to_node = Node(lane_id+'E')
        to_node.point = new_points[-1] 
        lane_node_set.append_node(to_node)
        to_node.node_type = 'other'

        lane.set_from_node(from_node)
        lane.set_to_node(to_node)

        fill_in_data =  fill_in_lane_bnd[lane_id]
        
        lane.lane_color = fill_in_data['COLOR']
        lane.lane_type_def = 'other'
        lane_set.append_line(lane)

    return lane_node_set, lane_set, average_z_values

def __add_lane_boundary_set(sf, origin, lane_node_set, lane_set, fill_in_lane_group_bnd, average_z_values):

    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]
        
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        new_points = []
        for point in shp_rec.points:
            new_point = point
            new_point[0], new_point[1] = transformer.transform(point[1], point[0])
            new_points.append(new_point)
        new_points = np.array(new_points)
        
        new_points = np.c_[new_points, shp_rec.z]
        average_z_values.append(shp_rec.z)
        # origin 무조건 전달, 상대좌표로 변경
        new_points -= origin

        lane_id = 'LANE{}_{}'.format(dbf_rec.GROUP_ID, dbf_rec.BND_IDX)
        lane = LaneBoundary(idx=lane_id, points=new_points)

        from_node = Node(lane_id+'S')
        from_node.point = new_points[0] 
        lane_node_set.append_node(from_node)
        from_node.node_type = 'other'

        to_node = Node(lane_id+'E')
        to_node.point = new_points[-1] 
        lane_node_set.append_node(to_node)
        to_node.node_type = 'other'

        lane.set_from_node(from_node)
        lane.set_to_node(to_node)
        lane.lane_type_def = 'other'

        fill_in_data = fill_in_lane_group_bnd[lane_id]
        lane.lane_color = fill_in_data['COLOR']
        lane_set.append_line(lane)

    return lane_node_set, lane_set, average_z_values

def __create_stop_line(sf, origin, node_set, lane_set, fill_in_lane_bnd):
    
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):

        shp_rec = shapes[i]
        dbf_rec = records[i]

        if dbf_rec['TYPE'] != '404000':
            continue
        
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        new_points = []
        for point in shp_rec.points:
            new_point = point
            new_point[0], new_point[1] = transformer.transform(point[1], point[0])
            new_points.append(new_point)
        new_points = np.array(new_points)
        
        new_points = np.c_[new_points, shp_rec.z]
        # origin 무조건 전달, 상대좌표로 변경
        new_points -= origin

        temp_stop_points = np.array(minimum_bounding_rectangle(new_points))
        middle_stop_x_point = sum([p[0] for p in temp_stop_points]) / len([p[0] for p in temp_stop_points])
        middle_stop_y_point = sum([p[1] for p in temp_stop_points]) / len([p[1] for p in temp_stop_points])
        middle_stop_z_point = sum([p[2] for p in temp_stop_points]) / len([p[2] for p in temp_stop_points])
        middle_stop_point = np.array([[middle_stop_x_point, middle_stop_y_point, middle_stop_z_point]])

        stop_line_id = '{}'.format(dbf_rec.ID)
        stop_lane = LaneBoundary(idx=stop_line_id, points=temp_stop_points)
        lane_set.append_line(stop_lane)

        from_node = Node(stop_line_id+'S')
        from_node.point = new_points[0] 
        node_set.append_node(from_node)

        to_node = Node(stop_line_id+'E')
        to_node.point = new_points[-1] 
        node_set.append_node(to_node)

        stop_lane.set_from_node(from_node)
        stop_lane.set_to_node(to_node)

        stop_lane.lane_type_def = 'other'

    return node_set, lane_set

def find_average_z_values(average_z_values):
  all_z_values = list(itertools.chain(*average_z_values))
  average_z_value = sum(all_z_values) / len(all_z_values)
  return average_z_value



def __load_lane_boundary_set(sf, origin, lane_node_set, lane_set, average_z_value):
    # node_set = NodeSet()
    # lane_set = LaneBoundarySet()

    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]
        
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        new_points = []
        for point in shp_rec.points:
            new_point = point
            new_point[0], new_point[1] = transformer.transform(point[1], point[0])
            new_points.append(new_point)
        new_points = np.array(new_points)
       
        z = []
        for i in range(new_points.shape[0]):
            z.append(np.array([average_z_value]))
        new_points = np.c_[new_points, z]
        new_points -= origin
        lane_id = 'LANE{}_{}'.format(dbf_rec.ETC_ID, dbf_rec.ETC_TYPE)
        lane = LaneBoundary(idx=lane_id, points=new_points)
        # lane.road_id = dbf_rec.GROUP_ID
        lane_set.append_line(lane)

        from_node = Node(lane_id+'S')
        from_node.point = new_points[0] 
        lane_node_set.append_node(from_node)
        from_node.node_type = 'other'

        to_node = Node(lane_id+'E')
        to_node.point = new_points[-1] 
        lane_node_set.append_node(to_node)
        to_node.node_type = 'other'

        lane.set_from_node(from_node)
        lane.set_to_node(to_node)
        lane.lane_type_def = 'other'

    return lane_node_set, lane_set


def __fill_in_lane_cen_attributes(jiat_shp_kunsan_txt_dir):
    link_dict = {}
    lane_cen_txt_file = jiat_shp_kunsan_txt_dir + "\\LANE_CEN.txt"
    with open(lane_cen_txt_file) as file:
        lines = file.readlines()
        properties = lines[0]
        values = lines[1:]
        for value in values:
            group_id, link_id, positive, lane_idx, l_bnd_idx, r_bnd_idx, arrow, conn_type, shared = value.split('|')
            link_id = '{}_{}'.format(link_id, lane_idx)
            link_dict[link_id] = {'POSITIVE':positive, 'L_BND_IDX' : l_bnd_idx, 'R_BND_IDX' : r_bnd_idx, 'ARROW': arrow, 'CONN_TYPE':conn_type, 'SHARED': shared}
    return link_dict

def __fill_in_lane_group_cen_attributes(jiat_shp_kunsan_txt_dir):
    lane_dict = {}
    lane_group_bnd_txt_file = jiat_shp_kunsan_txt_dir + "\\LANE_GROUP_CEN.txt"
    with open(lane_group_bnd_txt_file) as file:
        lines = file.readlines()
        properties = lines[0]
        values = lines[1:]
        for value in values:
            group_id, lane_idx, conn_id, l_bnd_idx, r_bnd_idx, lane_type, shared = value.split('|')
            lane_id = 'LANE{}_{}'.format(group_id, lane_idx)
            lane_dict[lane_id] = {'CONN_ID': conn_id, 'L_BND_IDX': l_bnd_idx, 'R_BND_IDX': r_bnd_idx, 'LANE_TYPE': lane_type, 'SHARED': shared}
    return lane_dict

def __fill_in_lane_group_bnd_attributes(jiat_shp_kunsan_txt_dir):
    link_dict = {}
    lane_group_cen_txt_file = jiat_shp_kunsan_txt_dir + "\\LANE_GROUP_BND.txt"
    with open(lane_group_cen_txt_file) as file:
        lines = file.readlines()
        properties = lines[0]
        values = lines[1:]
        for value in values:
            group_id, bnd_idx, bnd_type, color, bnd_cover = value.split('|')
            link_id = 'LANE{}_{}'.format(group_id, bnd_idx)
            link_dict[link_id] = {'GROUP_ID':group_id, 'BND_IDX': bnd_idx, 'BND_TYPE': bnd_type, 'COLOR': color, 'BND_COVER': bnd_cover}
        # for link in link_dict:
        #     if '/' in link_dict[link]['L_BND_IDX']:
        #         link_dict[link]['L_BND_IDX'] = link_dict[link]['L_BND_IDX'].split('/')[-1]
        #     if '/' in link_dict[link]['R_BND_IDX']:
        #         link_dict[link]['R_BND_IDX'] = link_dict[link]['R_BND_IDX'].split('/')[-1]
    return link_dict



def __fill_in_lane_bnd_attributes(jiat_shp_kunsan_txt_dir):

    lane_dict = {}
    lane_bnd_txt_file = jiat_shp_kunsan_txt_dir + "\\LANE_BND.txt"
    with open(lane_bnd_txt_file) as file:
        lines = file.readlines()
        properties = lines[0]
        values = lines[1:]
        for value in values:
            group_id, link_id, positive, bnd_idx, bnd_type, color, bnd_cover = value.split('|')
            lane_id = 'LANE{}_{}'.format(link_id, bnd_idx)
            lane_dict[lane_id] = {'POSITIVE':positive, 'BND_TYPE' : bnd_type, 'COLOR' : color, 'BND_COVER': bnd_cover}
    return lane_dict



def import_and_save(input_path):
    
    output_path = os.path.join(input_path, 'output') 
    relative_loc = True
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
    except OSError:
        print('Error: Creating directory. ' +  output_path)

    mgeo = import_jiat_shp(input_path)
    mgeo.to_json(output_path)

if __name__ == "__main__":
    import_and_save(jiat_shp_kunsan_txt_dir)
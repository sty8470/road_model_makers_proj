import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # 프로젝트 Root 경로
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(current_path + '/../../lib/common') # 프로젝트 Root 경로

import numpy as np
import traceback
import copy
import csv

import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

from lib.common.polygon_util import calculate_centroid
from lib.common.coord_trans_ll2tm import CoordTrans_LL2TM

from pyproj import Proj, Transformer, CRS

from lib.mgeo.class_defs import *

from lib.mgeo.edit.funcs import edit_node, edit_link

from lib.mgeo.utils.logger import Logger
from lib.mgeo.utils import error_fix

import math
import re

# def convert_points(points):
#     new_data_points = []
#     for point in points:
#         transformer = Transformer.from_crs("epsg:4326", "epsg:26910")
#         new_x, new_y = transformer.transform(point[0], point[1])
#         new_point = [new_x, new_y, point[2]]
#         new_data_points.append(new_point)
#     return np.array(new_data_points)
     

def convert_points(points, coord_trans_obj):
    new_data_points = []
    
    for point in points:
        east, north = coord_trans_obj.ll2tm(point[1], point[0])
        new_data_point = [east, north, point[2]]
        new_data_points.append(new_data_point)
    return np.array(new_data_points)


def RoadrunnerImporter(input_path, spheroid, latitude_of_origin, central_meridian, scale_factor, false_easting, false_northing, world_origin_lat, world_origin_lon):
    geojson_files, folder_info = geojson_common.read_geojson_files(input_path)
    
    node_set = NodeSet()
    link_set = LineSet()
    lane_node_set = NodeSet()
    lane_mark_set = LaneBoundarySet()
    light_set = SignalSet()
    cw_set = CrossWalkSet()
    scw_set = SingleCrosswalkSet()

    coord_trans_obj = CoordTrans_LL2TM()
    coord_trans_obj.set_tm_params(
        spheroid,
        latitude_of_origin,
        central_meridian,
        scale_factor,
        false_easting,
        false_northing)

    origin = convert_points([[world_origin_lon, world_origin_lat, 0]], coord_trans_obj)[0]
    origin = np.array(origin)
    print('origin : ', origin)

    r_id = 0

    travel_dir_container = dict() # 각 링크의 원본 데이터 상 travel dir 정보 임시 저장 (해당 링크의 point는 뒤집혀서 저장됨)
    features = geojson_files[list(geojson_files.keys())[0]]['features']
    for line in features:       
        if line['properties']['Type'] == 'Lane':            
            link_id = line['properties']['Id']
            points = line['geometry']['coordinates']
            points = np.array(convert_points(points, coord_trans_obj))
            # points -= origin
            
            # TravelDir = Backward 인 경우 Points를 뒤집어서 Link 방향을 맞춰주는 작업 수행
            if line['properties']['TravelDir'] == 'Backward':
                points = np.flip(points, axis=0)                

            link = Link(points=points, 
                    idx=link_id, 
                    link_type=line['properties']['LaneType'],
                    lazy_point_init=False)

            link.link_type_def = 'RoadRunner'

            if line['properties']['LaneType'] == 'Driving' or line['properties']['LaneType'] == 'Center Turn':
                speed_limit = line['properties']['SpeedLimit']
                
                # speed 설정
                if speed_limit == '' or speed_limit == '0' or speed_limit == None:
                    Logger.log_warning('There is no Speed Limit Info.')
                    link.set_max_speed_kph(0)
                else:    
                    match = re.match(r"([0-9]+)([a-z]+)", speed_limit, re.I)
                    if match is not None:
                        items = match.groups()
                    if 'mph' in speed_limit:
                        speed = float(items[0]) * 1.6
                    else:
                        speed = float(items[0])
                    
                    link.set_max_speed_kph(speed)

            # Predecessors 있고 이미 Link Set에 추가 된 경우
            if len(line['properties']['Predecessors']) >= 1:
                for predecessor in line['properties']['Predecessors']:
                    if predecessor['Id'] in link_set.lines:
                        # TravelDir가 Backward 인 경우 Predecessors는 다음 도로를 의미
                        if line['properties']['TravelDir'] == 'Backward':
                            link.set_to_node(link_set.lines[predecessor['Id']].from_node)
                            break
                        # TravelDir가 Forward 인 경우 Predecessors는 이전 도로
                        else:
                            link.set_from_node(link_set.lines[predecessor['Id']].to_node)
                            break              

            if len(line['properties']['Successors']) >= 1:
                for successor in line['properties']['Successors']:
                    if successor['Id'] in link_set.lines:
                        # TravelDir가 Backward인 경우 Successors는 이전 도로를 의미
                        if line['properties']['TravelDir'] == 'Backward':
                            link.set_from_node(link_set.lines[successor['Id']].to_node)
                            break
                        # Successors가 Forward 인 경우 Successors는 다음 도로
                        else:
                            link.set_to_node(link_set.lines[successor['Id']].from_node)
                            break

            if link.from_node == None or link.from_node == '':
                start_node = Node(link_id+'S')
                start_node.point = points[0]
                node_set.nodes[start_node.idx] = start_node
                link.set_from_node(start_node)
            
            if link.to_node == None or link.to_node == '':
                end_node = Node(link_id+'E')
                end_node.point = points[-1]
                node_set.nodes[end_node.idx] = end_node
                link.set_to_node(end_node)             

            r_id += 1
            link.road_id = r_id

            link_set.lines[link.idx] = link
            travel_dir_container[link.idx] = line['properties']['TravelDir']

        elif line['properties']['Type'] == 'Signal':
            sign_id = line['properties']['Id']
            # sign_type = line['properties']['Name'].split("/")[-1].split('.')[0]
            points = line['geometry']['coordinates'][0]
            points = np.array(convert_points(points, coord_trans_obj))
            # points -= origin
            point = calculate_centroid(points)
            traffic_light = Signal(sign_id)
            traffic_light.dynamic = True
            traffic_light.orientation = '+'
            traffic_light.country = 'KR'

            # mgeo 기준으로 type 설정
            traffic_light.type_def = 'mgeo'
            traffic_light.type = 'car'            
            traffic_light.sub_type = []
            for bulb in line['properties']['Bulbs']:
                if 'red' in bulb['NodeName']:
                    traffic_light.sub_type.append('red')
                elif 'yellow' in bulb['NodeName']:
                    traffic_light.sub_type.append('yellow')
                elif 'green' in bulb['NodeName']:
                    traffic_light.sub_type.append('straight')
                # turn 신호의 종류를 알 수 없어서 일단 left로 설정
                elif 'turn' in bulb['NodeName']:
                    traffic_light.sub_type.append('left')

            traffic_light.point = point

            light_set.signals[traffic_light.idx] = traffic_light
        
        elif line['properties']['Type'] == 'LaneBoundary':
            lane_id = line['properties']['Id']
            # points = np.array(line['geometry']['coordinates'])
            points = line['geometry']['coordinates']
            points = np.array(convert_points(points, coord_trans_obj))
            # points -= origin
            
            start_node = Node(lane_id+'S')
            start_node.point = points[0]

            # 같은 위치에 Node가 이미 있는 경우 Start Node로 재사용
            is_found = False
            for lane_node_id in lane_node_set.nodes:
                lane_node = lane_node_set.nodes[lane_node_id]
                
                if np.array_equal(lane_node.point, start_node.point):
                    start_node = lane_node
                    is_found = True
                    break
                else:
                    pos_vector = lane_node.point - start_node.point
                    dist = np.linalg.norm(pos_vector, ord=2)
                    if dist < 0.01:
                        start_node = lane_node
                        is_found = True
                        break
                    
            
            if is_found == False:
                lane_node_set.nodes[start_node.idx] = start_node

            end_node = Node(lane_id+'E')
            end_node.point = points[-1]

            # 같은 위치에 Node가 이미 있는 경우 End Node로 재사용
            is_found = False
            for lane_node_id in lane_node_set.nodes:
                lane_node = lane_node_set.nodes[lane_node_id]

                if np.array_equal(lane_node.point, end_node.point):
                    end_node = lane_node
                    is_found = True
                    break
                else:
                    pos_vector = lane_node.point - end_node.point
                    dist = np.linalg.norm(pos_vector, ord=2)
                    if dist < 0.01:
                        end_node = lane_node
                        is_found = True
                        break

            if is_found == False:
                lane_node_set.nodes[end_node.idx] = end_node

            lane = LaneBoundary(points=points, idx=lane_id)
            lane.lane_type_def = 'RoadRunner'
            lane.lane_type = []
            lane.set_from_node(start_node)
            lane.set_to_node(end_node)

            lane_mark_set.lanes[lane.idx] = lane     

        elif line['properties']['Type'] == 'Crosswalk':
            cw = Crosswalk()
            
            cw_id = line['properties']['Id']
            points = line['geometry']['coordinates'][0]
            points = np.array(convert_points(points, coord_trans_obj))

            # 국토부 데이터 모델에서 횡단보도가 5번이라 일단 cw_type에 5라는 값을 사용
            scw = SingleCrosswalk(points=points, idx=cw_id, cw_type = 5)            
            scw_set.append_data(scw, create_new_key=False)

            cw.append_single_scw_list(scw)                 
            cw_set.append_data(cw)
            scw.ref_crosswalk_id = cw.idx       

    
    for feature in features:
        # related signal 정보 설정
        if feature['properties']['Type'] == 'Gate':
            link = link_set.lines[feature['properties']['Lane']['Id']]

            # 신호등에 연결된 Link 정보 추가
            if len(feature['properties']['Signals']) >= 1:
                for signal in feature['properties']['Signals']:
                    light_set.signals[signal['Id']].link_id_list.append(link.idx)

                # GeoJSON에는 Right, Left, Straight 값이 설정되므로 related_signal 값은 해당 값을 소문자로 변경해서 입력
                # 연결된 신호등이 있는 경우에만 related signal 정보 설정
                if feature['properties']['TurnRelation'] == 'Left':
                    link.related_signal = 'left'
                elif feature['properties']['TurnRelation'] == 'Right':
                    link.related_signal = 'right'
                elif feature['properties']['TurnRelation'] == 'Straight':
                    link.related_signal = 'straight'
                elif feature['properties']['TurnRelation'] == 'UTurnLeft':
                    link.related_signal = 'uturn_normal'
                elif feature['properties']['TurnRelation'] == 'UTurnRight':
                    link.related_signal = 'uturn_normal'
                else:
                    link.related_signal = feature['properties']['TurnRelation']

            # Gate와 연결된 Link의 From_Node의 on_stop_line 필드 값을 true로 설정
            link.from_node.on_stop_line = True

        # Link의 Lane Boundary 설정
        elif feature['properties']['Type'] == 'Lane':
            # link가 link_set에 포함되어 있는 경우
            if feature['properties']['Id'] in link_set.lines:
                link = link_set.lines[feature['properties']['Id']]

                # Forward 인 경우
                if feature['properties']['TravelDir'] == 'Forward':
                    if feature['properties']['LeftBoundary']['Id'] in lane_mark_set.lanes:
                        link.lane_mark_left.append(lane_mark_set.lanes[feature['properties']['LeftBoundary']['Id']])

                    if feature['properties']['RightBoundary']['Id'] in lane_mark_set.lanes:
                        link.lane_mark_right.append(lane_mark_set.lanes[feature['properties']['RightBoundary']['Id']])
                # Backward 인 경우
                else:
                    if feature['properties']['LeftBoundary']['Id'] in lane_mark_set.lanes:
                        link.lane_mark_right.append(lane_mark_set.lanes[feature['properties']['LeftBoundary']['Id']])

                    if feature['properties']['RightBoundary']['Id'] in lane_mark_set.lanes:
                        link.lane_mark_left.append(lane_mark_set.lanes[feature['properties']['RightBoundary']['Id']])
            

    # 분석 결과 한 Node로 모이거나 나가는 Link가 여러 개인 경우 중복 노드가 생길 가능성이 있음.
    # 0.0001 거리 이하인 경우 중복노드로 체크하고 Repair 수행
    # 0.0001로 값을 설정한 이유는 짧은 노드의 경우 0.0001 보다는 멀리 생성되는 경우가 많기 떄문
    repair_overlapped_node(node_set)
            
    set_lane_change_info_into_link_set(features, link_set, travel_dir_container)

    # 길이가 짧은 Link를 From_Link 또는 To_Link와 Merge
    # for link_id , type_ck in list(link_set.lines.items()):
    #     link = link_set.lines[link_id]
    #     from_node = link.from_node
    #     to_node = link.to_node

    #     pos_vector = from_node.point - to_node.point
    #     dist = np.linalg.norm(pos_vector, ord=2)

    #     # Link 길이가 2M 보다 작은 경우
    #     if dist < 2:
    #         # from_link가 있는 경우
    #         if len(link.from_node.from_links) >= 1:
    #             for from_link in link.from_node.from_links:
    #                 new_points = np.vstack((from_link.points, link.points[1:]))
    #                 from_link.set_points(new_points)

    #                 from_link.set_to_node(link.to_node)

    #             edit_link.delete_link(link_set, link)

    #             # 현재 Link의 from_node 삭제
    #             from_node.to_links = list()
    #             from_node.from_links = list()
    #             edit_node.delete_node(node_set, from_node, delete_junction=False)
    #         # from_link는 없고 to_link가 있는 경우
    #         elif len(link.to_node.to_links) >= 1:
    #             for to_link in link.to_node.to_links:
    #                 new_points = np.vstack((link.points, to_link.points[1:]))
    #                 to_link.set_points(new_points)
                  
    #                 to_link.set_from_node(link.from_node)

    #             edit_link.delete_link(link_set, link)

    #             # 현재 Link의 to_node 삭제
    #             to_node.to_links = list()
    #             to_node.from_links = list()
    #             edit_node.delete_node(node_set, to_node, delete_junction=False)

    # Signal과 연결된 Link 중 Link Merge 단계를 거치면서 없어진 Link를 Signal 연결 정보에서 제거
    # for signal_id in light_set.signals:
    #     signal = light_set.signals[signal_id]
    #     copy_link_id_list = copy.deepcopy(signal.link_id_list)
    #     for link_id in copy_link_id_list:
    #         if link_id not in link_set.lines:
    #             signal.link_id_list.remove(link_id)

    mgeo_planner_map = MGeo(
        node_set=node_set, 
        link_set=link_set, 
        lane_node_set=lane_node_set, 
        lane_boundary_set=lane_mark_set,
        light_set=light_set,
        cw_set=cw_set,
        scw_set=scw_set)
    mgeo_planner_map.set_origin(origin)
    
    # proj4 변환
    proj4_datum = ' +ellps={}'.format(spheroid)
    porj4_lat_0 = ' +lat_0={}'.format(latitude_of_origin)
    porj4_x_0 = ' +x_0={}'.format(false_easting)
    porj4_y_0 = ' +y_0={}'.format(false_northing)
    porj4_lon_0 = ' +lon_0={}'.format(central_meridian)
    porj4_k = ' +k={}'.format(scale_factor)
    proj4_string = '+proj=tmerc'  + porj4_lat_0 + porj4_lon_0 + porj4_k + porj4_x_0 + porj4_y_0 + proj4_datum + ' +units=m +no_defs'
    # mgeo_planner_map.global_coordinate_system = Proj(proj4_string).srs
    mgeo_planner_map.global_coordinate_system = proj4_string
    
    return mgeo_planner_map


def import_txt_data(input_path):
    link_set = __create_link_set(input_path)
    node_set = __create_node_set(link_set)

    mgeo_planner_map = MGeo(node_set, link_set)
    return mgeo_planner_map


def __create_node_set(line_set):
    idx = 0
    node_set = NodeSet()
    lines = line_set.lines
    for line in lines:
        # Node 생성하기
        create_node_point = [lines[line].points[0], lines[line].points[-1]]
        for i, point in enumerate(create_node_point):
            idx += 1
            node_id = 'NODE{}'.format(idx)
            node = Node(node_id)
            node.point = point
            if i == 0:
                node.add_to_links(lines[line])
            elif i == 1:
                node.add_from_links(lines[line])
            node_set.nodes[node.idx] = node

    return node_set

# import_txt_data('C:/Users/sjhan/Documents/road_model_maker/rsc/map_data/20-10-19 CBNU/' )

def set_lane_change_info_into_link_set(geojson_lines, link_set, travel_dir_container):
    right_link = None
    left_link = None
    right_link_id = None
    left_link_id = None

    for line in geojson_lines:

        right_link = None
        left_link = None
        right_link_id = None
        left_link_id = None

        if line['properties']['Type'] == 'LaneBoundary':
            # lane marking
            if 'RightLane' in line['properties']:
                right_link_id = line['properties']['RightLane']['Id']
                if right_link_id in link_set.lines:
                    right_link = link_set.lines[right_link_id]
                
            if 'LeftLane' in line['properties']:
                left_link_id = line['properties']['LeftLane']['Id']
                if left_link_id in link_set.lines:
                    left_link = link_set.lines[left_link_id]
            
            
            # 위 조건 문에서 right_link, left_link 가 생성되었을 때만 아래가 동작
            if right_link is not None and left_link is not None:
                # 다르면 스킵 (lane boundary가 중앙선인 경우 이렇게 됨)
                if travel_dir_container[right_link_id] != travel_dir_container[left_link_id] :
                    continue

                # 같으면
                if travel_dir_container[right_link_id] == 'Forward':
                    left_link.set_right_lane_change_dst_link(right_link)
                    left_link.can_move_right_lane = True
                    right_link.set_left_lane_change_dst_link(left_link)
                    right_link.can_move_left_lane = True

                else: # backward인 경우에는 left, right 관계가 반대가 됨
                    left_link.set_left_lane_change_dst_link(right_link)
                    left_link.can_move_left_lane = True
                    right_link.set_right_lane_change_dst_link(left_link)
                    right_link.can_move_right_lane = True
               
# RoadRunner import 시 생성되는 중복 노드 제거
def repair_overlapped_node(node_set):
    Logger.log_trace('Called: repair_overlapped_node')

    try:
        if node_set is None or len(node_set.nodes) < 1 :
            Logger.log_info('There is no node data.')
            return

        # Distance를 0.1로 잡을 경우 겹치지 않는 Node가 검색되는 문제가 있어서 Distance를 0.0001로 조정
        overlapped_node_set = error_fix.search_overlapped_node(node_set, 0.0001)
       
        if overlapped_node_set is None or overlapped_node_set == []:
            Logger.log_info('No overlapped node is found.')
            return

    except BaseException as e:
        Logger.log_error('find_overlapped_node failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    try:      
        nodes_of_no_use = error_fix.repair_overlapped_node(overlapped_node_set)
        edit_node.delete_nodes(node_set, nodes_of_no_use)

        Logger.log_info('repair_overlapped_node done OK')
    except BaseException as e:
        Logger.log_error('repair_overlapped_node failed (traceback is down below) \n{}'.format(traceback.format_exc()))


if __name__ == "__main__":
    RoadrunnerImporter(
        'D:\\road_model_maker\\rsc\\map_data\\opendrive_test\\RR_DefaultScene_4Way_StopSign',
        'WGS84',
        38.0,
        127.0,
        1.0,
        0,
        0
        )
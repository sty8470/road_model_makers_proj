import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import numpy as np

from lib.mgeo.class_defs import *
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_junction
from lib.mgeo.utils import error_fix

import struct
import uuid
import base64
import re

from lib.mgeo.class_defs import *
from lib.mgeo.edit.funcs import edit_node
from lib.mgeo.utils import error_fix

from lib.tomtom.tomtom_converter import *

from lib.common.logger import Logger

def create_speed_restrictions_from_geojson(map_info, origin):
    # dict {uuid : speed-info}
    speed_set = dict()
    if 'speedRestrictions' not in map_info:
        return dict()

    speed_restrictions = map_info['speedRestrictions']['features']
    for item in speed_restrictions:
        speed_id = item['properties']['id']
        restrInfos = item['properties']['restrInfos']
        is_passenger = True if 'Passenger' in restrInfos else False
        speed_info = int(restrInfos.split(';')[0])

        is_max = True if restrInfos.split(';')[2] == 'MaximumSpeed' else False
        is_recommended = True if restrInfos.split(';')[2] == 'RecommendedSpeed' else False

        speed_unit = item['properties']['speedUnit']
        speed_set[speed_id] = {'speed':speed_info, 'is_max':is_max, 'is_recommended':is_recommended, 'is_passenger':is_passenger, 'unit':speed_unit}
        # speed_set[speed_id] = [speed_info, speed_max, speed_unit]

    return speed_set


def create_node_and_link_from_geojson(map_info, lane_mark_set, origin, lane_node_set): 
    speed_set = create_speed_restrictions_from_geojson(map_info, origin)
    
    line_items = map_info['laneCenterline']['features']
    # laneTrajectoryLane은 일단 안가져오기
    # line_items.extend(map_info['laneTrajectoryLane']['features'])
    
    node_set, link_set = make_link_set(speed_set, lane_mark_set, line_items, origin)
    junction_set = set_link_lane_change(map_info['laneGroup'], link_set)
    
    non_exist_lane_mark_list = error_fix.find_non_existent_lane_marking(line_items, lane_mark_set)
    error_fix.repair_non_existent_lane_marking(non_exist_lane_mark_list, link_set, lane_mark_set)


    dangling_lane_node = error_fix.find_dangling_nodes(lane_node_set)
    edit_node.delete_nodes(lane_node_set, dangling_lane_node)
    
    dangling_node = error_fix.find_dangling_nodes(node_set)
    # 제대로 안 생긴 junction이라 지워야한다.
    for node in dangling_node:
        for jc in node.junctions:
            if jc.idx in junction_set.junctions:
                edit_junction.delete_junction(junction_set, jc)

    edit_node.delete_nodes(node_set, dangling_node)

    return node_set, link_set, junction_set, lane_mark_set


def make_link_set(speed_set, lane_mark_set, line_items, origin):
    node_set = NodeSet()
    link_set = LineSet()

    for line in line_items:

        # if line['properties']['type'] == 'DRIVABLE_LANE':
        link_id =  line['properties']['id']


        # line_type
        link_type = None
        if 'type' in line['properties']:
            link_type = line['properties']['type']

        # ';' 기준으로 여러개가 들어가있는 경우가 있음(★)
        # NON_DRIVABLE_LANE은 정보가 없음
        max_speed = 0
        speed_unit = ''
        speed_region = [0, 0]
        recommended_speed = 0
        speed_qustn = {}

        # if link_type in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
        if line['properties']['speedInfos'] is not None and line['properties']['speedInfos'] != '':

            speed_info_list = line['properties']['speedInfos'].split(';')
            for speed_info in speed_info_list:
                speed_info_id = speed_info.split(':')[0]
                speed_info_range = speed_info.split(':')[1]

                if speed_info_id in speed_set:
                    current_speed_info = speed_set[speed_info_id]
                    
                    speed_unit = current_speed_info['unit']

                    # 추천속도일 경우 > 21.06.02 OpenDrive 최고속도만 지정 가능해서 사용안하지만 추가해놓음
                    if current_speed_info['is_recommended'] is True:
                        recommended_speed = float(current_speed_info['speed'])

                    # passenger_car가 있는 정보를 max로 넣기
                    if current_speed_info['is_max'] and current_speed_info['is_passenger']:
                        max_speed = current_speed_info['speed']
                        speed_regions = speed_info_range.split(',')
                        for sr in speed_info_range.split(','):
                            speed_region = sr.split('..')
                            speed_region = list(map(int, speed_region))

                            if max_speed not in speed_qustn:
                                speed_qustn[max_speed] = [speed_region]
                            else:
                                speed_qustn[max_speed].append(speed_region)
                                speed_qustn[max_speed].sort()
                                # start - end 연결하기(★바꾸기★)
                                if len(speed_qustn[max_speed]) > 1:
                                    new_data = []
                                    for res in speed_qustn[max_speed]:
                                        if len(new_data) < 1:
                                            new_data.append(res)
                                        else:
                                            if new_data[-1][0] < res[0]:
                                                if new_data[-1][1] == res[0]:
                                                    new_data[-1] = [new_data[-1][0], res[1]]
                                                else:
                                                    new_data.append(res)
                                            elif new_data[-1][0] > res[0]:
                                                if new_data[-1][0] == res[1]:
                                                    new_data[-1] = [res[0], new_data[-1][1]]
                                                else:
                                                    new_data.append(res)
                                            else:
                                                new_data.append(res)
                                    speed_qustn[max_speed] = new_data

                # speed_info = line['properties']['speedInfos'].split(';')[0].split(':')[0]
                # if speed_info in speed_set:
                #     if speed_set[speed_info]['is_max'] is True:
                #         max_speed = speed_set[speed_info]['speed']
                #         speed_unit = speed_set[speed_info]['unit']
        
        ll_points = line['geometry']['coordinates']
        while len(ll_points) == 1:
            ll_points = ll_points[0]

        lane_mark_left = None
        if 'leftDiv' in line['properties']:
            lane_mark_left = line['properties']['leftDiv']

        lane_mark_right = None
        if 'rightDiv' in line['properties']:
            lane_mark_right = line['properties']['rightDiv']

        points = convert_points(ll_points)
        points = np.array(points)
        points -= origin

        opp_traffic = False
        is_entrance = False
        is_exit = False
        # [210512] tomtom geoJSON 데이터 추가 속성 추출
        if line['properties']['oppTraffic'] == 1:
            opp_traffic = True
        if line['properties']['entrance'] == 1:
            is_entrance = True
        if line['properties']['exit'] == 1:
            is_exit = True

        
        if 'prvLanes' in line['properties'] and line['properties']['prvLanes'] is not None:
            prvLanes = line['properties']['prvLanes'].split(';')
            if len(prvLanes) == 1:
                prv_link = prvLanes[0].split(':')
                prv_link_id = prv_link[0]
                if prv_link_id in link_set.lines:
                    start_node = link_set.lines[prv_link_id].to_node
                else:
                    start_node = Node(link_id+'S')
                    start_node.point = points[0]
                    node_set.nodes[start_node.idx] = start_node
            else:
                start_node = None
                prv_link = []
                for links in prvLanes:
                    prv_link_temp = links.split(':')
                    prv_link_id = prv_link_temp[0]
                    prv_link.append(prv_link_temp)
                    if prv_link_id in link_set.lines:
                        start_node = link_set.lines[prv_link_id].to_node
                if start_node is None:
                    start_node = Node(link_id+'S')
                    start_node.point = points[0]
                    node_set.nodes[start_node.idx] = start_node

        if 'nxtLanes' in line['properties'] and line['properties']['nxtLanes'] is not None:
            nxtLanes = line['properties']['nxtLanes'].split(';')

            if len(nxtLanes) == 1:
                nxt_link = nxtLanes[0].split(':')
                nxt_link_id = nxt_link[0]
                if nxt_link_id in link_set.lines:
                    end_node = link_set.lines[nxt_link_id].from_node
                else:
                    end_node = Node(link_id+'E')
                    end_node.point = points[-1]
                    node_set.nodes[end_node.idx] = end_node
            else:
                end_node = None
                nxt_link = []
                for links in nxtLanes:
                    nxt_link_temp = links.split(':')
                    nxt_link_id = nxt_link_temp[0]
                    nxt_link.append(nxt_link_temp)
                    if nxt_link_id in link_set.lines:
                        end_node = link_set.lines[nxt_link_id].from_node
                if end_node is None:
                    end_node = Node(link_id+'E')
                    end_node.point = points[-1]
                    node_set.nodes[end_node.idx] = end_node

        link = Link(points=points, idx=link_id, lazy_point_init=False)
        # link.link_type = link_type
        # link.link_type_def = 'TomTom_v2105a'
        link.set_link_type(link_type, 'TomTom_v2105a')
        link.set_from_node(start_node)
        link.set_to_node(end_node)

        # link에다가 입력 다르게 해야한다.
        if recommended_speed:
            link.set_recommended_speed_kph(recommended_speed)
        
        if len(speed_qustn) > 0:
            link.speed_list = speed_qustn
            link.set_max_speed_kph(max(speed_qustn.keys()))
            link.set_speed_unit(speed_unit)
            for skey, sitem in speed_qustn.items():
                for si in sitem:
                    link.set_speed_region(int(si[0]), int(si[1]))

        if lane_mark_left in lane_mark_set.lanes:
            link.set_lane_mark_left(lane_mark_set.lanes[lane_mark_left])
        else:
            Logger.log_warning('lane mark left (id : {}) does not exist for link (id: {})'.format(lane_mark_left, link_id))
        
        if lane_mark_right in lane_mark_set.lanes:
            link.set_lane_mark_right(lane_mark_set.lanes[lane_mark_right])
        else:
            Logger.log_warning('lane mark right (id : {}) does not exist for link (id: {})'.format(lane_mark_right, link_id))

        link.opp_traffic = opp_traffic
        link.is_entrance = is_entrance
        link.is_exit = is_exit
        
        link_set.lines[link.idx] = link

    overlapped_node = error_fix.search_overlapped_node(node_set, 0.1)
    nodes_of_no_use = error_fix.repair_overlapped_node(overlapped_node)
    edit_node.delete_nodes(node_set, nodes_of_no_use)

    return node_set, link_set

def set_link_lane_change(lane_group, link_set):

    junction_set = JunctionSet()
    new_road_id = 1
    new_junction_id = 10000

    for lane in lane_group['features']:
        
        # 분기점에서 junction 넣기
        set_junction = False
        set_junction_node = []

        lanes = lane['properties']['lanes']
        lane_change_list = lanes.split(';')
        lane_change_list = list(reversed(lane_change_list))

        # if len(list(set(non_exist_lane_mark_list).intersection(lane_change_list))) > 0:
        #     for i in lane_change_list:
        #         link_id = lane_change_list[i]
        #         if link_id in link_set.lines:
        #             edit_link.delete_link(link_set, link_set.lines[link_id])
        
        road_id = lane['properties']['id']
        ego_lane = 1

        if len(lane_change_list) > 1:
            road_change = False
            for i in range(len(lane_change_list)):
                current_link_id = lane_change_list[i]
                
                if current_link_id in link_set.lines:
                    current_link = link_set.lines[current_link_id]
                    
                    if current_link.link_type in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE', 'EMERGENCY_LANE',"NON_DRIVABLE_LANE"]:
                        if road_change:
                            # road_id = 'newroad{}'.format(new_road_id)
                            # new_road_id += 1
                            # ego_lane = 1
                            road_change = False
                            set_junction = True

                        else:
                            if len(current_link.from_node.to_links) > 1:
                                road_change = True
                            if len(current_link.to_node.from_links) > 1:
                                road_change = True
                        
                    


                    current_link.road_id = road_id
                    current_link.ego_lane = ego_lane
                    ego_lane += 1
                    
                    if current_link.link_type in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE', 'EMERGENCY_LANE',"NON_DRIVABLE_LANE"]:
                        set_junction_node.append(current_link.from_node)
                        set_junction_node.append(current_link.to_node)

                    if i == 0:
                        right_link_id = lane_change_list[i+1]
                        left_link_id = None
                    elif i == (len(lane_change_list)-1):
                        right_link_id = None
                        left_link_id = lane_change_list[i-1]
                    else:
                        right_link_id = lane_change_list[i+1]
                        left_link_id = lane_change_list[i-1]

                    if right_link_id in link_set.lines:
                        right_link = link_set.lines[right_link_id]
                        current_link.set_right_lane_change_dst_link(right_link)

                        if right_link.link_type == 'DRIVABLE_LANE':
                            current_link.can_move_right_lane = True
                            if road_change:
                                current_link.can_move_right_lane = False
                        else:
                            current_link.can_move_right_lane = False

                        if right_link.link_type in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
                            set_junction_node.append(right_link.from_node)
                            set_junction_node.append(right_link.to_node)
                                
                    if left_link_id in link_set.lines:

                        if left_link_id in link_set.lines:
                            left_link = link_set.lines[left_link_id]
                            current_link.set_left_lane_change_dst_link(left_link)

                            if left_link.link_type == 'DRIVABLE_LANE':
                                current_link.can_move_left_lane = True
                            else:
                                current_link.can_move_left_lane = False

                            # junction 생성은 차선에는 전부 다
                            if left_link.link_type in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
                                set_junction_node.append(left_link.from_node)
                                set_junction_node.append(left_link.to_node)


                    if current_link.ego_lane == 1:
                        current_link.can_move_left_lane = False
                        
                    if current_link.link_type != 'DRIVABLE_LANE':
                        current_link.can_move_right_lane = False
                        current_link.can_move_left_lane = False
        else:
            current_link_id = lane_change_list[0]
            if current_link_id in link_set.lines:
                current_link = link_set.lines[current_link_id]
                current_link.road_id = road_id
                current_link.ego_lane = ego_lane

                if current_link.link_type in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
                    set_junction_node.append(current_link.from_node)
                    set_junction_node.append(current_link.to_node)

        if lane['properties']['nextArea'] is not None:
            nextArea = lane['properties']['nextArea'].split(';')
        else:
            nextArea = []

        if lane['properties']['prevArea'] is not None:
            prevArea = lane['properties']['prevArea'].split(';')
        else:
            prevArea = []

        # if len(nextArea) > 1 and set_junction == False:
        #     set_junction = True
        #     set_junction_node = []
        #     for ilane in lane_change_list:
        #         current_link = link_set.lines[ilane]
        #         if current_link.link_type not in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
        #             continue
        #         set_junction_node.append(current_link.to_node)
        #         for tlink in current_link.to_node.to_links:
        #             set_junction_node.append(tlink.to_node)

        # if len(prevArea) > 1 and set_junction == False:
        #     set_junction = True
        #     set_junction_node = []
        #     for ilane in lane_change_list:
        #         current_link = link_set.lines[ilane]
        #         if current_link.link_type not in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
        #             continue
        #         set_junction_node.append(current_link.from_node)
        #         for flink in current_link.from_node.from_links:
        #             set_junction_node.append(flink.from_node)

        if set_junction:
            new_junction_id += 1
            junction = Junction(_id = str(new_junction_id))
            set_junction_node = list(set(set_junction_node))
            for i in set_junction_node:
                junction.add_jc_node(i)
            junction_set.append_junction(junction, create_new_key=False)
            # if len(nextArea) == len(prevArea) == 1:
            #     print('여기는 그냥 차선만 늘어난다.', junction.idx)
        else:
            add_junction_node = []
            if len(nextArea) > 1:
                for ilane in lane_change_list:
                    current_link = link_set.lines[ilane]
                    if current_link.link_type != 'DRIVABLE_LANE':
                        continue
                    add_junction_node.append(current_link.to_node)
                    for tlink in current_link.to_node.to_links:
                        add_junction_node.append(tlink.to_node)
                new_junction_id += 1
                junction = Junction(_id = str(new_junction_id))
                add_junction_node = list(set(add_junction_node))
                for inode in add_junction_node:
                    junction.add_jc_node(inode)
                junction_set.append_junction(junction, create_new_key=False)   

            
            add_junction_node = []
            if len(prevArea) > 1:
                for ilane in lane_change_list:
                    current_link = link_set.lines[ilane]
                    if current_link.link_type != 'DRIVABLE_LANE':
                        continue
                    add_junction_node.append(current_link.from_node)
                    for flink in current_link.from_node.from_links:
                        add_junction_node.append(flink.from_node)
                new_junction_id += 1
                junction = Junction(_id = str(new_junction_id))
                add_junction_node = list(set(add_junction_node))
                for inode in add_junction_node:
                    junction.add_jc_node(inode)
                junction_set.append_junction(junction, create_new_key=False)   

    return junction_set


# lane_marking에서도 중복 node 제거하기
def create_lane_marking_from_geojson(map_info, origin): 

    node_set = NodeSet()
    lanemark_set = LaneBoundarySet()

    lines = map_info['singleBorder']['features']
    for line in lines:
        lane_marking_id = line['properties']['id']
        # if line['properties']['type'] not in [
        #     'ROAD_BORDER',
        #     'UNDEFINED_ROAD_BORDER',
        #     'UNKNOWN_BARRIER',
        #     'LEFT_CURB',
        #     'RIGHT_CURB',
        #     'BI_CURB'
        # ]:
        #     continue
        ll_points = line['geometry']['coordinates']
        while len(ll_points) == 1:
            ll_points = ll_points[0]

        points = convert_points(ll_points)

        points = np.array(points)
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

        lane_boundary.lane_color = [line['properties']['color'].lower()]
        lane_boundary = convert_string_to_laneType(line['properties']['type'], lane_boundary)
        
        lanemark_set.lanes[lane_boundary.idx] = lane_boundary

    overlapped_node = error_fix.search_overlapped_node(node_set, 0.05)
    nodes_of_no_use = error_fix.repair_overlapped_node(overlapped_node)
    edit_node.delete_nodes(node_set, nodes_of_no_use)

    
    # 294780589: "PassingRestriction.LaneBorderpassingfromleftandright" = 0
    # 1485072440: "PassingRestriction.LaneBorderpassingnotallowed" = 3
    # 886768577: "PassingRestriction.LaneBorderpassingonlylefttoright" = 1
    # -2092663395: "PassingRestriction.LaneBorderpassingonlyrighttoleft" = 2

    # tomtom geoJSON 데이터 추가 속성 추출 passRestr
    lines = map_info['laneBorder']['features']
    for line in lines:
        lane_marking_id = line['properties']['id']
        if lane_marking_id not in lanemark_set.lanes:
            Logger.log_warning('lane_marking_id({}) not in lane_mark_set, skipping current lane mark import'.format(lane_marking_id))
            continue
        clane = lanemark_set.lanes[lane_marking_id]
        # avro 파일과 text 스타일 똑같이
        pass_restr = line['properties']['passRestr'].replace('_', '').lower()
        clane.pass_restr = pass_restr

    return node_set, lanemark_set

    
def create_traffic_sign_set_from_geojson(map_info, origin):
    # fid, id, type, subtype, shape, heading, colors, add_info, faceWidth, faceHeight, add_data, verDate
    ts_set = SignalSet()
    
    if 'trafficSigns' not in map_info:
        return ts_set

    ts_list = map_info['trafficSigns']['features']

    for ts in ts_list:
        sign_id = ts['properties']['id']
        point = ts['geometry']['coordinates']
        width = ts['properties']['faceWidth']
        height = ts['properties']['faceHeight']
        heading = ts['properties']['heading']
        color = ts['properties']['colors']
        shape = ts['properties']['shape']
        sign_type = ts['properties']['type']
        sign_subtype = ts['properties']['subtype']

        point = convert_points([point])
        point = np.array(point[0])
        point -= origin

        traffic_sign = Signal(sign_id)
        traffic_sign.dynamic = False
        traffic_sign.orientation = '+'
        traffic_sign.country = 'US'     
        traffic_sign.type_def = 'tomtom'
            
        traffic_sign.type = sign_type
        traffic_sign.sub_type = sign_subtype
        # 사이즈 설정
        traffic_sign.height = height * 0.01 # cm to m
        traffic_sign.width = width * 0.01 # cm to m
        traffic_sign.heading = heading
        traffic_sign.point = point
        ts_set.signals[traffic_sign.idx] = traffic_sign

    return ts_set
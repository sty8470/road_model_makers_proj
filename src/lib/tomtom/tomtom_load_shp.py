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
from lib.mgeo.edit.funcs import edit_node
from lib.mgeo.utils import error_fix
import struct
import uuid
import base64
import re

from lib.tomtom.tomtom_converter import *

def create_speed_restrictions_from_shp(map_info, origin):
    speed_set = dict()
    speed_restrictions = map_info['speedRestrictions']
    
    shapes = speed_restrictions.shapes()
    records  = speed_restrictions.records()
    fields = speed_restrictions.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        speed_id = dbf_rec['id']
        speed_info = int(dbf_rec['restrInfos'].split(';')[0])
        speed_set[speed_id] = speed_info*1.60934

    return speed_set


def create_node_and_link_from_shp(map_info, lane_mark_set, origin):

    speed_set = create_speed_restrictions_from_shp(map_info, origin)

    node_set = NodeSet()
    link_set = LineSet()
    junction_set = JunctionSet()

    center_lines = map_info['laneCenterline']

    c_shapes = center_lines.shapes()
    c_records  = center_lines.records()
    c_fields = center_lines.fields
    if len(c_shapes) != len(c_records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(c_shapes)):
        shp_rec = c_shapes[i]
        dbf_rec = c_records[i]

        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
        shp_rec.points = convert_points(shp_rec.points)
        shp_rec.points -= origin
        
        link_id = dbf_rec['id']

        # [210512] tomtom geoJSON 데이터 추가 속성 추출
        opp_traffic = dbf_rec['oppTraffic']
        is_entrance = dbf_rec['entrance']
        is_exit = dbf_rec['exit']

        line_type = dbf_rec['type']
        max_speed = 0
        max_speed = 0
        if line_type == 'DRIVABLE_LANE':
            if dbf_rec['speedInfos'] is not None:
                speed_info = dbf_rec['speedInfos'].split(':')[0]
                if speed_info in speed_set:
                    max_speed = speed_set[speed_info]

        lane_mark_left = dbf_rec['leftDiv']
        lane_mark_right = dbf_rec['rightDiv']

        if dbf_rec['prvLanes'] is not None:
            prvLanes = dbf_rec['prvLanes'].split(';')
            if len(prvLanes) == 1:
                prv_link = prvLanes[0].split(':')
                prv_link_id = prv_link[0]
                if prv_link_id in link_set.lines:
                    start_node = link_set.lines[prv_link_id].to_node
                else:
                    start_node = Node(link_id+'S')
                    start_node.point = shp_rec.points[0]
                    node_set.nodes[start_node.idx] = start_node
            else:
                start_node = None
                for links in prvLanes:
                    prv_link = links.split(':')
                    prv_link_id = prv_link[0]
                    if prv_link_id in link_set.lines:
                        start_node = link_set.lines[prv_link_id].to_node
                if start_node is None:
                    start_node = Node(link_id+'S')
                    start_node.point = shp_rec.points[0]
                    node_set.nodes[start_node.idx] = start_node

                # junction = Junction(_id=line['properties']['fid'])
                # junction.add_jc_node(start_node)
                # junction_set.append_junction(junction)
                # junction_link.append(prv_link)

        if dbf_rec['nxtLanes'] is not None:
            nxtLanes = dbf_rec['nxtLanes'].split(';')

            if len(nxtLanes) == 1:
                nxt_link = nxtLanes[0].split(':')
                nxt_link_id = nxt_link[0]
                if nxt_link_id in link_set.lines:
                    end_node = link_set.lines[nxt_link_id].from_node
                else:
                    end_node = Node(link_id+'E')
                    end_node.point = shp_rec.points[-1]
                    node_set.nodes[end_node.idx] = end_node
            else:
                end_node = None
                for links in nxtLanes:
                    nxt_link = links.split(':')
                    nxt_link_id = nxt_link[0]
                    if nxt_link_id in link_set.lines:
                        end_node = link_set.lines[nxt_link_id].from_node
                if end_node is None:
                    end_node = Node(link_id+'E')
                    end_node.point = shp_rec.points[-1]
                    node_set.nodes[end_node.idx] = end_node

                # junction = Junction(_id=line['properties']['fid'])
                # junction.add_jc_node(end_node)
                # junction_set.append_junction(junction)
                # junction_link.append(nxt_link)

        link = Link(points=shp_rec.points, idx=link_id, lazy_point_init=False)
        link.link_type = line_type
        link.link_type_def = 'TomTom_v2105a'
        link.set_from_node(start_node)
        link.set_to_node(end_node)
        link.set_max_speed_kph(max_speed)
        if lane_mark_left in lane_mark_set.lanes:
            link.set_lane_mark_left(lane_mark_set.lanes[lane_mark_left])
        if lane_mark_right in lane_mark_set.lanes:
            link.set_lane_mark_right(lane_mark_set.lanes[lane_mark_right])

        link.link_type = line_type

        link.opp_traffic = opp_traffic
        link.is_entrance = is_entrance
        link.is_exit = is_exit

        link_set.lines[link.idx] = link

    # laneTrajectoryLane은 일단 안가져오기
    # trajectory_lines = map_info['laneTrajectoryLane']

    # t_shapes = trajectory_lines.shapes()
    # t_records  = trajectory_lines.records()
    # t_fields = trajectory_lines.fields

    # if len(t_shapes) != len(t_records):
    #     raise BaseException('[ERROR] len(shapes) != len(records)')

    # for i in range(len(t_shapes)):
    #     shp_rec = t_shapes[i]
    #     dbf_rec = t_records[i]

    #     shp_rec.points = np.array(shp_rec.points)
    #     shp_rec.z = np.array(shp_rec.z)
    #     shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
    #     shp_rec.points = convert_points(shp_rec.points)
    #     shp_rec.points -= origin
        
    #     link_id = dbf_rec['id']

    #     if dbf_rec['prev'] is not None:
    #         prvLanes = dbf_rec['prev'].split(';')
    #         if len(prvLanes) == 1:
    #             prv_link = prvLanes[0].split(':')
    #             prv_link_id = prv_link[0]
    #             if prv_link_id in link_set.lines:
    #                 start_node = link_set.lines[prv_link_id].to_node
    #             else:
    #                 start_node = Node(link_id+'S')
    #                 start_node.point = shp_rec.points[0]
    #                 node_set.nodes[start_node.idx] = start_node
    #         else:
    #             start_node = None
    #             for links in prvLanes:
    #                 prv_link = links.split(':')
    #                 prv_link_id = prv_link[0]
    #                 if prv_link_id in link_set.lines:
    #                     start_node = link_set.lines[prv_link_id].to_node
    #             if start_node is None:
    #                 start_node = Node(link_id+'S')
    #                 start_node.point = shp_rec.points[0]
    #                 node_set.nodes[start_node.idx] = start_node

    #             # junction = Junction(_id=line['properties']['fid'])
    #             # junction.add_jc_node(start_node)
    #             # junction_set.append_junction(junction)
    #             # junction_link.append(prv_link)

    #     if dbf_rec['next'] is not None:
    #         nxtLanes = dbf_rec['next'].split(';')

    #         if len(nxtLanes) == 1:
    #             nxt_link = nxtLanes[0].split(':')
    #             nxt_link_id = nxt_link[0]
    #             if nxt_link_id in link_set.lines:
    #                 end_node = link_set.lines[nxt_link_id].from_node
    #             else:
    #                 end_node = Node(link_id+'E')
    #                 end_node.point = shp_rec.points[-1]
    #                 node_set.nodes[end_node.idx] = end_node
    #         else:
    #             end_node = None
    #             for links in nxtLanes:
    #                 nxt_link = links.split(':')
    #                 nxt_link_id = nxt_link[0]
    #                 if nxt_link_id in link_set.lines:
    #                     end_node = link_set.lines[nxt_link_id].from_node
    #             if end_node is None:
    #                 end_node = Node(link_id+'E')
    #                 end_node.point = shp_rec.points[-1]
    #                 node_set.nodes[end_node.idx] = end_node

    #             # junction = Junction(_id=line['properties']['fid'])
    #             # junction.add_jc_node(end_node)
    #             # junction_set.append_junction(junction)
    #             # junction_link.append(nxt_link)

    #     link = Link(points=shp_rec.points, idx=link_id, lazy_point_init=False)
    #     link.link_type = 1
    #     link.set_from_node(start_node)
    #     link.set_to_node(end_node)
        
    #     link_set.lines[link.idx] = link
    
    set_link_lane_change_from_shp(map_info['laneGroup'], link_set, junction_set)
    
    return node_set, link_set, junction_set



def set_link_lane_change_from_shp(sf, link_set, junction_set):

    # road_id = 1000

    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields
    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for ind in range(len(shapes)):
        shp_rec = shapes[ind]
        dbf_rec = records[ind]

        lanes = dbf_rec['lanes'].split(';')
        lane_change_list = []

        lane_change_list = list(reversed(lanes))
        ego_lane = 1
        # road_id += 1
        current_link = None

        if len(lane_change_list) > 1:
            road_change = False
            for i in range(len(lane_change_list)):
                current_link_id = lane_change_list[i]
                
                if current_link_id in link_set.lines:
                    current_link = link_set.lines[current_link_id]

                    current_link.road_id = dbf_rec['id']
                    current_link.ego_lane = ego_lane
                    ego_lane += 1
                    
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
                        else:
                            current_link.can_move_right_lane = False

                    if left_link_id in link_set.lines and current_link.ego_lane > 1:
                        left_link = link_set.lines[left_link_id]
                        current_link.set_left_lane_change_dst_link(left_link)
                        
                        if left_link.link_type == 'DRIVABLE_LANE':
                            current_link.can_move_left_lane = True
                        else:
                            current_link.can_move_left_lane = False

                    if current_link.link_type != 'DRIVABLE_LANE':
                        current_link.can_move_right_lane = False
                        current_link.can_move_left_lane = False
                      
        # 연결된 area가 2개 이상일 때 junction 만들기
        nextArea = dbf_rec['nextArea'].split(';')
        prevArea = dbf_rec['prevArea'].split(';')

        junction_flag = False
        set_junction_node = []
        if len(nextArea) > 1:
            junction_flag = True
            for ilane in lane_change_list:
                current_link = link_set.lines[ilane]
                if current_link.link_type != 'DRIVABLE_LANE':
                    continue
                set_junction_node.append(current_link.to_node)
                for tlink in current_link.to_node.to_links:
                    set_junction_node.append(tlink.to_node)

        if len(prevArea) > 1:
            junction_flag = True
            for ilane in lane_change_list:
                current_link = link_set.lines[ilane]
                if current_link.link_type != 'DRIVABLE_LANE':
                    continue
                set_junction_node.append(current_link.from_node)
                for flink in current_link.from_node.from_links:
                    set_junction_node.append(flink.from_node)

        if junction_flag:
            junction = Junction()
            set_junction_node = list(set(set_junction_node))
            for inode in set_junction_node:
                junction.add_jc_node(inode)
            junction_set.append_junction(junction, create_new_key=True)   




def create_lane_marking_from_shp(map_info, origin):

    node_set = NodeSet()
    lane_set = LaneBoundarySet()

    sf = map_info['singleBorder']
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields
    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
        shp_rec.points = convert_points(shp_rec.points)
        shp_rec.points -= origin
        
        lane_marking_id = dbf_rec['id']

        start_node = Node(lane_marking_id+'S')
        start_node.point = shp_rec.points[0]
        node_set.nodes[start_node.idx] = start_node

        end_node = Node(lane_marking_id+'E')
        end_node.point = shp_rec.points[-1]
        node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=shp_rec.points, idx=lane_marking_id)
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)

        lane_boundary.lane_color = dbf_rec['color'].lower()
        lane_boundary = convert_string_to_laneType(dbf_rec['type'], lane_boundary)
        
        lane_set.lanes[lane_boundary.idx] = lane_boundary

    overlapped_node = error_fix.search_overlapped_node(node_set, 0.1)
    nodes_of_no_use = error_fix.repair_overlapped_node(overlapped_node)
    edit_node.delete_nodes(node_set, nodes_of_no_use)
    
    sf = map_info['laneBorder']
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields
    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]
        lane_marking_id = dbf_rec['id']
        if lane_marking_id not in lane_set.lanes:
            print('lane_marking_id({}) not in lane_mark_set'.format(lane_marking_id))
            continue
        clane = lane_set.lanes[lane_marking_id]
        # avro 파일과 text 스타일 똑같이
        pass_restr = dbf_rec['passRestr'].replace('_', '').lower()
        clane.pass_restr = pass_restr


    return node_set, lane_set


def create_traffic_sign_set_from_shp(sf, origin):
    # fid, id, type, subtype, shape, heading, colors, add_info, faceWidth, faceHeight, add_data, verDate
    ts_set = SignalSet()
    
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields
    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
        shp_rec.points = convert_points(shp_rec.points)
        shp_rec.points -= origin

        sign_id = dbf_rec['id']
        width = dbf_rec['faceWidth']
        height = dbf_rec['faceHeight']
        heading = dbf_rec['heading']
        color = dbf_rec['colors']
        shape = dbf_rec['shape']
        sign_type = dbf_rec['type']
        sign_subtype = dbf_rec['subtype']

        traffic_sign = Signal(sign_id)
        traffic_sign.dynamic = False
        traffic_sign.orientation = '+'
        traffic_sign.country = 'US'     
            
        traffic_sign.type_def = 'tomtom'
        traffic_sign.type = sign_type
        traffic_sign.sub_type = sign_type
        
        traffic_sign.height = height
        traffic_sign.width = width
        traffic_sign.heading = heading
        traffic_sign.point = shp_rec.points[0]
        ts_set.signals[traffic_sign.idx] = traffic_sign

    return ts_set
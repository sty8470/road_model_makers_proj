import numpy as np
import struct
import uuid
import base64 
import re
import avro.schema
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter

from lib.mgeo.class_defs import *
from lib.mgeo.edit.funcs import edit_node
from lib.mgeo.utils import error_fix

from lib.tomtom.tomtom_converter import *
from random import *


def create_speed_restrictions_from_avro(map_info, origin):
    speed_set = dict()
    speed_restrictions = map_info['SpeedRestriction']
    
    for item in speed_restrictions:
        speed_id = str(uuid.UUID(bytes=struct.pack('>qq', item['entity']['UUID']['mostSigBits'], item['entity']['UUID']['leastSigBits'])))
        restrict_info = next(bitem for bitem in item['attributes'] if bitem['ddctType'] == -1019393843)
        speed_info = int(next(value['value'] for value in restrict_info['nsoAttributes'] if value['ddctType'] == 1579600761))
        speed_max = True if next(value['value']['ddctType'] for value in restrict_info['nsoAttributes'] if value['ddctType'] == 1508516011) == 772807679 else False
        speed_unit = 'Mph' # NOTE(hjp): can't find this inside TT avro
        speed_set[speed_id] = {'speed':speed_info, 'is_max':speed_max, 'unit':speed_unit}
        
        assignment = item['associations']
        for association in assignment:
            assoc_link_id = str(uuid.UUID(bytes=struct.pack('>qq',
                association['otherFeature']['UUID']['mostSigBits'],
                association['otherFeature']['UUID']['leastSigBits'])))
            speed_set[speed_id][assoc_link_id] = dict()
            
            for attribute in association['attributes']:
                for nso in attribute['nsoAttributes']:
                    if nso['ddctType'] == -224675254:
                        speed_set[speed_id][assoc_link_id]['end'] = nso['value']
                    elif nso['ddctType'] == -2020684723:
                        speed_set[speed_id][assoc_link_id]['start'] = nso['value']

    return speed_set


def create_node_link_set_from_avro(map_info, lane_mark_set, origin):

    speed_set = create_speed_restrictions_from_avro(map_info, origin)
    center_line_item = map_info['LaneCenterLine']
    # laneTrajectoryLane은 일단 안가져오기
    trajectory_line_item = map_info['LaneTrajectoryLine']
    line_items = [center_line_item, trajectory_line_item]
    # line_items = [center_line_item]

    node_set, link_set = make_link_set(speed_set, lane_mark_set, line_items, origin)
    # overlapped node를 먼저 제거하고 양 옆 차선 정보 생성
    overlapped_node = error_fix.search_overlapped_node(node_set, 0.1)
    nodes_of_no_use = error_fix.repair_overlapped_node(overlapped_node)
    edit_node.delete_nodes(node_set, nodes_of_no_use)
    junction_set = set_link_lane_change_values_avro(map_info['LaneGroup'], link_set)
        
    return node_set, link_set, junction_set


def make_link_set(speed_set, lane_mark_set, line_items, origin):
    node_set = NodeSet()
    link_set = LineSet()
    junction_link = []
    for lines in line_items:
        for idx, line in enumerate(lines):
            points = []
            link_type = 'DRIVABLE_LANE'
            nxt_link_id_list = []
            prv_link_id_list = []
            lane_mark_left = None
            lane_mark_right = None
            max_speed = None
            in_region = False

            # [210512] tomtom geoJSON 데이터 추가 속성 추출
            opp_traffic = False
            is_entrance = False
            is_exit = False

            link_id = str(uuid.UUID(bytes=struct.pack('>qq',
                line['entity']['UUID']['mostSigBits'],
                line['entity']['UUID']['leastSigBits'])))

            for attributes in line['attributes']:
                # centerlines
                # 346157642: "LaneCenterLine",
                # -1291395400: "LaneCenterLine.EntranceLane",
                # -1777738272: "LaneCenterLine.ExitLane",
                # 244390646: "LaneCenterLine.Geometries",
                # -1165827340: "LaneCenterLine.LaneType",
                # 11320660: "LaneCenterLine.Length",
                # -572916081: "LaneCenterLine.OpposingTrafficPossible",
                # 871265832: "LaneCenterLine.SourceQuality",
                # 728941090: "LaneCenterLine.Width",
                # -1934776132: "LaneCenterLineOfLaneGroup",

                att_ddctType = convert_ddctType(attributes['ddctType'])

                if 'Geometries' in att_ddctType:
                    for nsoAttributes in attributes['nsoAttributes']:
                        nso_ddctType = convert_ddctType(nsoAttributes['ddctType'])
                        if nso_ddctType == 'DetailedGeometry.type':
                            # value WKT : Well-Known Text
                            pass

                        elif nso_ddctType == 'DetailedGeometry.geometry':
                            # value Base64
                            points_type, points, in_region = convert_string_to_points_avro(nsoAttributes['value'])

                elif 'LaneType' in att_ddctType:
                    link_type = attributes['value']

                # [210512] tomtom geoJSON 데이터 추가 속성 추출
                # True 일 경우에만 데이터에 들어가있음
                elif 'OpposingTrafficPossible' in att_ddctType:
                    opp_traffic = attributes['value']

                elif 'EntranceLane' in att_ddctType:
                    is_entrance = attributes['value']

                elif 'ExitLane' in att_ddctType:
                    is_exit = attributes['value']

            if not in_region:
                continue

            for associations in line['associations']:
                # associations
                # 370245627: "LaneConnection",
                # 1518724947: "LeftLaneBorderOfLane",
                # -344801492: "RightLaneBorderOfLane",
                # -1934776132: "LaneCenterLineOfLaneGroup",
                # 852205264: "LaneGroup",

                # otherFeature
                # 346157642: "LaneCenterLine",
                # -1268011471: "LaneBorder",
                # 852205264: "LaneGroup",

                ass_ddctType = convert_ddctType(associations['entity']['ddctType'])

                if ass_ddctType == 'LaneConnection':
                    if associations['associationType'] == 'TARGET':
                        nxt_link_id = str(uuid.UUID(bytes=struct.pack('>qq', 
                                associations['otherFeature']['UUID']['mostSigBits'], 
                                associations['otherFeature']['UUID']['leastSigBits'])))
                        nxt_link_id_list.append(nxt_link_id)

                    if associations['associationType'] == 'SOURCE':
                        prv_link_id = str(uuid.UUID(bytes=struct.pack('>qq', 
                                associations['otherFeature']['UUID']['mostSigBits'], 
                                associations['otherFeature']['UUID']['leastSigBits'])))
                        prv_link_id_list.append(prv_link_id)

                elif ass_ddctType == 'LeftLaneBorderOfLane':
                    lane_mark_left = str(uuid.UUID(bytes=struct.pack('>qq', 
                            associations['otherFeature']['UUID']['mostSigBits'], 
                            associations['otherFeature']['UUID']['leastSigBits'])))
                
                elif ass_ddctType == 'RightLaneBorderOfLane':
                    lane_mark_right = str(uuid.UUID(bytes=struct.pack('>qq', 
                            associations['otherFeature']['UUID']['mostSigBits'], 
                            associations['otherFeature']['UUID']['leastSigBits'])))
                
                elif ass_ddctType == 'LaneGroup':
                    lane_group_id = str(uuid.UUID(bytes=struct.pack('>qq', 
                            associations['otherFeature']['UUID']['mostSigBits'], 
                            associations['otherFeature']['UUID']['leastSigBits'])))
                
                elif ass_ddctType == 'SpeedAssignment':
                    speed_id = str(uuid.UUID(bytes=struct.pack('>qq', 
                            associations['otherFeature']['UUID']['mostSigBits'], 
                            associations['otherFeature']['UUID']['leastSigBits'])))
                    if speed_id in speed_set:
                        if speed_set[speed_id]['is_max'] is True:
                            if link_id in speed_set[speed_id]:
                                max_speed = speed_set[speed_id]['speed']
                                speed_unit = speed_set[speed_id]['unit']
                                speed_offset = speed_set[speed_id][link_id]['start']
                                
            # assign properties to Link()
            points = np.array(points)
            points -= origin

            start_node = None
            for prv_link_id in prv_link_id_list:
                if prv_link_id in link_set.lines:
                    start_node = link_set.lines[prv_link_id].to_node
            if start_node is None:
                start_node = Node(link_id+'S')
                start_node.point = points[0]
                node_set.nodes[start_node.idx] = start_node

            if len(prv_link_id_list) > 1:
                junction_link.append(prv_link_id)

            end_node = None
            for nxt_link_id in nxt_link_id_list:
                if nxt_link_id in link_set.lines:
                    end_node = link_set.lines[nxt_link_id].from_node
            if end_node is None:
                end_node = Node(link_id+'E')
                end_node.point = points[-1]
                node_set.nodes[end_node.idx] = end_node

            if len(nxt_link_id_list) > 1:
                junction_link.append(nxt_link_id)
                
            link = Link(points=points, 
                    idx=link_id, 
                    link_type=link_type, 
                    lazy_point_init=False)
            link.link_type_def = 'TomTom_v2105a'
            link.set_from_node(start_node)
            link.set_to_node(end_node)
            if max_speed is not None:
                link.set_max_speed_kph(max_speed)
                link.set_speed_unit(speed_unit)
                link.set_speed_region(speed_offset)

            link.opp_traffic = opp_traffic
            link.is_entrance = is_entrance
            link.is_exit = is_exit
            
            link_set.lines[link.idx] = link

            # lane_mark 데이터가 lane_marking_set에 있는지(?)
            if lane_mark_left in lane_mark_set.lanes:
                link.set_lane_mark_left(lane_mark_set.lanes[lane_mark_left])
            if lane_mark_right in lane_mark_set.lanes:
                link.set_lane_mark_right(lane_mark_set.lanes[lane_mark_right])

    return node_set, link_set


def set_link_lane_change_values_avro(group_list, link_set):

    junction_set = JunctionSet()
    # road_id = 1000
    # junction 들어가는 도로 찾기
    for idx, group in enumerate(group_list):

        # 연결된 area가 2개 이상일 때 junction 만들기
        nextArea = []
        prevArea = []
        for item in group['associations']:
            if item['associationType'] == 'TARGET' and convert_ddctType(item['entity']['ddctType']) == 'RoadAreaConnection':
                item_id = str(uuid.UUID(bytes=struct.pack('>qq', item['entity']['UUID']['mostSigBits'], item['entity']['UUID']['leastSigBits'])))
                nextArea.append(item_id)
            if item['associationType'] == 'SOURCE' and convert_ddctType(item['entity']['ddctType']) == 'RoadAreaConnection':
                item_id = str(uuid.UUID(bytes=struct.pack('>qq',  item['entity']['UUID']['mostSigBits'], item['entity']['UUID']['leastSigBits'])))
                prevArea.append(item_id)
        

        group_id = str(uuid.UUID(bytes=struct.pack('>qq', 
                group['entity']['UUID']['mostSigBits'], 
                group['entity']['UUID']['leastSigBits'])))
        # 시퀀스 작은게 오른쪽, 큰게 왼쪽
        # 5(오른쪽만) 4 3 2 1(왼쪽만)
        lane_change_list = []

        for association in group['associations']:
            # 1752572445: "RoadNetworkArctoRoadArea",
            # -1208863320: "RoadAreaConnection",
            # -1934776132: "LaneCenterLineOfLaneGroup",
            ass_ddctType = convert_ddctType(association['entity']['ddctType'])
            if ass_ddctType == 'LaneCenterLineOfLaneGroup':
                sequence = association['sequence']
                msb = association['otherFeature']['UUID']['mostSigBits']
                lsb = association['otherFeature']['UUID']['leastSigBits']
                link_id = str(uuid.UUID(bytes=struct.pack('>qq', msb, lsb)))
                lane_change_list.insert(sequence-1, link_id)
        

        lane_change_list = list(reversed(lane_change_list))
        ego_lane = 1

        if len(lane_change_list) > 1:
            road_change = False
            for i in range(len(lane_change_list)):
                current_link_id = lane_change_list[i]
                
                if current_link_id in link_set.lines:
                    current_link = link_set.lines[current_link_id]

                    current_link.road_id = group_id
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

    return junction_set


def create_lane_marking_set_from_avro(origin, laneBorder):
    node_set = NodeSet()
    lane_set = LaneBoundarySet()

    for i, lane in enumerate(laneBorder):
        
        msb = lane['entity']['UUID']['mostSigBits']
        lsb = lane['entity']['UUID']['leastSigBits']
        lane_id = uuid.UUID(bytes=struct.pack('>qq', msb, lsb))

        points = []
        lane_color = None
        lane_shape = None
        in_region = False

        for attr in lane['attributes']:
            ddctType = convert_ddctType(attr['ddctType'])


            if ddctType == 'LaneBorder.LaneBorderComponent': # -32884444
                for nso in attr['nsoAttributes']:
                    nso_ddctType = convert_ddctType(nso['ddctType'])
                    if nso_ddctType == 'LaneBorderComponent.Geometries': # 979833510
                        for nso_attr in nso['nsoAttributes']:

                            geoAttriDT = convert_ddctType(nso_attr['ddctType'])
                            if geoAttriDT == 'DetailedGeometry.type':
                                # value WKT : Well-Known Text
                                geo_type = nso_attr['value']

                            elif geoAttriDT == 'DetailedGeometry.geometry':
                                # value Base64
                                list_type, points, in_region = convert_string_to_points_avro(nso_attr['value'])                                

                    elif nso_ddctType == 'LaneBorderComponent.BorderColor': # -1836887369
                        lane_color = nso['value']

                    elif nso_ddctType == 'LaneBorderComponent.BorderType': # -1885629980
                        lane_shape = nso['value']

            elif ddctType == 'LaneBorder.Length':
                lane_length = attr['value'] # 그냥 숫자

            elif ddctType == 'LaneBorder.PassingRestriction':
                # Passing Restriction value
                # 294780589: "PassingRestriction.LaneBorderpassingfromleftandright" = 0
                # 1485072440: "PassingRestriction.LaneBorderpassingnotallowed" = 3
                # 886768577: "PassingRestriction.LaneBorderpassingonlylefttoright" = 1
                # -2092663395: "PassingRestriction.LaneBorderpassingonlyrighttoleft" = 2
                lanePassingRestrictionType = convert_ddctType(attr['value']['ddctType'])
                pass_restr = lanePassingRestrictionType.split('.')[1].replace('LaneBorder', '')

            elif ddctType == 'LaneBorder.Width':
                lane_width = attr['value']

        if not in_region:
            continue

        # 데이터 이용해서 lane 만들기
        lane_marking_id = str(lane_id)
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

        # lane_boundary.lane_type
        # lane_boundary.lane_width
        # lane_boundary.dash_interval_L1
        # lane_boundary.dash_interval_L2
        lane_boundary.lane_color = [lane_color.lower()]
        lane_boundary.pass_restr = pass_restr
        lane_boundary = convert_string_to_laneType(lane_shape, lane_boundary)
        # lane_boundary.lane_shape = laneShape

        # lane_boundary.fill_in_points_evenly_accor_to_leng(2)

        lane_set.lanes[lane_boundary.idx] = lane_boundary

    return node_set, lane_set


def create_traffic_sign_set_from_avro(origin, ts_list):
    ts_set = SignalSet()
    for ts in ts_list:
        in_region = False
        msb = ts['entity']['UUID']['mostSigBits']
        lsb = ts['entity']['UUID']['leastSigBits']
        ts_id = str(uuid.UUID(bytes=struct.pack('>qq', msb, lsb)))
        # "-1736719413": "TrafficSign",
        # "903380502": "TrafficSign.AdditionalInfo",
        # "-221155645": "TrafficSign.Category",
        # "-1386077372": "TrafficSign.Color",
        # "1546173379": "TrafficSign.FaceSize",
        # "-541012267": "TrafficSign.Geometries",
        # "-1692856105": "TrafficSign.Heading",
        # "1380281186": "TrafficSign.Shape",
        # "405386971": "TrafficSign.Subcategory",
        # "956186098": "TrafficSign.VerificationDate",
        for attr in ts['attributes']:
            ddctType = convert_ddctType(attr['ddctType'])

            if ddctType == 'TrafficSign.Subcategory':
                sub_category = attr['value']

            elif ddctType == 'TrafficSign.AdditionalInfo':
                color = attr['value']

            elif ddctType == 'TrafficSign.VerificationDate':
                verification_date = attr['value']

            elif ddctType == 'TrafficSign.Shape':
                shape = attr['value']

            elif ddctType == 'TrafficSign.Heading':
                heading = attr['value']

            elif ddctType == 'TrafficSign.FaceSize':
                for i in attr['nsoAttributes']:
                    ddct_i = convert_ddctType(i['ddctType'])
                    if ddct_i == 'BoundingBox.Height':
                        height = i['value']
                    elif ddct_i == 'BoundingBox.Width':
                        width = i['value']

            elif ddctType == 'TrafficSign.Color':
                # 색상 두개임
                color = attr['value']

            elif ddctType == 'TrafficSign.Geometries':
                geo_string = attr['nsoAttributes'][1]['value']
                list_type, points, in_region = convert_string_to_points_avro(geo_string)
                # mcity 데이터 기준으로 만든거라, lat/lng이 아니라 좌표가 들어가 있어서 바꿔야 할 수도 있음


            elif ddctType == 'TrafficSign.Category':
                category = attr['value']

        if not in_region:
            continue

        # point = transformer_point(point)
        # mcity 데이터 기준으로 만든거라, lat/lng이 아니라 좌표가 들어가 있어서 바꿔야 할 수도 있음
        point = np.array(points[0])
        point -= origin

        traffic_sign = Signal(ts_id)
        traffic_sign.dynamic = False
        traffic_sign.orientation = '+'
        traffic_sign.country = 'US'     
            
        traffic_sign.type_def = 'tomtom'
        traffic_sign.type = category
        traffic_sign.sub_type = sub_category
        # 사이즈 설정
        traffic_sign.height = height
        traffic_sign.width = width
        traffic_sign.heading = heading
        traffic_sign.point = point
        ts_set.signals[traffic_sign.idx] = traffic_sign

    return ts_set
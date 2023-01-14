import os 
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import numpy as np

from lib.mgeo.class_defs import *

import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

import csv
import json
import ast
import shutil

from lib.deepmap.deepmap_converter import *


class DeepMapImporter:

    def geojson_to_mgeo(self, iuput_folder_path):
        json_files, map_data = read_json_files(iuput_folder_path)

        origin = json_files['UCDavis_CenterLines']['features'][0]['geometry']['coordinates'][0]
        origin = np.array(origin)

        link_items = json_files['UCDavis_CenterLines']['features']
        road_items = json_files['UCDavis_Outlines']['features']
        feature_items = json_files['UCDavis_Features']['features']
        naviga_items = json_files['UCDavis_Navigable_Boundaries']['features']

        node_set, link_set, junction_set = self.create_node_link_set_from_json(origin, link_items, road_items)
        
        traffic_sign_set = self.create_traffic_sign_set_from_json(origin, link_set, feature_items)
        traffic_light_set = self.create_traffic_light_set_from_json(origin, link_set, feature_items)
        lane_node_set, lane_boundary_set = self.create_lane_marking_set_from_json(origin, road_items, naviga_items, feature_items)
        
        # 위경도를 좌표로 바꿔서(converter에 change_geometry) 저장을 해놓은 데이터(UCDavis_Outlines_geo)를 이용해서 차선 데이터
        # lane_node_set, lane_boundary_set = self.create_lane_marking_set_from_json_geo(origin, json_files['UCDavis_Outlines_geo'], naviga_items, feature_items)


        mgeo_planner_map = MGeo(
            node_set = node_set,
            link_set = link_set, 
            junction_set = junction_set,
            sign_set = traffic_sign_set, 
            light_set = traffic_light_set,
            lane_node_set = lane_node_set,
            lane_boundary_set = lane_boundary_set)

        mgeo_planner_map.set_origin(origin)
        
        return mgeo_planner_map

    def create_node_link_set_from_json(self, origin, link_items, road_items):

        node_set = NodeSet()
        link_set = LineSet()
        junction_set = JunctionSet()

        for item in link_items:
            points = item['geometry']['coordinates']
            points = np.array(points)
            points -= origin
            idx = str(item['properties']['parentLaneElId'])
            link = Link(
                points=points, 
                idx=idx,
                lazy_point_init=False)
            
            # link.fill_in_points_evenly_accor_to_leng(2)
            # link_type_def 추가
            link.link_type_def = 'deepmap'

            link_set.lines[link.idx] = link

        lines = link_set.lines
        idx = 0
        for line in lines:
            create_node_point = [lines[line].points[0], lines[line].points[-1]]
            for i, point in enumerate(create_node_point):
                node_id = 'ND{}'.format(idx)
                idx += 1
                node = Node(node_id)
                node.point = point
                if i == 0:
                    node.add_to_links(lines[line])
                elif i == 1:
                    node.add_from_links(lines[line])
                node_set.nodes[node.idx] = node

        tl_dict = dict()
        ts_dict = dict()
        
        for item in road_items:
            link_item = link_set.lines[str(item['properties']['id'])]
            # link에 차선 변경 가능 정보
            left_link_id_list = item['properties']['leftLanesList']
            right_link_id_list = item['properties']['rightLanesList']
            related_signal = item['properties']['restrictions']['trafficDirection'].lower()

            # BICYCLE...은 어쩐담
            vehicle_type = item['properties']['restrictions']['allowedVehicleTypesList']
            if vehicle_type[0] == 'BICYCLE':
                link_item.link_type = '0'

            if len(left_link_id_list) > 0:
                link_item.can_move_left_lane = True
                for l_id in left_link_id_list:
                    link_item.set_left_lane_change_dst_link(link_set.lines[str(l_id)])
            if len(right_link_id_list) > 0:
                link_item.can_move_right_lane = True
                for l_id in right_link_id_list:
                    link_item.set_right_lane_change_dst_link(link_set.lines[str(l_id)])

            # speedLimitValue/speedLimitUnit
            speedLimitValue = item['properties']['restrictions']['speedLimitValue']
            # mph to kph
            link_item.set_max_speed_kph(int(speedLimitValue * 1.609))
            link_item.related_signal = related_signal
            
            # 연결되어있는 Link 찾기
            if len(item['properties']['associationInfo']) > 0:
                if 'associatedSignalsList' in item['properties']['associationInfo']:
                    associatedSignalsList = item['properties']['associationInfo']['associatedSignalsList']
                    for signal in associatedSignalsList:
                        signal_id = str(signal['featureId'])
                        if tl_dict.get(signal_id):
                            tl_dict[signal_id].append(link_item.idx)
                        else:
                            tl_dict[signal_id] = [link_item.idx]
                elif 'associatedSignsList' in item['properties']['associationInfo']:
                    associatedSignsList = item['properties']['associationInfo']['associatedSignsList']
                    for signal in associatedSignsList:
                        signal_id = str(signal['featureId'])
                        if ts_dict.get(signal_id):
                            ts_dict[signal_id].append(link_item.idx)
                        else:
                            ts_dict[signal_id] = [link_item.idx]
                
        return node_set, link_set, junction_set


    def create_traffic_sign_set_from_json(self, origin, link_set, feature_items):

        traffic_sign_set = SignalSet()
            
        ts_dict = dict()

        for item in feature_items:
            if item['properties']['featureType'] == 'TrafficSign':
                sign_id = str(item['properties']['featureId'])
                try:
                    link_id_list = ts_dict[sign_id]
                except:
                    link_id_list = []
                point = item['geometry']['coordinates'][0][0]
                point = np.array(point)
                point -= origin

                traffic_sign = Signal(sign_id)
                traffic_sign.link_id_list = link_id_list
                traffic_sign.dynamic = False
                traffic_sign.orientation = '+'
                traffic_sign.country = 'US'

                # LINK ID List를 사용해서 Link 참조 List 구성
                for i in range(len(traffic_sign.link_id_list)):
                    if traffic_sign.link_id_list[i] in link_set.lines:
                        traffic_sign.link_list.append(link_set.lines[traffic_sign.link_id_list[i]])
                    else:
                        raise BaseException('[ERROR] Could not find link ID mapped in link set.')
            
                for i in range(len(traffic_sign.link_list)):
                    if traffic_sign.road_id == None or traffic_sign.road_id == '':
                        traffic_sign.road_id = traffic_sign.link_list[i].road_id
                    else :
                        # Signal이 참조하고 있는 lane들이 서로 다른 road id를 가진 경우 예외 발생
                        if traffic_sign.road_id != traffic_sign.link_list[i].road_id :
                            raise BaseException('[ERROR] The lanes referenced by signal have different road id.')      
                
                traffic_sign.type = 'US'
                traffic_sign.sub_type = item['properties']['signType']
                # 사이즈 설정
                # type, sub_type 값을 설정한 후 호출해야 함
                traffic_sign.set_size()

                traffic_sign.point = point
                
                traffic_sign_set.signals[traffic_sign.idx] = traffic_sign

        return traffic_sign_set

    def create_traffic_light_set_from_json(self, origin, link_set, feature_items):
        
        traffic_light_set = SignalSet()
            
        tl_dict = dict()

        for item in feature_items:
            if item['properties']['featureType'] == 'TrafficSignal':
                signal_id = str(item['properties']['featureId'])
                try:
                    link_id_list = tl_dict[signal_id]
                except:
                    link_id_list = []
                point = item['geometry']['coordinates'][0][0]
                point = np.array(point)
                point -= origin

                traffic_light = Signal(signal_id)
                traffic_light.link_id_list = link_id_list
                traffic_light.dynamic = True
                traffic_light.orientation = '+'
                traffic_light.country = 'US'

                # LINK ID List를 사용해서 Link 참조 List 구성
                for i in range(len(traffic_light.link_id_list)):
                    if traffic_light.link_id_list[i] in link_set.lines:
                        traffic_light.link_list.append(link_set.lines[traffic_light.link_id_list[i]])
                    else:
                        raise BaseException('[ERROR] Could not find link ID mapped in link set.')
            
                for i in range(len(traffic_light.link_list)):
                    if traffic_light.road_id == None or traffic_light.road_id == '':
                        traffic_light.road_id = traffic_light.link_list[i].road_id
                    else :
                        # Signal이 참조하고 있는 lane들이 서로 다른 road id를 가진 경우 예외 발생
                        if traffic_light.road_id != traffic_light.link_list[i].road_id :
                            raise BaseException('[ERROR] The lanes referenced by signal have different road id.')      

                traffic_light.type = 'US'
                traffic_light.sub_type = item['properties']['signalType']
                # 사이즈 설정
                # type, sub_type 값을 설정한 후 호출해야 함
                traffic_light.set_size()

                traffic_light.point = point
                
                traffic_light_set.signals[traffic_light.idx] = traffic_light

        return traffic_light_set

    def create_lane_marking_set_from_json(self, origin, outlines, navigas, features):

        node_set = NodeSet()
        lane_set = LaneBoundarySet()

        for item in outlines:
            points = item['geometry']['coordinates']
            points = np.array(points)
            points -= origin

            idx = 'C{}'.format(str(item['properties']['id']))

            # left/right 겹치는 것
            leftBoundaryLine = item['properties']['leftBoundaryLine']
            leftLinePoints = convert_points(leftBoundaryLine['geometry'])
            try:
                leftLineColor = leftBoundaryLine['lineColor']
                leftLineType = leftBoundaryLine['lineType']
            except:
                leftLineColor = "WHITE"
                leftLineType = "SOLID"

            left_start_node = Node('L{}S'.format(idx))
            left_start_node.point = leftLinePoints[0]
            node_set.nodes[left_start_node.idx] = left_start_node

            left_end_node = Node('L{}E'.format(idx))
            left_end_node.point = leftLinePoints[-1]
            node_set.nodes[left_end_node.idx] = left_end_node
                
            left_lane_marking = LaneBoundary(points=leftLinePoints, idx='L{}'.format(idx))
            left_lane_marking.set_from_node(left_start_node)
            left_lane_marking.set_to_node(left_end_node)
                
            lane_set.lanes[left_lane_marking.idx] = left_lane_marking

            # if len(item['properties']['rightLanesList']) == 0:
            rightBoundaryLine = item['properties']['rightBoundaryLine']
            rightLinePoints = convert_points(rightBoundaryLine['geometry'])
            try:
                rightLineColor = rightBoundaryLine['lineColor']
                rightLineType = rightBoundaryLine['lineType']
            except:
                rightLineColor = "WHITE"
                rightLineType = "SOLID"

            right_start_node = Node('R{}S'.format(idx))
            right_start_node.point = rightLinePoints[0]
            node_set.nodes[right_start_node.idx] = right_start_node

            right_end_node = Node('R{}E'.format(idx))
            right_end_node.point = rightLinePoints[-1]
            node_set.nodes[right_end_node.idx] = right_end_node

            right_lane_marking = LaneBoundary(points=rightLinePoints, idx='R{}'.format(idx))
            right_lane_marking.set_from_node(right_start_node)
            right_lane_marking.set_to_node(right_end_node)
                
            lane_set.lanes[right_lane_marking.idx] = right_lane_marking
    
        for item in navigas:
            points = item['geometry']['coordinates']
            points = np.array(points)
            points -= origin
            idx = 'N{}'.format(str(item['properties']['parentLaneElId']))
            lane_boundary = LaneBoundary(
                points=points, 
                idx=idx)

            start_node = Node('{}S'.format(idx))
            start_node.point = points[0]
            node_set.nodes[start_node.idx] = start_node

            end_node = Node('{}E'.format(idx))
            end_node.point = points[-1]
            node_set.nodes[end_node.idx] = end_node
            
            lane_boundary.set_from_node(start_node)
            lane_boundary.set_to_node(end_node)
            lane_boundary.lane_type_def = 'US'
            lane_boundary.lane_type = [599]
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = [ 'undefined' ]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 1
            lane_boundary.dash_interval_L2 = 1
            lane_boundary.lane_type_offset = [0]
            lane_set.lanes[lane_boundary.idx] = lane_boundary
        
        for item in features:
            if item['geometry']['type'] == "LineString":
                if item['properties']['featureType'] == "Stopline":
                    points = item['geometry']['coordinates']
                    points = np.array(points)
                    points -= origin
                    idx = '{}'.format(item['properties']['featureId'])
                    item_type = item['properties']['featureType']

                    start_node = Node('R{}S'.format(idx))
                    start_node.point = leftLinePoints[0]
                    node_set.nodes[start_node.idx] = start_node

                    end_node = Node('R{}E'.format(idx))
                    end_node.point = leftLinePoints[-1]
                    node_set.nodes[end_node.idx] = end_node

                    lane_boundary = LaneBoundary(points=points, idx='{}'.format(idx))
                    lane_boundary.set_from_node(start_node)
                    lane_boundary.set_to_node(end_node)
                    lane_boundary.lane_shape =  [ "Solid" ]
                    lane_boundary.lane_color = [ "white" ]
                    lane_boundary.lane_width = 0.15
                    lane_boundary.dash_interval_L1 = 1
                    lane_boundary.dash_interval_L2 = 1
                    lane_boundary.lane_type_offset = [0]
                    # lane_boundary.fill_in_points_evenly_accor_to_leng(2)
                    lane_set.lanes[lane_boundary.idx] = lane_boundary
                    
            # centerLine = item['properties']['centerLine']
            # centerLinePoints = convert_points(centerLine['geometry'])
            
        return node_set, lane_set


    def create_lane_marking_set_from_json_geo(self, origin, outlines, navigas, features):
        node_set = NodeSet()
        lane_set = LaneBoundarySet()

        for item in outlines:
            points = item['geometry']['coordinates']

            idx = str(item['properties']['id'])

            # left/right 겹치는 것
            leftBoundaryLine = item['properties']['leftBoundaryLine']
            points = leftBoundaryLine['geometry']
            points -= origin
            leftLinePoints = np.array(points)
            try:
                leftLineColor = leftBoundaryLine['lineColor']
                leftLineType = leftBoundaryLine['lineType']
            except:
                leftLineColor = "WHITE"
                leftLineType = "SOLID"

            if leftLineColor == "WHITE":
                leftLineColor = ["white"]

            if leftLineColor == "YELLOW":
                leftLineColor = ["yellow"]

            if leftLineType == "BROKEN":
                leftLineType = [ "Broken" ]

            if leftLineType == "SOLID":
                leftLineType = [ "Solid" ]

            if leftLineType == "DOUBLE SOLID":
                leftLineType = [ "Solid", "Solid" ]


            left_start_node = Node('L{}S'.format(idx))
            left_start_node.point = leftLinePoints[0]
            node_set.nodes[left_start_node.idx] = left_start_node

            left_end_node = Node('L{}E'.format(idx))
            left_end_node.point = leftLinePoints[-1]
            node_set.nodes[left_end_node.idx] = left_end_node
                
            left_lane_marking = LaneBoundary(points=leftLinePoints, idx='L{}'.format(idx))
            left_lane_marking.set_from_node(left_start_node)
            left_lane_marking.set_to_node(left_end_node)
            left_lane_marking.lane_type_def = 'US'
            left_lane_marking.lane_type = [503]
            left_lane_marking.lane_shape = leftLineType
            left_lane_marking.lane_color = leftLineColor
            left_lane_marking.lane_width = 0.15
            left_lane_marking.dash_interval_L1 = 1
            left_lane_marking.dash_interval_L2 = 1

            left_lane_marking.lane_type_offset = [0]
            # left_lane_marking.fill_in_points_evenly_accor_to_leng(2)
            lane_set.lanes[left_lane_marking.idx] = left_lane_marking

            # if len(item['properties']['rightLanesList']):
            rightBoundaryLine = item['properties']['rightBoundaryLine']
            points = rightBoundaryLine['geometry']
            points -= origin
            rightLinePoints = np.array(points)
            try:
                rightLineColor = rightBoundaryLine['lineColor']
                rightLineType = rightBoundaryLine['lineType']
            except:
                rightLineColor = "WHITE"
                rightLineType = "SOLID"


            if rightLineColor == "WHITE":
                rightLineColor = [ "white" ]

            if rightLineColor == "YELLOW":
                rightLineColor = [ "yellow" ]

            if rightLineType == "BROKEN":
                rightLineType = [ "Broken" ]

            if rightLineType == "SOLID":
                rightLineType = [ "Solid" ]

            if rightLineType == "DOUBLE SOLID":
                rightLineType = [ "Solid", "Solid" ]

            right_start_node = Node('R{}S'.format(idx))
            right_start_node.point = rightLinePoints[0]
            node_set.nodes[right_start_node.idx] = right_start_node

            right_end_node = Node('R{}E'.format(idx))
            right_end_node.point = rightLinePoints[-1]
            node_set.nodes[right_end_node.idx] = right_end_node

            right_lane_marking = LaneBoundary(points=rightLinePoints, idx='R{}'.format(idx))
            right_lane_marking.set_from_node(right_start_node)
            right_lane_marking.lane_type_def = 'US'
            right_lane_marking.lane_type = [503]
            right_lane_marking.set_to_node(right_end_node)
            right_lane_marking.lane_shape = leftLineType
            right_lane_marking.lane_color = leftLineColor
            right_lane_marking.lane_width = 0.15
            right_lane_marking.dash_interval_L1 = 1
            right_lane_marking.dash_interval_L2 = 1
            right_lane_marking.lane_type_offset = [0]
            # right_lane_marking.fill_in_points_evenly_accor_to_leng(2)
            lane_set.lanes[right_lane_marking.idx] = right_lane_marking
    
        for item in navigas:
            points = item['geometry']['coordinates']
            points = np.array(points)
            points -= origin
            idx = 'N{}'.format(str(item['properties']['parentLaneElId']))
            lane_boundary = LaneBoundary(
                points=points, 
                idx=idx)

            start_node = Node('{}S'.format(id))
            start_node.point = points[0]
            node_set.nodes[start_node.idx] = start_node

            end_node = Node('{}E'.format(id))
            end_node.point = points[-1]
            node_set.nodes[end_node.idx] = end_node
            
            lane_boundary.set_from_node(start_node)
            lane_boundary.set_to_node(end_node)
            lane_boundary.lane_type_def = 'US'
            lane_boundary.lane_type = [599]
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = [ 'undefined' ]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 1
            lane_boundary.dash_interval_L2 = 1
            lane_boundary.lane_type_offset = [0]
            lane_set.lanes[lane_boundary.idx] = lane_boundary
        
        for item in features:
            if item['geometry']['type'] == "LineString":
                if item['properties']['featureType'] == "Stopline":
                    points = item['geometry']['coordinates']
                    points = np.array(points)
                    points -= origin
                    idx = '{}'.format(item['properties']['featureId'])
                    item_type = item['properties']['featureType']

                    start_node = Node('S{}S'.format(idx))
                    start_node.point = leftLinePoints[0]
                    node_set.nodes[start_node.idx] = start_node

                    end_node = Node('S{}E'.format(idx))
                    end_node.point = leftLinePoints[-1]
                    node_set.nodes[end_node.idx] = end_node

                    lane_boundary = LaneBoundary(points=points, idx='ST{}'.format(idx))
                    lane_boundary.set_from_node(start_node)
                    lane_boundary.set_to_node(end_node)
                    lane_boundary.lane_shape =  [ "Solid" ]
                    lane_boundary.lane_color = [ "white" ]
                    lane_boundary.lane_width = 0.15
                    lane_boundary.dash_interval_L1 = 1
                    lane_boundary.dash_interval_L2 = 1
                    lane_boundary.lane_type_offset = [0]
                    # lane_boundary.fill_in_points_evenly_accor_to_leng(2)
                    lane_set.lanes[lane_boundary.idx] = lane_boundary
                    
        return node_set, lane_set


if __name__ == "__main__":
    importer = DeepMapImporter()
    iuput_folder_path = 'D:/road_model_maker/rsc/map_data/deepmap_json_UCDavis'
    importer.geojson_to_mgeo(iuput_folder_path)
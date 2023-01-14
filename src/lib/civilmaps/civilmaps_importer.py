import os
import sys

from lib.mgeo.class_defs.mgeo import MGeo
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(current_path + '/../lib/common/')

import json
import csv
import numpy as np

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.class_defs import *

from lib.civilmaps.civilmaps_converter import *
from lib.civilmaps.civilmaps_exporter import *

"""
Editor에 MGeo(Node+Link+...) import 하는 class
1. geojson_to_lane
    civilmaps 1차 데이터에는 Link 정보가 없음
    차선 데이터를 이용한 Lane Node와 Lane marking 데이터를 불러옴
    - type/sub_type이 정해져 있지 않아서 type = US, sub_type = name

2. geojson_to_mgeo
    - Node가 없으면 초기 카메라 위치 설정이 안되는 에러가 발생 > Node = Lane Node
"""

class CivilmapsImporter:
    
    def lane_marking_set_from_json(self, origin, items):
        
        node_set = NodeSet()
        lane_set = LaneBoundarySet()

        for item in items:
            id = item['id']
            name = item['properties']['asset']['name']
            points = item['geometry']['coordinates']
            points = convert_points(points)
            points -= origin

            lane_boundary = LaneBoundary(points=points, idx=id)
            lane_boundary = convert_line_name(name, lane_boundary)

            if lane_boundary is not None:

                start_node = Node('{}S'.format(id))
                start_node.point = points[0]
                node_set.nodes[start_node.idx] = start_node

                end_node = Node('{}E'.format(id))
                end_node.point = points[-1]
                node_set.nodes[end_node.idx] = end_node

                lane_boundary.set_from_node(start_node)
                lane_boundary.set_to_node(end_node)
                lane_set.lanes[lane_boundary.idx] = lane_boundary

        return node_set, lane_set

    def traffic_sign_set_from_json(self, origin, items):

        ts_set = SignalSet()

        for item in items:
            id = item['id']
            name = item['properties']['asset']['name']
            points = item['geometry']['coordinates']
            points = convert_points(points)
            points -= origin

            traffic_sign_name = get_traffic_sign(name)
            if traffic_sign_name:
                point = points_to_point(points)
                traffic_sign = Signal(id)
                traffic_sign.dynamic = False
                traffic_sign.orientation = '+'
                traffic_sign.country = 'US'
                traffic_sign.type = 'US'
                traffic_sign.sub_type = traffic_sign_name
                # 사이즈 설정
                # type, sub_type 값을 설정한 후 호출해야 함
                traffic_sign.set_size()
                traffic_sign.point = point
                
                ts_set.signals[traffic_sign.idx] = traffic_sign
                
        return ts_set


    def traffic_light_set_from_json(self, origin, items):

        tl_set = SignalSet()

        for item in items:
            id = item['id']
            name = item['properties']['asset']['name']
            points = item['geometry']['coordinates']
            points = convert_points(points)
            points -= origin

            traffic_light_name = get_traffic_light(name)
            if traffic_light_name:
                point = points_to_point(points)
                traffic_light = Signal(id)
                traffic_light.dynamic = False
                traffic_light.orientation = '+'
                traffic_light.country = 'US'
                traffic_light.type = 'US'
                traffic_light.sub_type = traffic_light_name
                # 사이즈 설정
                # type, sub_type 값을 설정한 후 호출해야 함
                traffic_light.set_size()
                traffic_light.point = point
                
                tl_set.signals[traffic_light.idx] = traffic_light
                
        return tl_set

        

    def geojson_to_mgeo(self, iuput_folder_path):

        json_files, map_data = read_json_files(iuput_folder_path)
        items = json_files['WGS_geofeatures_raw_feature_collection']['features']
        origin = np.array(get_origin(items[0]))

        node_set = NodeSet()
        link_set = LineSet()
        # 차선데이터
        lane_node_set, lane_boundary_set = self.lane_marking_set_from_json(origin, items)
        ts_set = self.traffic_sign_set_from_json(origin, items)
        tl_set = self.traffic_light_set_from_json(origin, items)

        # civilmaps 데이터에 링크 데이터 없어서 None값 넣어놓음
        mgeo_planner_map = MGeo(node_set=lane_node_set,
                                            link_set=link_set, 
                                            lane_node_set=lane_node_set, 
                                            lane_boundary_set=lane_boundary_set,
                                            sign_set=ts_set, 
                                            light_set=tl_set)
        mgeo_planner_map.set_origin(origin)

        return mgeo_planner_map



if __name__ == "__main__":
    iuput_folder_path = 'D:/road_model_maker/rsc/map_data/civilmaps_geojson_sample'
    importer = CivilmapsImporter()
    importer.geojson_to_mgeo(iuput_folder_path)
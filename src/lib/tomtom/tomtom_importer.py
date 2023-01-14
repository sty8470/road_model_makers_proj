import os
import sys
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
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common


from lib.common.logger import Logger

from lib.tomtom.tomtom_converter import *

from lib.tomtom.tomtom_load_avro import *
from lib.tomtom.tomtom_load_shp import *
from lib.tomtom.tomtom_load_geojson import *
from lib.tomtom.tomtom_load_json import *


"""
tomtom >> MCity
    1. avro : avro_to_map > tomtom_load_avro
    2. shp : shp_to_map > tomtom_load_shp
    3. geojson : geojson_to_map > tomtom_load_geojson
    4. json(avro) : json_to_map > tomtom_load_json
"""



class TomTomImporter:
    

    def avro_to_map(self, input_path, extract_setting):
        # 추출 영역에 대한 설정
        if not extract_setting == None and extract_setting['extract_type'] == 'region':
            set_boundary(float(extract_setting['latitude_min']), float(extract_setting['longitude_min']), 
                float(extract_setting['latitude_max']), float(extract_setting['longitude_max']))

        map_info = read_avro_files(input_path)

        origin, zone = get_origin(map_info['LaneCenterLine'])
        origin = np.array(origin)
        # Logger.log_info('Origin : {}, UTM_ZONE: {}'.format(origin, zone))
        print('Origin : {}, UTM_ZONE: {}'.format(origin, zone))

        lane_node_set, lane_boundary_set = create_lane_marking_set_from_avro(origin, map_info['LaneBorder'])
        node_set, link_set, junction_set = create_node_link_set_from_avro(map_info, lane_boundary_set, origin)
        sign_set = create_traffic_sign_set_from_avro(origin, map_info['TrafficSign'])

        mgeo_planner_map = MGeo(node_set = node_set, 
                                            link_set = link_set,
                                            junction_set = junction_set,
                                            lane_node_set = lane_node_set, 
                                            lane_boundary_set = lane_boundary_set,
                                            sign_set = sign_set)
        mgeo_planner_map.set_origin(origin)
        mgeo_planner_map.global_coordinate_system = Proj('+proj=utm +zone={} +datum=WGS84 +units=m +no_defs'.format(zone)).srs

        # 추출 영역 설정 초기화
        clear_boundary()
        return mgeo_planner_map


    def shp_to_map(self, input_path):
        # Get File List
        map_info, filename_map = shp_common.read_shp_files(input_path)
        origin, zone = transformer_point(shp_common.get_first_shp_point(map_info['laneCenterline']))
        origin = np.array(origin)
        Logger.log_info('Origin : {}, UTM_ZONE: {}'.format(origin, zone))
    
        lane_node_set, lane_boundary_set = create_lane_marking_from_shp(map_info, origin)
        node_set, link_set, junction_set = create_node_and_link_from_shp(map_info, lane_boundary_set, origin)
        # junction_set = set_link_lane_change_from_shp(map_info['laneGroup'], link_set)
        sign_set = create_traffic_sign_set_from_shp(map_info['trafficSigns'], origin)
        mgeo_planner_map = MGeo(node_set = node_set,
                                            link_set = link_set,
                                            junction_set = junction_set,
                                            lane_node_set = lane_node_set,
                                            lane_boundary_set = lane_boundary_set,
                                            sign_set = sign_set)
        mgeo_planner_map.set_origin(origin)
        mgeo_planner_map.global_coordinate_system = Proj('+proj=utm +zone={} +datum=WGS84 +units=m +no_defs'.format(zone)).srs
        # 42dot 처럼 prj 파일을 이용하면 "+proj=longlat +ellps=WGS84 +no_defs " 이 정보만 출력됨
        # prj_file = os.path.normpath(os.path.join(input_path, 'laneCenterline.prj'))
        # mego_planner_map.set_coordinate_system_from_prj_file(prj_file)
        return mgeo_planner_map

    def geojson_to_map(self, input_path):

        map_info, filename_map = geojson_common.read_geojson_files(input_path)
        origin_points = map_info['laneCenterline']['features'][0]['geometry']['coordinates']
        while len(origin_points) == 1:
            origin_points = origin_points[0]
            
        origin, zone = transformer_point(origin_points[0])
        origin = np.array(origin)
        Logger.log_info('Origin : {}, UTM_ZONE: {}'.format(origin, zone))
        
        lane_node_set, lane_set = create_lane_marking_from_geojson(map_info, origin)
        node_set, link_set, junction_set, lane_mark_set = create_node_and_link_from_geojson(map_info, lane_set, origin, lane_node_set)
        sign_set = create_traffic_sign_set_from_geojson(map_info, origin)

        mgeo_planner_map = MGeo(node_set = node_set, 
                                            link_set = link_set,
                                            junction_set = junction_set,
                                            lane_node_set = lane_node_set, 
                                            lane_boundary_set = lane_mark_set,
                                            sign_set = sign_set)
        mgeo_planner_map.set_origin(origin)
        mgeo_planner_map.global_coordinate_system = Proj('+proj=utm +zone={} +datum=WGS84 +units=m +no_defs'.format(zone)).srs

        return mgeo_planner_map

    def json_to_map(self, input_path):

        map_info = read_json_files(input_path)

        origin, zone = transformer_point(map_info['LaneCenterLine'][0]['attributes']['detail_geo'][0])
        origin = np.array(origin)
        Logger.log_info('Origin : {}, UTM_ZONE: {}'.format(origin, zone))

        node_set, link_set = create_node_and_link_from_json(map_info['LaneCenterLine'], origin)
        lane_node_set, lane_set = create_lane_marking_set_from_json(map_info['LaneBorder'], origin)
        set_link_lane_change_values_json(link_set, map_info['LaneGroup'])

        mego_planner_map = MGeo(node_set = node_set, 
                                            link_set = link_set,
                                            lane_node_set = lane_node_set, 
                                            lane_boundary_set = lane_set)
        mego_planner_map.set_origin(origin)

        return mego_planner_map
        

if __name__ == u'__main__':
    importer = TomTomImporter()
    # input_path = 'D:\\road_model_maker\\rsc\\map_data\\tomtom_geojson_US_CA_SanFrancisco_Interstate101'
    # importer.geojson_to_map(input_path)
    input_path = 'C:\\Users\\user\\Documents\\road_model_maker\\data\\hdmap\\tomtom_geojson_US_NV_LasVegas'
    importer.geojson_to_map(input_path)
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(current_path + '/../lib/common/')
sys.path.append(current_path + '/../../lib/common/')

import json
import csv
import numpy as np

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.class_defs import *
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common


from lib.tomtom.test_tomtom_load_avro import *
from lib.tomtom.test_tomtom_converter import *


"""
tomtom >> MCity
    1. avro : avro_to_map > tomtom_load_avro
    2. shp : shp_to_map > tomtom_load_shp
"""

class TestTomTomImporter:
    

    def avro_to_map(self, input_path):
        import time

        start_time = time.time_ns()
        job_start_time = start_time

        files_info = get_avro_files_path(input_path)
        # map_info = read_avro_files(input_path)
        
        origin, zone = get_origin_fa(files_info['LaneCenterLine'])
        # origin = get_origin(map_info['LaneCenterLine'])
        origin = np.array(origin)
        print('Origin : {}, UTM_ZONE: {}'.format(origin, zone))

        lane_node_set, lane_boundary_set = create_lane_marking_set_from_avro_fa(origin, files_info['LaneBorder'])
        end_time = time.time_ns()
        print('create_lane_marking_set_from_avro : {}ns'.format(end_time - start_time))

        start_time = end_time
        node_set, link_set, junction_set = create_node_link_set_from_avro_fa(files_info, lane_marking_set, origin)
        end_time = time.time_ns()
        print('create_node_link_set_from_avro : {}ns'.format(end_time - start_time))

        start_time = end_time
        sign_set = create_traffic_sign_set_from_avro_fa(origin, files_info['TrafficSign'])
        end_time = time.time_ns()
        print('create_traffic_sign_set_from_avro : {}ns'.format(end_time - start_time))

        mgeo_planner_map = MGeo(node_set = node_set, 
                                            link_set = link_set,
                                            junction_set = junction_set,
                                            lane_node_set=lane_node_set, 
                                            lane_boundary_set=lane_boundary_set,
                                            sign_set = sign_set)
        mgeo_planner_map.set_origin(origin)
        mgeo_planner_map.global_coordinate_system = Proj('+proj=utm +zone={} +datum=WGS84 +units=m +no_defs'.format(zone)).srs

        # 추출 영역 설정 초기화
        clear_boundary()        
        end_time = time.time_ns()
        print('total processed time : {}ns'.format(end_time - job_start_time))

        return mgeo_planner_map
        
if __name__ == u'__main__':
    importer = TestTomTomImporter()

    # input_path = 'D:\\road_model_maker\\rsc\\map_data\\tomtom_geojson_US Interstate 101'
    # importer.geojson_to_map(input_path)
    # # D:\지도\TomTom\HDMap_AVRO
    # input_path = 'D:\\road_model_maker\\rsc\\map_data\\tomtom_avro_M-City'
    input_path = os.path.join(current_path, '../../../', 'rsc/map_data/tomtom_avro_M-City')
    print(input_path)
    importer.avro_to_map(input_path)
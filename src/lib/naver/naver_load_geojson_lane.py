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
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

from lib.naver.naver_geojson import *
from lib.naver.naver_hdmap_importer import NaverHDMapImporter

def load_naver_lane(input_path):

    output_path = os.path.join(input_path, 'output') 
    relative_loc = True
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
    except OSError:
        print('Error: Creating directory. ' +  output_path)

    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__)) 

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    # Get File List
    map_info, filename_map = geojson_common.read_geojson_files(input_path)
    # map_info['A1_LANE']  중앙선, 길가장자리,차선, 안전지대구역선
    # map_info['A2_STOP']  정지선
    # 차선

    # map_info['A3_LINK']
    # drive_path

    # map_info['B2_SURFSIGN_DIRECTION']
    # 101직진 102우회전 103좌회전 104직우회전 105직좌회전 106좌회전 유턴 107유턴 108전체방향
    # 110 직진 유턴 201좌합류 202우합류

    # map_info['B2_SURFSIGN_PLANE']
    # 9랑 97은 없는데 뭐지

    node_file_name = next((item for item in map_info.keys() if 'NODE' in item), False)
    link_file_name = next((item for item in map_info.keys() if 'LINK' in item), False)
    lane_file_name = next((item for item in map_info.keys() if 'LANE' in item), False)
    stop_file_name = next((item for item in map_info.keys() if 'STOP' in item), False)

    surface_plane_file_name = next((item for item in map_info.keys() if 'PLANE' in item), False)

    origin = map_info[node_file_name]['features'][0]['geometry']['coordinates']
    print('[INFO] Origin Set as: ', origin)

    importer = NaverHDMapImporter()
    node_link_mgeo = importer.import_geojson(input_path)

    node_set = node_link_mgeo.node_set
    link_set = node_link_mgeo.link_set

    lane_node_set = NodeSet()
    lane_boundary_set = LaneBoundarySet()

    a1_lane = map_info[lane_file_name]['features']
    a2_stop = map_info[stop_file_name]['features']

    for lane in a1_lane:
        lane_marking_id = lane['properties']['id']
        points = lane['geometry']['coordinates']
        points -= np.array(origin)

        if is_out_of_xy_range(points, [-780, 210], [-283, 725]) != False:
            continue

        start_node = Node(lane_marking_id+'S')
        start_node.point = points[0]
        lane_node_set.nodes[start_node.idx] = start_node

        end_node = Node(lane_marking_id+'E')
        end_node.point = points[-1]
        lane_node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=points, idx=lane_marking_id)
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)

        lane_type = lane['properties']['lanecode']

        if lane_type == '1': # 중앙선
            lane_boundary.lane_type = [501]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3
            lane_boundary.lane_color = ['yellow']
            lane_boundary.lane_shape = ["Solid"]
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

        elif lane_type == '2': # U턴구역선
            lane_boundary.lane_type = [502]
            lane_boundary.lane_width = 0.35 # 너비가 0.3~0.45 로 규정되어있다.
            lane_boundary.dash_interval_L1 = 0.5
            lane_boundary.dash_interval_L2 = 0.5
            lane_boundary.lane_shape = [ "Broken" ]
            lane_boundary.lane_color = ["white"]
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

        elif lane_type == '3': # 차선
            lane_boundary.lane_type = [503]
            lane_boundary.lane_width = 0.15
            
            # 도시 
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 5

            # # 지방도로
            # lane_boundary.dash_interval_L1 = 5
            # lane_boundary.dash_interval_L2 = 8

            # # 자동차전용도로, 고속도로
            # lane_boundary.dash_interval_L1 = 10
            # lane_boundary.dash_interval_L2 = 10
            lane_boundary.lane_color = ['white']
            lane_boundary.lane_shape = ["Broken"]
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

        elif lane_type == '4': # 버스전용차선
            lane_boundary.lane_type = [504]
            lane_boundary.lane_width = 0.15 
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = ["blue"]
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

        elif lane_type == '5': # 길가장자리구역선
            lane_boundary.lane_type = [505]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = ["white"]
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

        elif lane_type == '6': # 진로변경제한선
            lane_boundary.lane_type = [506]
            lane_boundary.lane_width = 0.15 #점선일 때 너비가 0.1 ~ 0.5로, 넓을 수도 있다.
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = ["white"]
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)
        
        elif lane_type == '7': # 길가장자리구역선
            lane_boundary.lane_type = [505]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 점선을 사용하지 않아 문서에 없음. 임의로 설정.
            lane_boundary.lane_color = ['yellow']
            lane_boundary.lane_shape = ["Solid"]
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

        elif lane_type == '8': # 주정차금지선
            lane_boundary.lane_type = [515]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = ["yellow"]
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

        elif lane_type == '9': # 주정차금지선
            lane_boundary.lane_type = [515]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = ["yellow"]
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

        elif lane_type == '11': # 안전지대구역선
            lane_boundary.lane_type = [531]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.lane_color = ['yellow']
            lane_boundary.lane_shape = ["Solid"]
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)
        
        elif lane_type == '12' or lane_type == '99': # 99
            lane_boundary.lane_type = [599]
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.dash_interval_L2 = 3 # 문서에 없어 임의로 설정.
            lane_boundary.lane_color = ['yellow']
            lane_boundary.lane_shape = ["Solid"]
            # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

        else:
            raise BaseException('Unexpected lane_type = {}'.format(lane_type))

        lane_boundary.lane_type_def = 'naver'
        lane_boundary.lane_type_offset = [0]

        lane_boundary_set.lanes[lane_boundary.idx] = lane_boundary

    for lane in a2_stop:
        lane_marking_id = lane['properties']['id']
        points = lane['geometry']['coordinates']
        points -= np.array(origin)

        if is_out_of_xy_range(points, [-780, 210], [-283, 725]) != False:
            continue

        start_node = Node(lane_marking_id+'S')
        start_node.point = points[0]
        lane_node_set.nodes[start_node.idx] = start_node

        end_node = Node(lane_marking_id+'E')
        end_node.point = points[-1]
        lane_node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=points, idx=lane_marking_id)
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)

        lane_boundary.lane_type = [530]
        lane_boundary.lane_width = 0.6
        lane_boundary.dash_interval_L1 = 0 # 문서에 없어 임의로 설정.
        lane_boundary.dash_interval_L2 = 0 # 문서에 없어 임의로 설정.
        lane_boundary.lane_color = ['white']
        lane_boundary.lane_shape = ["Solid"]

        lane_boundary.lane_type_def = 'naver'
        lane_boundary.lane_type_offset = [0]
        # lane_boundary.fill_in_points_evenly_accor_to_leng(10)

        lane_boundary_set.lanes[lane_boundary.idx] = lane_boundary 

    #TODO : TEST
    singlecrosswalk_set = SingleCrosswalkSet()
    b2_surface_plane = map_info[surface_plane_file_name]['features']

    for cw in b2_surface_plane:
        cw_id = cw['properties']['id']
        points = cw['geometry']['coordinates'][0]
        cw_type = cw['properties']['signtype']
        if cw_type == '4' or cw_type == '5' or cw_type == '6':
            points -= np.array(origin)
            crosswalk = SingleCrosswalk(points, cw_id, cw_type)
            singlecrosswalk_set.append_data(crosswalk, False)

    mgeo_planner_map = MGeo(
        node_set=node_set, link_set=link_set, lane_node_set=lane_node_set, lane_boundary_set=lane_boundary_set, scw_set=singlecrosswalk_set )

    mgeo_planner_map.set_origin(origin)

    return mgeo_planner_map

def is_out_of_xy_range(points, xlim, ylim):

    x = points[:,0]
    y = points[:,1]
    z = points[:,2]

    if x.max() < xlim[0] or xlim[1] < x.min():
        x_out = True
    else:
        x_out = False

    # y축에 대해
    if y.max() < ylim[0] or ylim[1] < y.min():
        y_out = True
    else:
        y_out = False
        
    return x_out or y_out
    
if __name__ == u'__main__':
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\naverlabs_geojson_pangyo'
    load_naver_lane(input_path)
    
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')

import math
import json
import csv
import numpy as np

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.class_defs import *
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

from lib.stryx.stryx_geojson import *


def load_road(input_path):

    output_path = os.path.join(input_path, 'output')  
    relative_loc = True

    map_info, filename_map = geojson_common.read_geojson_files(input_path)

    origin = map_info['A1_NODE']['features'][0]['geometry']['coordinates']
    print('[INFO] Origin Set as: ', origin)

    surf_line_list = map_info['B2_SURFACELINEMARK']['features']
    c3_roadedge = map_info['C3_VEHICLEPROTECTIONSAFETY']['features']

    node_set = NodeSet()
    lane_set = LineSet()

    for each_line in surf_line_list:
        lane_marking_id = each_line['id']
        points = np.array(each_line['geometry']['coordinates'])
        points -= np.array(origin)
        start_node = Node(lane_marking_id+'S')
        start_node.point = points[0]
        node_set.nodes[start_node.idx] = start_node

        end_node = Node(lane_marking_id+'E')
        end_node.point = points[-1]
        node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=points, idx=lane_marking_id)
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)

        # lane_boundary.fill_in_points_evenly_accor_to_leng(0.3)

        lane_set.lines[lane_boundary.idx] = lane_boundary

    for each_line in c3_roadedge:
        lane_marking_id = each_line['id']
        points = np.array(each_line['geometry']['coordinates'])
        points -= np.array(origin)
        start_node = Node(lane_marking_id+'S')
        start_node.point = points[0]
        node_set.nodes[start_node.idx] = start_node

        end_node = Node(lane_marking_id+'E')
        end_node.point = points[-1]
        node_set.nodes[end_node.idx] = end_node

        lane_boundary = LaneBoundary(points=points, idx=lane_marking_id)
        lane_boundary.set_from_node(start_node)
        lane_boundary.set_to_node(end_node)

        # lane_boundary.fill_in_points_evenly_accor_to_leng(0.3)

        lane_set.lines[lane_boundary.idx] = lane_boundary

    mgeo_planner_map = MGeo(
        node_set=node_set, link_set=lane_set)

    mgeo_planner_map.set_origin(origin)

    return mgeo_planner_map


def setProp(nodes, lines, origin):

    # ??????????????? ?????? ?????????????????? ???????????? ?????? ????????????
    # ??????????????? ????????? lane code?????? ????????? ????????? ??????

    node_set = nodes
    lane_set = LineSet()

    for line in lines:
        lane_boundary = lines[line]
        # ?????? ?????? ?????? ?????? ??????
        lane_boundary.lane_type_def = 'NGII_SHP2'
        
        lane_type = lane_boundary.lane_type
        if lane_type == 501: # ?????????
            lane_boundary.lane_type = 501
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = "yellow"


        elif lane_type == 5011: # ????????????
            lane_boundary.lane_type = 5011
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3
            lane_boundary.lane_shape = [ "Broken" ]
            lane_boundary.lane_color = "yellow"

        elif lane_type == 502: # ???????????????
            lane_boundary.lane_type = 502
            lane_boundary.lane_width = 0.35 # ????????? 0.3~0.45 ??? ??????????????????.
            lane_boundary.dash_interval_L1 = 0.5
            lane_boundary.dash_interval_L2 = 0.5
            lane_boundary.lane_shape = [ "Broken" ]
            lane_boundary.lane_color = "white"

        elif lane_type == 503: # ??????
            lane_boundary.lane_type = 503
            lane_boundary.lane_width = 0.15
            
            # ?????? 
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 5
            lane_boundary.lane_shape = [ "Broken" ]
            lane_boundary.lane_color = "white"

            # # ????????????
            # lane_boundary.dash_interval_L1 = 5
            # lane_boundary.dash_interval_L2 = 8

            # # ?????????????????????, ????????????
            # lane_boundary.dash_interval_L1 = 10
            # lane_boundary.dash_interval_L2 = 10

        elif lane_type == 504: # ??????????????????
            lane_boundary.lane_type = 504
            lane_boundary.lane_width = 0.15 
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = "blue"

        elif lane_type == 505: # ????????????????????????
            lane_boundary.lane_type = 505
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # ????????? ???????????? ?????? ????????? ??????. ????????? ??????.
            lane_boundary.dash_interval_L2 = 3 # ????????? ???????????? ?????? ????????? ??????. ????????? ??????.
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = "white"
        
        elif lane_type == 506:  # ?????????????????????
            lane_boundary.lane_type = 506
            lane_boundary.lane_width = 0.15 #????????? ??? ????????? 0.1 ~ 0.5???, ?????? ?????? ??????.
            lane_boundary.dash_interval_L1 = 3
            lane_boundary.dash_interval_L2 = 3
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = "white"

        elif lane_type == 515: # ??????????????????
            lane_boundary.lane_type = 515
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # ????????? ?????? ????????? ??????.
            lane_boundary.dash_interval_L2 = 3 # ????????? ?????? ????????? ??????.
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = "yellow"

        elif lane_type == 525: # ?????????
            lane_boundary.lane_type = 525
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 0.75 # 0.5 ~ 1.0
            lane_boundary.dash_interval_L2 = 0.75 # 0.5 ~ 1.0
            lane_boundary.lane_shape = [ "Broken" ]
            lane_boundary.lane_color = "white"

        elif lane_type == 530: # ?????????
            lane_boundary.lane_type = 530
            lane_boundary.lane_width = 0.6 # ???????????? 0.3 ~ 0.6
            lane_boundary.dash_interval_L1 = 0 # ?????????????????? ????????? ??????
            lane_boundary.dash_interval_L2 = 0 # ?????????????????? ????????? ??????.
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = "white"

        elif lane_type == 531: # ????????????
            lane_boundary.lane_type = 531
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # ????????? ?????? ????????? ??????.
            lane_boundary.dash_interval_L2 = 3 # ????????? ?????? ????????? ??????.
            # 531??? null????????? ????????? ??????
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = "yellow"

        elif lane_type == 535: # ???????????????
            lane_boundary.lane_type = 535
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # ????????? ?????? ????????? ??????.
            lane_boundary.dash_interval_L2 = 3 # ????????? ?????? ????????? ??????.
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = "white"

        elif lane_type == 599: # ?????????
            lane_boundary.lane_type = 599
            lane_boundary.lane_width = 0.15
            lane_boundary.dash_interval_L1 = 3 # ????????? ?????? ????????? ??????.
            lane_boundary.dash_interval_L2 = 3 # ????????? ?????? ????????? ??????.
            lane_boundary.lane_shape = [ "Solid" ]
            lane_boundary.lane_color = "yellow"

        else:
            raise BaseException('Unexpected lane_type = {}'.format(lane_type))

        lane_set.lines[lane_boundary.idx] = lane_boundary

    mgeo_planner_map = MGeo(
        node_set=node_set, link_set=lane_set)

    mgeo_planner_map.set_origin(origin)

    return mgeo_planner_map

def load_mgeo_planner_lane(input_path):

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

    mgeo_planner_map = load_road(input_path)

    output_file = os.path.join(output_path, 'all_lane.csv')

    fileOpenMode = 'a'
    with open(output_file, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            lines = mgeo_planner_map.link_set.lines
            for line in lines:
                for point in lines[line].points:
                    if relative_loc:
                        point_rel = list()
                        for i in range(len(point)):
                            point_rel.append(point[i])
                        writer.writerow(point_rel)
                        continue
                    else:
                        writer.writerow(point)

if __name__ == u'__main__':
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\stryx_mdl201120_SejongLakePark'
    load_mgeo_planner_lane(input_path)
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
from lib.mgeo.edit.funcs import edit_line
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

from lib.stryx.stryx_geojson import *

def export_road(input_path):

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

    map_info, filename_map = geojson_common.read_geojson_files(input_path)

    origin = map_info['A1_NODE']['features'][0]['geometry']['coordinates']
    print('[INFO] Origin Set as: ', origin)

    surf_line_list = map_info['B2_SURFACELINEMARK']['features']
    a2_path_list = map_info['A2_LINK']['features']
    b3_surfmark_list = map_info['B3_SURFACEMARK']['features']
    b4_crosswalk = map_info['B4_CROSSWALK']['features']
    d3_sidewalk = map_info['D3_SIDEWALK']['features']
    c3_roadedge = map_info['C3_VEHICLEPROTECTIONSAFETY']['features']
    
    output_file_name_prefix = ''
    output_file_name_suffix = '.csv'
    output_file_name_list = dict()
    type_name_list = list()
    
    for i in range(len(surf_line_list)):
        each_line = surf_line_list[i]
        obj_prop = each_line['properties']
        # 종류 추가함
        kind_str = surfline_kind_code_to_str(obj_prop['Kind'])

        if kind_str == 'Lane_Border' or kind_str == 'Lane_Center':
            # Border 이거나 CenterLine 이면 하나의 파일로 한다
            type_name = 'Lane_Center'
            if not (type_name in type_name_list):
                type_name_list.append(type_name)
                output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
                output_file_name_list[type_name] = output_file_name

        else:
            type_name = kind_str
            if not (type_name in type_name_list):
                type_name_list.append(type_name)
                output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
                output_file_name_list[type_name] = output_file_name
                
    # A2_LINK에서 나오는 파일들: 하나의 파일로 다 모은다
    type_name = 'DrivePath'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name

    # B3_SURFACEMARK 에서 Kind가 5321인 데이터를 찾는다
    # 이 데이터가 횡단보도이다
    type_name = 'Crosswalk'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name

    # D3_SIDEWALK
    type_name = 'Sidewalk'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name

    type_name = 'RoadEdge'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name

    for key in output_file_name_list.keys():
        output_file_name_list[key] = os.path.join(
            output_path, output_file_name_list[key])

    for key in output_file_name_list.keys():
        each_out = output_file_name_list[key]
        if os.path.exists(each_out):
            print('[WARNING] Removing an existing file... ({})'.format(each_out))
            os.remove(each_out)
        
        fileOpenMode = 'w'
        with open(each_out, fileOpenMode, newline='') as csvfile:
            continue
    for key in output_file_name_list.keys():
        each_out = output_file_name_list[key]
        print('[INFO] Created a new file: ({})'.format(each_out))


    # B2_SURFACELINEMARK에서 나오는 파일들
    node_set = NodeSet()
    lane_set = LineSet()
    for each_line in surf_line_list:
        lane_marking_id = each_line['properties']['id']
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

        # lane_boundary 간격조절
        edit_line.fill_in_points_evenly_accor_to_leng(lane_boundary, 0.5)

        lane_set.lines[lane_boundary.idx] = lane_boundary

    mgeo_planner_map = MGeo(
        node_set=node_set, link_set=lane_set)

    mgeo_planner_map.set_origin(origin)
    
    key = kind_str
    each_out = output_file_name_list[key]
    fileOpenMode = 'a'
    with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            lines = mgeo_planner_map.link_set.lines
            for line in lines:
                # lane_boundary 간격조절
                edit_line.fill_in_points_evenly_accor_to_leng(lines[line], 0.5)
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
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\stryx_mdl201203_KAIST_3rd'
    export_road(input_path)
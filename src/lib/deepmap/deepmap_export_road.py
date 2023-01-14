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

"""
road mesh로 내보낼 데이터가 여러개여서 따로 만듦
"""
iuput_folder_path = 'D:/road_model_maker/rsc/map_data/deepmap_json_UCDavis'

# geojson 파일 읽기CenterLineCenterLine
def read_json_files(iuput_folder_path):
    file_list = os.listdir(iuput_folder_path)
    json_file_list = [file for file in file_list if file.endswith(".json")]
    data = {}
    filename_map = {}
    for each_file in json_file_list:
        file_full_path = os.path.join(iuput_folder_path, each_file)
        filename, file_extension = os.path.splitext(each_file)
        key = filename
        with open(file_full_path, 'r', encoding='UTF8') as input_file:
            data[key] = json.load(input_file)
            abs_filename = os.path.normpath(os.path.join(iuput_folder_path, each_file))
            filename_map[key] = abs_filename
    return data, filename_map

# 위경도를 한번에 좌표변환해서 파일에 저장하기
# UCDavis_Outlines 값을 UCDavis_Outlines_geo로
def change_geometry(iuput_folder_path):
    json_files = read_json_files(iuput_folder_path)[0]
    default_file = os.path.join(iuput_folder_path, 'UCDavis_Outlines.json')
    new_file = os.path.join(iuput_folder_path, 'UCDavis_Outlines_geo.json')

    shutil.copy(default_file, new_file)
    items = {}
    for i, item in enumerate(json_files['UCDavis_Outlines']['features']):
        points = item['geometry']['coordinates']
        idx = str(item['properties']['id'])

        startLine = item['properties']['startLine']['geometry']
        Points = []
        for point in startLine:
            new_point = convert_point(point)
            Points.append(new_point)
        item['properties']['startLine']['geometry'] = Points

        terminationLine = item['properties']['terminationLine']['geometry']
        Points = []
        for point in terminationLine:
            new_point = convert_point(point)
            Points.append(new_point)
        item['properties']['terminationLine']['geometry'] = Points

        leftBoundaryLine = item['properties']['leftBoundaryLine']['geometry']
        Points = []
        for point in leftBoundaryLine:
            new_point = convert_point(point)
            Points.append(new_point)
        item['properties']['leftBoundaryLine']['geometry'] = Points

        rightBoundaryLine = item['properties']['rightBoundaryLine']['geometry']
        Points = []
        for point in rightBoundaryLine:
            new_point = convert_point(point)
            Points.append(new_point)
        item['properties']['rightBoundaryLine']['geometry'] = Points

        centerLine = item['properties']['centerLine']['geometry']
        # Points = []
        for line in centerLine:
            # point = {}
            # point['lat'] = line['lat']
            # point['lng'] = line['lng']
            # point['alt'] = line['alt']
            # new_point = convert_point(point)
            # Points.append(new_point)

            line['leftProjection'] =  convert_point(line['leftProjection'])
            line['rightProjection'] =  convert_point(line['rightProjection'])
            
        item['properties']['centerLine']['geometry'] = Points
        print("완료, {}".format(i))

    with open(new_file, 'w') as f:
        json.dump(json_files['UCDavis_Outlines']['features'], f, indent=4)


# DeepMap CenterLines 데이터 이용해서 차선 정보 만들기
# 위경도 좌표를 바꾸기 때문에 크기가 큰 데이터에서는 적합하지 않다.
def create_lane_slow(iuput_folder_path):
    json_files = read_json_files(iuput_folder_path)[0]

    origin = json_files['UCDavis_CenterLines']['features'][0]['geometry']['coordinates'][0]
    origin = np.array(origin)

    node_set = NodeSet()
    lane_set = LineSet()

    for item in json_files['UCDavis_Outlines']['features']:
        points = item['geometry']['coordinates']
        points = np.array(points)
        points -= origin

        idx = str(item['properties']['id'])

        # left/right 겹치는 것
        leftBoundaryLine = item['properties']['leftBoundaryLine']
        leftLinePoints = convert_points(leftBoundaryLine['geometry'])
        try:
            leftLineColor = leftBoundaryLine['lineColor']
            leftLineType = leftBoundaryLine['lineType']
        except:
            leftLineColor = "WHITE"
            leftLineType = "SOLID"

        left_start_node = Node('R{}S'.format(idx))
        left_start_node.point = leftLinePoints[0]
        node_set.nodes[left_start_node.idx] = left_start_node

        left_end_node = Node('R{}E'.format(idx))
        left_end_node.point = leftLinePoints[-1]
        node_set.nodes[left_end_node.idx] = left_end_node
            
        left_lane_marking = LaneBoundary(points=leftLinePoints, idx='L{}'.format(idx))
        left_lane_marking.set_from_node(left_start_node)
        left_lane_marking.set_to_node(left_end_node)
            
        lane_set.lines[left_lane_marking.idx] = left_lane_marking

        if len(item['properties']['rightLanesList']) == 0:
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
                
            lane_set.lines[right_lane_marking.idx] = right_lane_marking

        centerLine = item['properties']['centerLine']
        centerLinePoints = convert_points(centerLine['geometry'])
    # mgeo_planner_map = MGeo(node_set, lane_set)
        
    return node_set, lane_set


# MGeo Node랑 Link 데이터 만들기
def geojson_to_mgeo_node_link(center_lines, origin):
    node_set = NodeSet()
    link_set = LineSet()
    for item in center_lines:
        points = item['geometry']['coordinates']
        points = np.array(points)
        points -= origin
        idx = str(item['properties']['parentLaneElId'])
        link = Link(
            points=points, 
            idx=idx,
            lazy_point_init=False)
        # link.fill_in_points_evenly_accor_to_leng(2)
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
    mgeo_planner_map = MGeo(node_set, link_set)
    print("Center-line")
    return mgeo_planner_map

# UCDavis_Navigable_Boundaries 
def create_road_navigable(navis, origin):
    node_set = NodeSet()
    link_set = LineSet()
    for item in navis:
        points = item['geometry']['coordinates']
        points = np.array(points)
        points -= origin
        idx = str(item['properties']['parentLaneElId'])
        link = Link(
            points=points, 
            idx=idx,
            lazy_point_init=False)
        # link.fill_in_points_evenly_accor_to_leng(2)
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
    mgeo_planner_map = MGeo(node_set, link_set)
    print("Navigable_Boundaries-line")
    return mgeo_planner_map


# DeepMap 데이터 이용해서 road mesh(csv 파일) 만드는 과정
def create_road_boundaries():
        
    input_path = '../../../rsc/map_data/deepmap_json_UCDavis'
    output_path = '../../../rsc/map_data/deepmap_json_UCDavis/output'
    relative_loc = True

    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))   

    # inputPath = os.path.normcase(inputPath)
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)  

    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)   

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    json_files = read_json_files(input_path)[0]

    origin = json_files['UCDavis_CenterLines']['features'][0]['geometry']['coordinates'][0]
    origin = np.array(origin)

    output_file_name_prefix = ''
    output_file_name_suffix = '.csv'
    output_file_name_list = dict()
    type_name_list = list()
    
    for type_name in ['Lane_Boundaries', 'Lane_Border', 'Lane_Center', 'Lane_Navigable']:
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

    mgeo_planner_map = create_lane(json_files['UCDavis_Outlines_geo'], json_files['UCDavis_Features']['features'], origin)
    key = 'Lane_Border'
    each_out = output_file_name_list[key]
    fileOpenMode = 'a'
    with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            lines = mgeo_planner_map.lane_marking_set.lanes
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

    # center line
    mgeo_planner_map_center = geojson_to_mgeo_node_link(json_files['UCDavis_CenterLines']['features'], origin)
    key = 'Lane_Center'
    each_out = output_file_name_list[key]
    fileOpenMode = 'a'
    with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            lines = mgeo_planner_map_center.link_set.lines
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

    # UCDavis_Navigable_Boundaries
    mgeo_planner_map_navi= create_road_navigable(json_files['UCDavis_Navigable_Boundaries']['features'], origin)
    key = 'Lane_Navigable'
    each_out = output_file_name_list[key]
    fileOpenMode = 'a'
    with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            lines = mgeo_planner_map_navi.link_set.lines
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


# 위경도를 좌표로 바꿔서 저장을 해놓은 데이터(UCDavis_Outlines_geo)를 이용해서 차선 데이터
def create_lane(outlines, features, origin):
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
            leftLineColor = "white"

        if leftLineColor == "YELLOW":
            leftLineColor = "yellow"

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
        left_lane_marking.lane_shape = leftLineType
        left_lane_marking.lane_color = leftLineColor
        left_lane_marking.lane_width = 0.15
        left_lane_marking.dash_interval_L1 = 1
        left_lane_marking.dash_interval_L2 = 1

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
            rightLineType = [ "Solid Solid" ]

        right_start_node = Node('R{}S'.format(idx))
        right_start_node.point = rightLinePoints[0]
        node_set.nodes[right_start_node.idx] = right_start_node

        right_end_node = Node('R{}E'.format(idx))
        right_end_node.point = rightLinePoints[-1]
        node_set.nodes[right_end_node.idx] = right_end_node

        right_lane_marking = LaneBoundary(points=rightLinePoints, idx='R{}'.format(idx))
        right_lane_marking.set_from_node(right_start_node)
        right_lane_marking.set_to_node(right_end_node)
        right_lane_marking.lane_shape = leftLineType
        right_lane_marking.lane_color = leftLineColor
        right_lane_marking.lane_width = 0.15
        right_lane_marking.dash_interval_L1 = 1
        right_lane_marking.dash_interval_L2 = 1
        
        
        # right_lane_marking.fill_in_points_evenly_accor_to_leng(2)
        lane_set.lanes[right_lane_marking.idx] = right_lane_marking
    
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

                # lane_boundary.fill_in_points_evenly_accor_to_leng(2)
                lane_set.lanes[lane_boundary.idx] = lane_boundary

    mgeo_planner_map = MGeo(node_set=node_set, lane_boundary_set=lane_set)
    mgeo_planner_map.set_origin(origin)
    print('outline-lane')
    return mgeo_planner_map


if __name__ == "__main__":
    create_road_boundaries()
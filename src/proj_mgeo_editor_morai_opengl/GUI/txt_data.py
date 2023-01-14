
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # 프로젝트 Root 경로
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(current_path + '/../../lib/common') # 프로젝트 Root 경로

import numpy as np
import csv

from lib.mgeo.class_defs import *
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common
from lib.common.coord_trans_ll2utm import CoordTrans_LL2UTM
from pyproj import Proj, Transformer, CRS

import math
import re

def convert_points(points):
    obj = CoordTrans_LL2UTM(52)
    new_data_points = []
    for point in points:
        east, north = obj.ll2utm(point[1], point[0])
        new_data_point = [east, north, point[2]]
        new_data_points.append(new_data_point)
    return np.array(new_data_points)

def import_geojson_data(input_path):
    geojson_files, folder_info = geojson_common.read_geojson_files(input_path)
    
    node_set = NodeSet()
    link_set = LineSet()

    lines = geojson_files['ASM_Project_Test_Road_Exp_210209_PM0420']['features']
    # 322, 0, 165
    latlng = [129, 0, 0]
    origin = convert_points([latlng])[0]
    origin = np.array(origin)
    print('origin : ', origin)

    for line in lines:
        if line['properties']['Type'] == 'Lane':
            if line['properties']['LaneType'] == 'Driving':

                link_id = line['properties']['Id']
                points = np.array(line['geometry']['coordinates'])
                points = np.array(convert_points(points))
                # points -= origin

                start_node = Node(link_id+'S')
                start_node.point = points[0]
                node_set.nodes[start_node.idx] = start_node

                end_node = Node(link_id+'E')
                end_node.point = points[-1]
                node_set.nodes[end_node.idx] = end_node


                link = Link(points=points, 
                        idx=link_id, 
                        link_type=line['properties']['LaneType'], 
                        lazy_point_init=False)
                link.set_from_node(start_node)
                link.set_to_node(end_node)

                link_set.lines[link.idx] = link

    mgeo_planner_map = MGeo(node_set=node_set, link_set=link_set)
    mgeo_planner_map.set_origin(origin)
    return mgeo_planner_map


def import_txt_data(input_path):
    link_set = __create_link_set(input_path)
    node_set = __create_node_set(link_set)

    mgeo_planner_map = MGeo(node_set, link_set)
    return mgeo_planner_map

# 청주 계룡리슈빌 MGEO csv 일 때
# def __create_link_set(file_path):
#     file_list = os.listdir(file_path)
#     idx = 0
#     line_set = LineSet()
    
#     for file in file_list:
#         file_name = os.path.join(file_path, file)
#         with open(file_name, 'r') as link:
#             # Link 생성하기
#             data = csv.reader(link, delimiter='\n')
#             data_split = list(data)
#             print(len(data_split))
#             link_id = file.split('.')[0]
#             link_points = []
#             for point in data_split:
#                 point = eval(point[0])
#                 link_points.append([point[0], point[1], point[2]])
#             link_points = np.array(link_points, dtype = np.float32)
#             link = Link(points =link_points, idx=link_id, lazy_point_init=False)
#             line_set.lines[link.idx] = link
#             idx += 1
#     return line_set


# 충북대 같이 txt 파일 포맷일 때
def __create_link_set(file_path):
    file_list = os.listdir(file_path)
    idx = 0
    line_set = LineSet()

    for file in file_list:
        file_name = os.path.join(file_path, file)
        with open(file_name, 'r') as link:
            # Link 생성하기
            data = link.read()
            data_split = data.splitlines()
            link_id = 'LINK{}'.format(idx)
            link_points = []
            for point in data_split:
                link_points.append(point.split('\t'))
            link_points = np.array(link_points, dtype = np.float32)
            link = Link(points =link_points, idx=link_id, lazy_point_init=False)
            line_set.lines[link.idx] = link
            idx += 1
    return line_set

def __create_node_set(line_set):
    idx = 0
    node_set = NodeSet()
    lines = line_set.lines
    for line in lines:
        # Node 생성하기
        create_node_point = [lines[line].points[0], lines[line].points[-1]]
        for i, point in enumerate(create_node_point):
            idx += 1
            node_id = 'NODE{}'.format(idx)
            node = Node(node_id)
            node.point = point
            if i == 0:
                node.add_to_links(lines[line])
            elif i == 1:
                node.add_from_links(lines[line])
            node_set.nodes[node.idx] = node

    return node_set


def import_saudi_shp(input_path):
    map_info = shp_common.read_shp_files(input_path, encoding_ansi=True)[0]

    node_set = NodeSet()
    link_set = LineSet()

    first_file = list(map_info.keys())[0]
    sf = map_info[first_file]

    shapes = sf.shapes()
    origin_e = shapes[0].points[0][0]
    origin_n = shapes[0].points[0][1]
    origin = [origin_e, origin_n, 0]
    # origin = convert_points_For_saudi([origin])[0]
    

    for map_i in map_info:
        sf = map_info[map_i]

        shapes = sf.shapes()
        records  = sf.records()
        fields = sf.fields

        if len(shapes) != len(records):
            raise BaseException('[ERROR] len(shapes) != len(records)')

        for i in range(len(shapes)):
            shp_rec = shapes[i]
            dbf_rec = records[i]
            
            # Convert to numpy array
            shp_rec.points = np.array(shp_rec.points)
            # shp_rec.z = np.array(shp_rec.z)
            point_z = np.array([0]*len(shp_rec.points))
            line_points = np.c_[shp_rec.points, point_z]
            line_points = np.array(line_points)
            # line_points = convert_points_For_saudi(line_points)
            # line_points -= origin

            from_node = Node()
            from_node.point = line_points[0] 
            node_set.append_node(from_node, create_new_key=True)

            to_node = Node()
            to_node.point = line_points[-1] 
            node_set.append_node(to_node, create_new_key=True)

            link = Link(points=line_points, lazy_point_init=False)
            link.set_from_node(from_node)
            link.set_to_node(to_node)
            link_set.append_line(link, create_new_key=True)

    mgeo_planner_map = MGeo(node_set = node_set, link_set = link_set)
    mgeo_planner_map.set_origin(origin)
    prj_file = os.path.normpath(os.path.join(input_path, '{}.prj'.format(first_file)))
    mgeo_planner_map.set_coordinate_system_from_prj_file(prj_file)
    
    return mgeo_planner_map


def utm_zone(point):
    # LatLng > utm_zone
    lnt = point[0]
    lat = point[1]
    num = 180 + lnt
    zone_con = int(num//6)
    return zone_con+1

def convert_points_For_saudi(points):
    new_data_points = []
    for point in points:
        utm_num = utm_zone(point)
        east, north = CoordTrans_LL2UTM(utm_num).ll2utm(point[1], point[0])
        new_data_point = [east, north, point[2]]
        new_data_points.append(new_data_point)
    return np.array(new_data_points)



def import_modelling_line_shp_file(input_path):
    map_info = shp_common.read_shp_files(input_path, encoding_ansi=True)[0]

    node_set = NodeSet()
    link_set = LineSet()

    first_file = list(map_info.keys())[0]
    sf = map_info[first_file]

    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    # origin_e = shapes[0].points[0][0]
    # origin_n = shapes[0].points[0][1]
    # origin_z = shapes[0].z[0]
    # origin = [origin_e, origin_n, origin_z]
    origin = [0, 0, 0]

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        link_id = str(dbf_rec.local_idx)
            
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)
        line_points = np.c_[shp_rec.points, shp_rec.z]
        line_points = np.array(line_points)
        line_points -= origin

        from_node = Node(link_id+'S')
        from_node.point = line_points[0] 
        node_set.append_node(from_node)

        to_node = Node(link_id+'E')
        to_node.point = line_points[-1] 
        node_set.append_node(to_node)

        link = Link(idx=link_id, points=line_points, lazy_point_init=False)
        link.set_from_node(from_node)
        link.set_to_node(to_node)
        link_set.append_line(link)

    mgeo = MGeo(node_set = node_set, link_set = link_set)
    mgeo.set_origin(origin)
    # mgeo.global_coordinate_system = Proj('+proj=utm +zone={} +datum=WGS84 +units=m +no_defs'.format(52)).srs
    
    return mgeo



if __name__ == "__main__":
    
    # import_saudi_shp('D:\\지도\\두바이\\merged_las_rgb_v2_trajectory')
    import_modelling_line_shp_file('D:\\01.지도\\210817_aict_slope\\Aict_Slope_track_Mgeo_Line')
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
import shutil

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.class_defs import *
from lib.common.coord_trans_ll2utm import CoordTrans_LL2UTM

from pyproj import Proj, Transformer, CRS

# geojson 파일 읽기
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


def convert_points(points):
    obj = CoordTrans_LL2UTM(10)
    new_data_points = []
    for point in points:
        east, north = obj.ll2utm(point['lat'], point['lng'])
        new_data_point = [east, north, point['alt']]
        new_data_points.append(new_data_point)
    return np.array(new_data_points)


def convert_point(point):
    transformer = Transformer.from_crs("epsg:4326", "epsg:26910")
    new_x, new_y = transformer.transform(point['lat'], point['lng'])
    new_point = [new_x, new_y, point['alt']]
    return new_point


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
        for line in centerLine:
            line['leftProjection'] = convert_point(line['leftProjection'])
            line['rightProjection'] = convert_point(line['rightProjection'])
            
        item['properties']['centerLine']['geometry'] = Points

    with open(new_file, 'w') as f:
        json.dump(json_files['UCDavis_Outlines']['features'], f, indent=4)
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
from lib.common.coord_trans_ll2utm import CoordTrans_LL2UTM

"""
civilmaps에 있는 데이터 type 변경을 위한 함수
1. convert_line_name
    name 값 이용해서 lane_boundary code/color/width/shape 입력
    sample 데이터
    - Road Edge
    - White Single Broken Line
    - Yellow Single Solid Line
    - White Single Solid Line
    - Bike Lane Solid Line
    - Bike Lane Broken Line
    - Stop Line
    + 횡단보도 데이터 편집(선 > 다각형)을 위해 code 999로 추가

2. convert_points
    Lat/Lng to UTM

3. read_json_files
    civilmaps 파일 타입 json

4. local_utm_to_sim_coord

5. points_to_point [임시]
    civilmaps 신호등/표지판 등 정보 선이어서 점정보로 변경하는 코드
    > 2021.02.22 모든 점의 평균값이용
"""

def get_origin(data):
    points = data['geometry']['coordinates']
    new_points = convert_points(points)
    return new_points[0]

def convert_line_name(name, lane_boundary):

    lane_type = 599
    lane_color = 'white'
    lane_width = 0.15
    dash_interval_L1 = 3
    dash_interval_L2 = 3
    lane_shape = ["Solid"]
    
    if name == 'White Single Broken Line':
        lane_type = 503
        lane_color = 'white'
        lane_width = 0.15
        dash_interval_L1 = 5
        dash_interval_L2 = 2
        lane_shape = ["Broken"]
    
    elif name == 'Yellow Single Solid Line':
        lane_type = 503
        lane_color = 'yellow'
        lane_width = 0.15
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]
    
    elif name == 'White Single Solid Line':
        lane_type = 503
        lane_color = 'white'
        lane_width = 0.15
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]
    
    elif name == 'Bike Lane Solid Line':
        lane_type = 535
        lane_color = 'white'
        lane_width = 0.15
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]
    
    elif name == 'Bike Lane Broken Line':
        lane_type = 535
        lane_color = 'white'
        lane_width = 0.15
        dash_interval_L1 = 5
        dash_interval_L2 = 2
        lane_shape = ["Broken"]
    
    elif name == 'Stop Line':
        lane_type = 530
        lane_color = 'white'
        lane_width = 0.15
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]
    
    elif name == 'Road Edge':
        lane_type = 505
        lane_color = 'undefined'
        lane_width = 0.15
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]

    # 횡단보도 데이터 편집/csv로 생성하기 위해서 code=999로 설정  
    elif name == 'Crosswalk':
        lane_type = 999
        lane_color = 'undefined'
        lane_width = 0.1
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]

    else:
        return None
        
    lane_boundary.lane_type_def = 'civilmaps'
    lane_boundary.lane_type = lane_type
    lane_boundary.lane_color = lane_color
    lane_boundary.lane_width = lane_width
    lane_boundary.dash_interval_L1 = dash_interval_L1
    lane_boundary.dash_interval_L2 = dash_interval_L2
    lane_boundary.lane_shape = lane_shape

    return lane_boundary


def convert_points(points):
    obj = CoordTrans_LL2UTM(10)
    new_data_points = []
    for point in points:
        east, north = obj.ll2utm(point[1], point[0])
        new_data_point = [east, north, point[2]]
        new_data_points.append(new_data_point)
    return np.array(new_data_points)



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


def local_utm_to_sim_coord(local_utm):
    # Local UTM  X, Y, Z = East, North, Up
    # Simulation X, Y, Z = West, Up, South
    
    sim_x = -1 * local_utm[0]
    sim_y = local_utm[2]
    sim_z = -1 * local_utm[1]

    return np.array([sim_x, sim_y, sim_z])


def points_to_point(points):

    x = points[:,0]
    y = points[:,1]
    z = points[:,2]

    return np.array([np.mean(x), np.mean(y), np.mean(z)])


def get_traffic_sign(name):
    if name == 'Low Clearance':
        return_type = name
    elif name == 'Keep-clear region':
        return_type = name
    elif name == 'Road Sign Outline - Do Not Enter':
        return_type = 'Do Not Enter'
    elif name == 'Road Sign Outline - One Way':
        return_type = 'One Way'
    elif name == 'Road Sign Outline - Parking':
        return_type = 'Parking'
    elif name == 'Road Sign Outline - Regulatory':
        return_type = 'Regulatory'
    elif name == 'Road Sign Outline - Lane Regulation':
        return_type = 'Lane Regulation'
    elif name == 'Road Sign Outline - Speed':
        return_type = 'Speed'
    elif name == 'Road Sign Outline - Warning/Advisory':
        return_type = 'Warning/Advisory'
    elif name == 'Road Sign Outline - Pedestrian':
        return_type = 'Pedestrian'
    elif name == 'Road Sign Outline - Stop Sign':
        return_type = 'Stop Sign'
    elif name == 'Road Sign Outline - Street Name':
        return_type = 'Street Name'
    elif name == 'Road Sign Outline - No Right Turn':
        return_type = 'No Right Turn'
    elif name == 'Road Sign Outline - No U Turn':
        return_type = 'No U Turn'
    elif name == 'Road Sign Outline - No Left Turn':
        return_type = 'No Left Turn'
    elif name == 'Road Sign Outline - Yield':
        return_type = 'Yield'
    else:
        return_type =  None

    return return_type


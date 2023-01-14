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

from lib.civilmaps.civilmaps_converter import *

"""
Editor 없이 출력하는 정보(표지판, 신호등)
civilmaps에 횡단보도는 편집(line -> polygon)이 필요해서 Editor에서 출력
"""

# 표지판
def export_taffic_sign(input_path):

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

    map_info, filename_map = read_json_files(input_path)

    items = map_info['WGS_geofeatures_raw_feature_collection']['features']
    origin = np.array(get_origin(items[0]))
    to_csv_list = []
    asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Prefabs/Traffic_Sign/'
    # 아직 미국쪽 데이터 만든게 딥맵 꺼 밖에 없어서 위경도 좌표만 바꾼것
    for item in items:
        id = item['id']
        name = item['properties']['asset']['name']
        points = item['geometry']['coordinates']
        points = convert_points(points)
        points -= origin
        point = points_to_point(points)
        

        file_name = get_traffic_sign(name)
        if not file_name:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue

        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root # + file_name
        # INFO #2
        pos = point
        pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
        position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

        # INFO #3
        orientation_string = '0.0/0.0/0.0'

        # csv 파일 출력을 위한 리스트로 추가
        to_csv_list.append([file_path, file_name, position_string, orientation_string, id])

    # 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'sim_build_data_traffic_sign.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)

    print('------------------ taffic_sign END')



# 신호등
def export_taffic_light(input_path):

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

    map_info, filename_map = read_json_files(input_path)

    items = map_info['WGS_geofeatures_raw_feature_collection']['features']
    origin = np.array(get_origin(items[0]))
    to_csv_list = []
    asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Models/Traffic_Light/'
    # 아직 미국쪽 데이터 만든게 딥맵꺼 밖에 없어서 위경도 좌표만 바꾼것
    for item in items:
        id = item['id']
        name = item['properties']['asset']['name']
        points = item['geometry']['coordinates']
        points = convert_points(points)
        points -= origin
        point = points_to_point(points)
        

        file_name = get_traffic_light(name)
        if not file_name:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue

        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root # + file_name
        # INFO #2
        pos = point
        pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
        position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

        # INFO #3
        orientation_string = '0.0/0.0/0.0'

        # csv 파일 출력을 위한 리스트로 추가
        to_csv_list.append([file_path, file_name, position_string, orientation_string, id])

    # 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'sim_build_data_traffic_light.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)

    print('------------------ taffic_light END')


def get_traffic_light(name):

    # Traffic Signal Outline - Automobile
    # Traffic Signal Outline - Guarded Left Turn
    # Road Sign Outline - Pedestrian Crossing Signal
    if name == 'Traffic Signal Outline - Automobile':
        return_type = 'V:RYG:OOO'
    elif name == 'Traffic Signal Outline - Guarded Left Turn':
        return_type = 'V:RYG:<<<'
    elif name == 'Road Sign Outline - Pedestrian Crossing Signal':
        return_type = 'PS'
    else:
        return_type =  None

    return return_type


if __name__ == "__main__":
    iuput_folder_path = 'D:/road_model_maker/rsc/map_data/civilmaps_geojson_sample'
    export_taffic_sign(iuput_folder_path)
    export_taffic_light(iuput_folder_path)
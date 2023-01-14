import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')

import json
import csv
import numpy as np

import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

from lib.stryx.stryx_load_geojson_lane import *
from lib.stryx.stryx_geojson import *

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

    map_info, filename_map = geojson_common.read_geojson_files(input_path)
    
    origin = map_info['A1_NODE']['features'][0]['geometry']['coordinates']
    ts_data = map_info['B1_SAFETYSIGN']['features']
    to_csv_list = []
    asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Prefabs/'

    for ts in ts_data:
        idx = ts['properties']['id']
        point = np.array(ts['geometry']['coordinates'])
        point -= origin

        result, file_path, file_name = get_traffic_sign_asset_path_and_name(ts)
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue

        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path


        # INFO #2
        pos = point
        pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
        position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

        # INFO #3
        orientation_string = '0.0/0.0/0.0'

        # csv 파일 출력을 위한 리스트로 추가
        to_csv_list.append([file_path, file_name, position_string, orientation_string, idx])

    # 신호등 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'sim_build_data_traffic_sign.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)

        signal_link_id = ts['properties']['LinkID']
    
def get_traffic_sign_asset_path_and_name(ts):
    # 주의표지	1
    # 규제표지	2
    # 지시표지	3
    # 보조표지	4
    idx = ts['properties']['id']
    prop_type = ts['properties']['Type']
    prop_sub_type = ts['properties']['SubType']
    prop_value = ts['properties']['Value']
    prop_unit = ts['properties']['Unit']

    if prop_type == '9' or prop_sub_type is None:
        print('[WARNING] @ __get_traffic_sign_asset_path_and_name: value is not set for traffic sign object with Type = {} (ts id = {})'.format(prop_type, idx))
        # print("{} Type = none or 9".format(idx))
        return False, '', ''
    

    # UPDATE(sglee): 지원 안 되는 prop_sub_type 지속적으로 업데이트
    if prop_sub_type in ['199', '299', '399', '499', '225']:
        # 225: 최저 속도 제한 >> 최저 속도 값을 link에서 받아와야 모델을 특정할 수 있는데, link에 최저 속도 값이 없음 

        print('[WARNING] @ __get_traffic_sign_asset_path_and_name: no supported model for this prop_sub_type = {} (ts id = {})'.format(prop_sub_type, idx))
        return False, '', ''

    if prop_type == '1':
        file_path = '01_MapCommon_Signs/01_Caution_Beam'
        file_name = '01_Caution_{}_Beam.prefab'.format(prop_sub_type)

    elif prop_type == '2':
        file_path = '01_MapCommon_Signs/02_Restriction_Beam'
        
        if prop_sub_type == '224':
            if (prop_value is None) or (prop_value is '') or (prop_value is 0):
                raise BaseException('[WARNING] @ __get_traffic_sign_asset_path_and_name: value is not set for traffic sign object with sub_type = {} (ts id = {})'.format(prop_sub_type, idx))
            # prop_subtype을 변경해준다
            prop_sub_type = '{}_{}kph'.format(prop_sub_type, prop_value)

        if prop_sub_type == '220':
            if (prop_value is None) or (prop_value is '') or (prop_value is 0):
                raise BaseException('[WARNING] @ __get_traffic_sign_asset_path_and_name: value is not set for traffic sign object with sub_type = {} (ts id = {})'.format(prop_sub_type, idx))
            # prop_subtype을 변경해준다
            prop_sub_type = '{}_{}t'.format(prop_sub_type, prop_value)
        file_name = '02_Restriction_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '3':
        file_path = '01_MapCommon_Signs/03_Indication_Beam'
        file_name = '03_Indication_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '4':
        file_path = '01_MapCommon_Signs/04_Aux_Beam'
        file_name = '04_Aux_{}_Beam.prefab'.format(prop_sub_type)

    else:
        raise BaseException('[ERROR] @ get_traffic_sign_asset_path_and_name: unexpected prop_type! (ts id = {})'.format(idx))

    return True, file_path, file_name

if __name__ == u'__main__': 
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\stryx_mdl201203_KAIST_3rd'
    export_taffic_sign(input_path)
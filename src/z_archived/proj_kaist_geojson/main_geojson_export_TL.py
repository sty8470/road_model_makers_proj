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

def export_taffic_light(input_path):
    

    # 차량횡형-삼색등	1
    # 차량횡형-사색등A	2 
    # 차량횡형-사색등B	3 
    # 차량횡형-화살표삼색등	4
    # 차량종형-삼색등	5
    # 차량종형-화살표삼색등	6
    # 차량종형-사색등	7
    # 버스삼색등	8 
    # 가변형 가변등	9
    # 경보형 가변등	10
    # 보행등	11 
    # 자전거종형-삼색등	12 
    # 자전거종형-이색등	13 
    # 차량보조등-종형삼색등	14
    # 차량보조등-종형사색등	15
    # 기타 신호등 유형	99 

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
    tl_data = map_info['C1_TRAFFICLIGHT']['features']
    to_csv_list = []
    asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Prefabs/'

    for tl in tl_data:
        idx = tl['properties']['fid']
        idx2 = tl['properties']['id']
        point = np.array(tl['geometry']['coordinates'])
        point -= origin
        signal_type = tl['properties']['Type']

        result, file_path, file_name =\
            get_traffic_light_asset_path_and_name(signal_type, idx)
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue

        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path


        # INFO #2
        pos = point
        # pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
        position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

        # INFO #3
        orientation_string = '0.0/0.0/0.0'

        # csv 파일 출력을 위한 리스트로 추가
        to_csv_list.append([file_path, file_name, position_string, orientation_string, idx])

    # 신호등 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'sim_build_data_traffic_light.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)
        signal_link_id = tl['properties']['LinkID']
    
def get_traffic_light_asset_path_and_name(prop_type, idx):

    if prop_type == '1': # 삼색등
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Hor_R_Y_SG.prefab'

    elif prop_type == '2': # 사색등A	2
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Hor_R_Y_LG_SG.prefab'

    elif prop_type == '11':
        # 보행자 신호등 (NGII)
        file_path = '01_MapCommon_PS'
        file_name = 'PS_RG.prefab'
        
    else:
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Misc_NGII_Shp2_{}.prefab'.format(prop_type)
        print('[ERROR] @ __get_traffic_light_asset_path_and_name: unexpected prop_type! (you passed = {} (tl id = {}))'.format(prop_type, idx))

    return True, file_path, file_name

if __name__ == u'__main__': 
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\stryx_mdl201203_KAIST_3rd'
    export_taffic_light(input_path)
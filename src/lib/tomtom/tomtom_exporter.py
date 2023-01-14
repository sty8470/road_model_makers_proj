import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import json
import csv
import numpy as np

import struct
import uuid
import base64
import re

import avro.schema
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.class_defs import *
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common
import lib.common.centroid as cent

from lib.tomtom.tomtom_converter import *


"""
Editor 없이 출력하는 정보(표지판)
tomtom은 신호등이 없음
"""

# 표지판 만들기
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

    map_info = read_geojson_files(input_path)

    origin = map_info['laneCenterline']['features'][0]['geometry']['coordinates']
    origin = transformer_point(origin[0])

    ts_data = map_info['trafficSigns']['features']

    to_csv_list_asset = []
    to_csv_list_other = []
    to_csv_list = []
    to_csv_list_asset.append(['FolderPath', 'PrefabName', 'InitPos', 'InitRot', 'GameObjectName'])
    asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Models/US_TrafficSign'


    to_csv_list_other.append(['Type', 'SubType', 'position_string', 'orientation_string', 'sign_id', 'shape', 'color', 're_width', 're_height', 'width', 'height'])

    # 프리팹 만들어진거랑 프리팹 만들어지지 않은 것 CSV 따로 만들어서 보내기
    
    for ts in ts_data:
        # msb = ts['entity']['UUID']['mostSigBits']
        # lsb = ts['entity']['UUID']['leastSigBits']
        # idx = uuid.UUID(bytes=struct.pack('>qq', msb, lsb))
        # attri = ts['attributes']
        # subcategory = attri[0]['value']
        # additionalInfo = attri[1]['value']
        # verificationDate = attri[2]['value']
        # shape = attri[3]['value']
        # faceSizeheight, faceSizewidth = attri[4]['nsoAttributes'][0]['value'], attri[4]['nsoAttributes'][1]['value']
        # heading = attri[5]['value']
        # color1 = attri[6]['value']
        # color2 = attri[7]['value']
        # color = '{};{}'.format(color1, color2)
        # geotype, geometries = convert_string_to_points(attri[8]['nsoAttributes'][1]['value'])

        sign_id = ts['properties']['id']
        point = ts['geometry']['coordinates']
        width = ts['properties']['faceWidth']
        height = ts['properties']['faceHeight']
        heading = ts['properties']['heading']
        color = ts['properties']['colors']
        shape = ts['properties']['shape']
        sign_type = ts['properties']['type']
        sign_subtype = ts['properties']['subtype']


        re_width, re_height = get_recommended_size(sign_subtype)

        add_info = ts['properties']['add_info']
        if len(add_info) > 0:
            value = int(float(add_info['value']))
            sign_subtype = '{}/{}'.format(sign_subtype, value)
        point = transformer_point(point)
        point = np.array(point)
        point -= origin

        
        
        # INFO #2
        pos = point
        pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
        position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

    
        # simulatorHeadingValue = signal_heading_deg + 180
        simulatorHeadingValue = -1 * heading + 90
        if simulatorHeadingValue > 360 :
            simulatorHeadingValue = simulatorHeadingValue - 360
        else:
            simulatorHeadingValue = simulatorHeadingValue
        # INFO #3
        orientation_string = '0.0/{:.6f}/0.0'.format(simulatorHeadingValue)

        to_csv_list.append(['{}_{}'.format(sign_type, sign_subtype), color, shape])

        result, file_path, file_name = __get_traffic_sign_asset_path_and_name(sign_type, sign_subtype, shape)


        if result:
            file_path = os.path.join(asset_path_root, file_path)
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
            # file_path = os.path.join(asset_path_root, sign_type)
            # to_csv_list_asset.append(['FolderPath', 'PrefabName', 'InitPos', 'InitRot', 'GameObjectName'])
            to_csv_list_asset.append([file_path, file_name, position_string, orientation_string, sign_id])
        else:
            # to_csv_list_other.append(['Type', 'SubType', 'position_string', 'orientation_string', 'sign_id', 'shape', 'color', 're_width', 're_height', 'width', 'height'])
            # csv 파일 출력을 위한 리스트로 추가
            to_csv_list_other.append([sign_type, sign_subtype, position_string, orientation_string, sign_id, shape, color, re_width, re_height, width, height])

    # 신호등 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'original_data2.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)

    output_file_name = os.path.join(output_path, 'sim_build_data_traffic_sign2.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list_asset)
        
    output_file_name = os.path.join(output_path, 'sim_build_data_traffic_sign_other2.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list_other)
    print('------------------ taffic_sign END')



def __get_traffic_sign_asset_path_and_name(sign_type, sub_type, shape):

    result, file_path, file_name = False, '', ''

    if sign_type == 'InformationSign':
        if 'Other' in sub_type:
            return False, '', ''
            
        elif sub_type == 'One Way':
            file_path = '0_Model'
            file_name = 'OneWay.fbx'
        else:
            return False, '', ''
            
    elif sign_type == 'LaneInformation':
        if sub_type == 'LaneInformation':
            return False, '', ''

        elif sub_type == 'Lane added left':
            file_path = '0_Model'
            file_name = 'Addedlane.fbx'

        elif sub_type == 'Lane ends left':
            file_path = '0_Model'
            file_name = 'Laneends.fbx'

        elif sub_type == 'Lane added right':
            file_path = '0_Model'
            file_name = 'Addedlane.fbx'
            
        elif sub_type == 'Lane ends right':
            file_path = '0_Model'
            file_name = 'Laneends.fbx'
        else:
            return False, '', ''

    elif sign_type == 'Mandatory':
        if sub_type == 'Other':
            return False, '', ''

    elif sign_type == 'OvertakingLane':
        if sub_type == 'Overtaking lane':
            return False, '', ''

    elif sign_type == 'POI':
        if sub_type == 'POI':
            return False, '', ''

    elif sign_type == 'Prohibition':
        if sub_type == 'Other':
            return False, '', ''

        elif sub_type == 'No parking':
            return False, '', ''

        elif sub_type == 'No pedestrians':
            return False, '', ''

        elif sub_type == 'No Entry':
            file_path = '0_Model'
            file_name = 'DoNotEnter.fbx'

        elif sub_type == 'No Turn Right':
            file_path = '0_Model'
            file_name = 'NoRightTurn.fbx'

        elif sub_type == 'No Turn Left':
            file_path = '0_Model'
            file_name = 'NoLeftTurn.fbx'
        else:
            return False, '', ''

    elif sign_type == 'RNR':
        if sub_type == 'RNR':
            # 모양에 따라서 나눠야 하나(?)
            file_path = '3_other_Model'
            file_name = 'US101.fbx'

    elif sign_type == 'SignPost':
        if sub_type == 'Sign Post':
            return False, '', ''

    elif sign_type == 'SpeedRestriction':
        sub_type, speed_value = sub_type.split('/')
        if sub_type == 'Speed': # Speed_50
            file_path = '0_Model'
            file_name = 'SpeedLimit_50.fbx'

        elif sub_type == 'Recommended Speed': # Recommended Speed_15
            return False, '', ''

        else:
            return False, '', ''

    elif sign_type == 'Warning':
        if sub_type == 'Other':
            return False, '', ''

        elif sub_type == 'Sharp curve left':
            file_path = '0_Model'
            file_name = 'SharpCurveAhead.fbx'
        elif sub_type == 'Sharp curve right':
            file_path = '0_Model'
            file_name = 'SharpCurveAhead.fbx'

        elif sub_type == 'Maximum Dimension':
            return False, '', ''

        elif sub_type == 'Traffic Lights':
            file_path = '0_Model'
            file_name = 'Signalahead.fbx'

        elif sub_type == 'Pedestrians':
            return False, '', ''

        elif sub_type == 'Yield':
            return False, '', ''

        elif sub_type == 'Children':
            return False, '', ''

        else:
            return False, '', ''

    else:
        raise BaseException('[ERROR] @ get_traffic_sign_asset_path_and_name: unexpected prop_type! (type = {})'.format(sign_type))
     
    return True, file_path, file_name  



def get_recommended_size(sub_type):

    re_width, re_height = 0, 0

    if sub_type in ['Children', 'No Turn Left', 'No Turn Right']:
        re_width, re_height = 36, 36
        
    elif sub_type in ['Lane added left', 'Lane added right', 'Lane ends left', 'Lane ends right', 
                    'No Entry', 'No parking', 'Sharp curve left', 'Sharp curve right']:
        re_width, re_height = 48, 48
    
    elif sub_type == 'Maximum Dimension':
        re_width, re_height = 30, 30

    elif sub_type == 'LaneInformation':
        re_width, re_height = 60, 30
    
    elif sub_type == 'No pedestrians':
        re_width, re_height = 30, 30

    elif sub_type == 'One Way':
        re_width, re_height = 54, 18

    elif sub_type == 'RNR':
        re_width, re_height = 30, 24

    elif sub_type in ['Speed', 'Recommended Speed']:
        re_width, re_height = 36, 48

    elif sub_type == 'Yield':
        re_width, re_height = 48, 48
        
    elif sub_type == 'Traffic Lights':
        re_width, re_height = 60, 60
        
    return int(re_width*2.54), int(re_height*2.54)




def get_traffic_sign_asset_path_and_name(ts):

    # 주의표지	1 Warning
    # 규제표지	2 Prohibition,
    # 지시표지	3 Mandatory, Stop
    # 보조표지	4 Name, InformationSign, SignPost
    # RailwayCrossing, SpeedRestriction
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


def local_utm_to_sim_coord(local_utm):
    # Local UTM  X, Y, Z = East, North, Up
    # Simulation X, Y, Z = West, Up, South
    
    sim_x = -1 * local_utm[0]
    sim_y = local_utm[2]
    sim_z = -1 * local_utm[1]

    return np.array([sim_x, sim_y, sim_z])

if __name__ == u'__main__':
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\tomtom_geojson_US Interstate 101'
    export_taffic_sign(input_path)
    

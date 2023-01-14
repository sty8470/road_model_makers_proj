"""
국토지리정보원의 데이터를 읽고 신호등 정보를 csv로 출력한다
"""
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')
sys.path.append(current_path + '/../lib_ngii_shp_ver2/')

from shp_common import *
import shapefile
import csv

import numpy as np
import matplotlib.pyplot as plt


def main_shp_ver1():
    '''
    국토지리정보원 ver1 포맷 데이터 일부를 csv로 출력한다
    '''
    input_path = '../../rsc/map_data/shp_01_Seoul_AutonomousDrivingTestbed/HDMap_UTM52N/'
    output_path = '../../output/ngii_shp_ver2_191226_모라이_제공자료/서울_자율주행테스트베드_신호등_200427_AM1051/'

    # 절대 경로로 변경
    # input_path = os.path.normcase(input_path)
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)   

    # 절대 경로로 변경
    # output_path = os.path.normcase(output_path)
    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    # Get Map Information
    map_info = read_shp_files(input_path)

    sf = map_info['B1_SIGNAL_POINT']
    
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    all_data_to_export = list()

    # 출력 필요한 형태
    # X, Y, Z, ID, AdminCode, Type, LinkID, Ref_Lane, PostID

    header = ['UTM52N East(m)', 'UTM52N North(m)', 'Ellipsoid Height(m)', 'HDUFID', 'LINKID', 'SIGNTYPE']
    all_data_to_export.append(header)

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]
        
        one_row = [shp_rec.points[0][0], shp_rec.points[0][1], shp_rec.z[0],
            dbf_rec['HDUFID'], dbf_rec['LINKID'],  dbf_rec['SIGNTYPE']]
         
        all_data_to_export.append(one_row)

    output_file = os.path.join(output_path, 'traffic_light_info_request.csv')
    fileOpenMode = 'w'
    with open(output_file, fileOpenMode, newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter = ',')
        writer.writerows(all_data_to_export)

    print('[INFO] ended')


def main_shp_ver2():
    '''
    국토지리정보원 ver2 포맷 데이터 일부를 csv로 출력한다
    '''

    # D:\road_model_maker\rsc\map_data\ngii_shp_ver2_Seoul_Sangam\SEC01_UTM52N_ElipsoidHeight
    input_path = '../../rsc/map_data/ngii_shp_ver2_Seoul_Sangam/SEC01_UTM52N_ElipsoidHeight'
    output_path = '../../rsc/map_data/ngii_shp_ver2_Seoul_Sangam/output'
    relative_loc = True

    # asset_path_root = D:\MoraiOneBuild\Assets\1_Module\Map\MapManagerModule\RoadObject\Prefabs
    asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Prefabs/'
    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))   
    to_csv_list = []
    # inputPath = os.path.normcase(inputPath)
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)  

    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)   

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    # Get Map Information
    map_info = read_shp_files(input_path)[0]

    origin = [ 313008.55819800857, 4161698.628368007, 35.66435583359189 ]
    print('[INFO] Origin Set as: ', origin)

    sf = map_info['C1_TRAFFICLIGHT']
    
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    # all_data_to_export = list()

    # # 출력 필요한 형태
    # # X, Y, Z, ID, AdminCode, Type, LinkID, Ref_Lane, PostID

    # header = ['UTM52N East(m)', 'UTM52N North(m)', 'Ellipsoid Height(m)', 'ID', 'AdminCode', 'Type', 'LinkID', 'Ref_Lane', 'PostID']
    # all_data_to_export.append(header)

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        idx = dbf_rec['ID']
        point = [shp_rec.points[0][0], shp_rec.points[0][1], shp_rec.z[0]]
        point = np.array(point)
        point -= origin
        # if is_out_of_xy_range(point, [-90, 735], [-445, 240]) == False:

        signal_type = dbf_rec['Type']

        result, file_path, file_name =\
            get_traffic_light_asset_path_and_name(signal_type, idx)

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
    output_file_name = os.path.join(output_path, 'traffic_light_ALL.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)


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

def local_utm_to_sim_coord(local_utm):
    # Local UTM  X, Y, Z = East, North, Up
    # Simulation X, Y, Z = West, Up, South
    
    sim_x = -1 * local_utm[0]
    sim_y = local_utm[2]
    sim_z = -1 * local_utm[1]

    return np.array([sim_x, sim_y, sim_z])


def is_out_of_xy_range(point, xlim, ylim):
    x_pos = point[0]
    y_pos = point[1]

    if x_pos < xlim[0] or xlim[1] < x_pos:
        return True

    if y_pos < ylim[0] or y_pos > ylim[1]:
        return True
        
    return False


if __name__ == u'__main__':
    main_shp_ver2()
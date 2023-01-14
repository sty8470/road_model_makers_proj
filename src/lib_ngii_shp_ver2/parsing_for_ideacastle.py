"""
상암지역에 대한 csv 파일을 아이디어캐슬에 제공하기 위한 파싱
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')

from shp_common import *
import shapefile
import csv
import ngii_shp_ver2_utils as ngii_utils

import numpy as np
import matplotlib.pyplot as plt
import load_csv


def _append_list_of_points(list_to_append, shp_rec, relative_loc, origin=None):
    for i in range(len(shp_rec.points)):
        e = shp_rec.points[i][0]
        n = shp_rec.points[i][1]
        z = shp_rec.z[i]

        if relative_loc:
            e = e - origin[0]
            n = n - origin[1]
            z = z - origin[2]
        
        list_to_append.append([e,n,z])


def _plot_all(input_path, style=None):
    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))   

    # inputPath = os.path.normcase(inputPath)
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)  

    # read csv
    data = load_csv.read_csv_file(input_path, delimiter=',', names=False)
    print(data.shape)

    x = data[:, 0]
    y = data[:, 1]
    z = data[:, 2]

    if style == None:
        plt.plot(x, y)
    else:
        plt.plot(x, y, style)

    plt.grid(True)


def export_to_csv():
    input_path = '../../rsc/map_data/ngii_shp_ver2_191226_모라이_제공자료/서울_자율주행테스트베드/SEC01_서울자율주행테스트베드'
    output_path = '../../output/ngii_shp_ver2_191226_모라이_제공자료/서울_자율주행테스트베드/SEC01_서울자율주행테스트베드/'
    relative_loc = True

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

    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 A1_NODE에서 검색되는 첫번째 포인트로한다
    """
    origin = get_first_shp_point(map_info['A1_NODE'])
    print('[INFO] Origin =', origin)

    
    lane = map_info['B2_SURFACELINEMARK']

    """
    출력 파일 Dict 만들기
    """
    output_file_name_list = dict()
    output_file_name_list['Lane_NoParking'] = 'RoadEdge_NoParkingLane.csv'
    output_file_name_list['Lane_Center'] = 'CenterLine.csv'
    output_file_name_list['Lane_Normal'] = 'NormalLane.csv'
    output_file_name_list['Lane_Misc'] = 'MiscLane.csv'

    """
    이 output_file_name_list를 전부 절대 경로로 변경한다
    """
    for key in output_file_name_list.keys():
        output_file_name_list[key] = os.path.join(
            output_path, output_file_name_list[key])


    """
    이 output_file_name_list에 해당하는 빈 파일을 전부 생성한다
    """
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

    
    sf = lane
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    output_data = dict()
    output_data['Lane_NoParking'] = list()
    output_data['Lane_Center'] = list()
    output_data['Lane_Normal'] = list()
    output_data['Lane_Misc'] = list()   

    for i in range(len(shapes)):
        print('Exporting B2_SURFACELINEMARK : {} / {}'.format(i+1, len(shapes)), end='\r')
        
        # DBF 정보를 보고 어느쪽으로 추가할지 결정한다
        dbf_rec = records[i]
        shp_rec = shapes[i]

        # 'Kind' 값은 규제 유형을 정의 
        kind_str = ngii_utils.surfline_kind_code_to_str(dbf_rec['Kind'], lane_prefix=False)

        # 'Type' 값은 형태 유형을 정의   
        type_str = ngii_utils.surfline_type_code_to_str(dbf_rec['Type'])

        # DBF 파일을 보고 출력할 파일을 선택한다
        if kind_str == 'Center':
            output_key = 'Lane_Center'

        elif kind_str == 'Normal':
            output_key = 'Lane_Normal'

        elif kind_str == 'NoParking':
            output_key = 'Lane_NoParking'

        else:
            output_key = 'Lane_Misc'

        # 출력해야 할 데이터로 append시킨다.
        _append_list_of_points(output_data[output_key], shp_rec, relative_loc, origin)
    print('')

    print('Writing B2_SURFACELINEMARK data to the corresponding file...', end='')
    for key in output_data.keys():
        fileOpenMode = 'a'
        each_out_file = output_file_name_list[key]
        each_out_data = output_data[key]
        with open(each_out_file, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            writer.writerows(each_out_data)
    print('Done')

    print('[INFO] Ended Successfully.')


def check_exported_files():
    fig = plt.figure()

    input_path = '../../output/ngii_shp_ver2_191226_모라이_제공자료/서울_자율주행테스트베드/SEC01_서울자율주행테스트베드/'

    input_file_name = 'NormalLane.csv'
    _plot_all(os.path.join(input_path, input_file_name), 'b.')

    input_file_name = 'CenterLine.csv'
    _plot_all(os.path.join(input_path, input_file_name), 'y.')

    input_file_name = 'RoadEdge_NoParkingLane.csv'
    _plot_all(os.path.join(input_path, input_file_name), 'g.')

    input_file_name = 'MiscLane.csv'
    _plot_all(os.path.join(input_path, input_file_name), 'k.')

    plt.show()


if __name__ == u'__main__':
    export_to_csv()
    check_exported_files()
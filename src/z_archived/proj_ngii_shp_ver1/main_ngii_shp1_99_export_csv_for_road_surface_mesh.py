"""
융기원에서 제공한 판교 맵에 대한 데이터(shape 포맷으로 되어있음)를
읽고 csv 파일로 출력한다.
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from shp_common import *
import shapefile
import csv
from tkinter import filedialog

def main():

    # 상대좌표로 뽑을 것인가를 결정
    relative_loc = True

    # 초기 경로
    input_init_dir = os.path.join(current_path, '../../rsc/map_data/')

    # 맵 로드할 경로
    input_path = filedialog.askdirectory(
        initialdir = input_init_dir,
        title = 'Load files from') # defaultextension = 'json') 과 같은거 사용 가능   

    # 출력 초기 경로
    output_init_dir = os.path.join(current_path, '../../output_csv/') 
    
    # csv 저장할 경로
    output_path = filedialog.askdirectory(
        initialdir = output_init_dir,
        title = 'Save files to') # defaultextension = 'json') 과 같은거 사용 가능

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    # Get Map Information
    map_info = read_shp_files(input_path)


    # """
    # Origin이 되는 Point를 찾는다
    # Origin은 현재는 A1_LANE에서 검색되는 첫번째 포인트로한다
    # """
    # shapes = map_info['A1_LANE'].shapes()
    # origin_e = shapes[0].points[0][0]
    # origin_n = shapes[0].points[0][1]
    # origin_z = shapes[0].z[0]
    # origin = [origin_e, origin_n, origin_z]

    # origin은 현재 override 함
    origin = [313008.55819800857, 4161698.628368007, 35.66435583359189]
    print('[INFO] Origin =', origin)
    

    """
    출력 파일 Dict 만들기
    """
    output_file_name_list = dict()
    # output_file_name_list['A1_LANE'] = 'A1_LANE.csv'
    output_file_name_list['A1LANE_CenterLine'] = 'A1LANE_CenterLine.csv'
    output_file_name_list['A1LANE_NormalLane'] = 'A1LANE_NormalLane.csv'
    output_file_name_list['A1LANE_MiscLane'] = 'A1LANE_MiscLane.csv'
    output_file_name_list['A1LANE_RoadEdge'] = 'A1LANE_RoadEdge.csv'
    output_file_name_list['A1LANE_Barrier'] = 'A1LANE_Barrier.csv'
    output_file_name_list['A2_STOP'] = 'A2_STOP.csv'
    output_file_name_list['A3_LINK'] = 'A3_LINK.csv'
    output_file_name_list['B2_SURFSIGN_LINE'] = 'B2_SURFSIGN_LINE.csv'
    

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


    # """ A1_LANE 처리 """
    lane = map_info['A1_LANE']

    # TODO(sglee): 함수로 변경
    sf = lane
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    output_data = {}
    output_data['A1LANE_CenterLine'] = list()
    output_data['A1LANE_NormalLane'] = list()
    output_data['A1LANE_MiscLane'] = list()
    output_data['A1LANE_RoadEdge'] = list()
    output_data['A1LANE_Barrier'] = list()

    for i in range(len(shapes)):
        print('Exporting A1_LANE : {} / {}'.format(i+1, len(shapes)), end='\r')
        # DBF 정보를 보고 어느쪽으로 추가할지 결정한다
        dbf_rec = records[i]
        shp_rec = shapes[i]

        # DBF 파일을 보고 출력할 파일을 선택한다
        if dbf_rec['CODE'] == '2':
            key = 'A1LANE_Barrier'
        else:
            if dbf_rec['LANECODE'] == '01':
                key = 'A1LANE_CenterLine'
            elif dbf_rec['LANECODE'] == '03':
                key = 'A1LANE_NormalLane'
            elif dbf_rec['LANECODE'] == '07':
                key = 'A1LANE_RoadEdge'
            else:
                key = 'A1LANE_MiscLane'
        
        _append_list_of_points(output_data[key], shp_rec, relative_loc, origin)
    print('')

    print('Inspecting A1_LANE to each file...', end='')
    for key in output_data.keys():
        fileOpenMode = 'a'
        each_out_file = output_file_name_list[key]
        each_out_data = output_data[key]
        with open(each_out_file, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            writer.writerows(each_out_data)
    print('Done')


    # _export_shp_a1_to_csv(map_info, output_file_name_list, 'A1_LANE', relative_loc, origin)
    _export_shp_line_to_csv(map_info, output_file_name_list, 'A2_STOP', relative_loc, origin)
    _export_shp_line_to_csv(map_info, output_file_name_list, 'A3_LINK', relative_loc, origin)
    _export_shp_line_to_csv(map_info, output_file_name_list, 'B2_SURFSIGN_LINE', relative_loc, origin)

    print('[INFO] Ended Successfully.')


def _export_shp_a1_to_csv(map_info, output_file_name_list, key, relative_loc, origin):
    '''
    PolyLineZ인 선 전체를 csv파일로 출력한다
    '''
    sf = map_info[key]

    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    # 파일에 쓸 데이터를 큰 Array로 만든다
    output_data = list()
    for i in range(len(shapes)):
        print('Inspecting {} : {} / {}'.format(key, i+1, len(shapes)), end='\r')
        shp_rec = shapes[i]
        _append_list_of_points(output_data, shp_rec, relative_loc, origin)
    print('')

    # 파일에 쓰기
    print('Exporting {} to a file...'.format(key), end='')
    fileOpenMode = 'a'
    each_out_file = output_file_name_list[key]
    each_out_data = output_data
    with open(each_out_file, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            writer.writerows(each_out_data)
    print('Done')


def _export_shp_line_to_csv(map_info, output_file_name_list, key, relative_loc, origin):
    '''
    PolyLineZ인 선 전체를 csv파일로 출력한다
    '''
    sf = map_info[key]

    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    # 파일에 쓸 데이터를 큰 Array로 만든다
    output_data = list()
    for i in range(len(shapes)):
        print('Inspecting {} : {} / {}'.format(key, i+1, len(shapes)), end='\r')
        shp_rec = shapes[i]
        _append_list_of_points(output_data, shp_rec, relative_loc, origin)
    print('')

    # 파일에 쓰기
    print('Exporting {} to a file...'.format(key), end='')
    fileOpenMode = 'a'
    each_out_file = output_file_name_list[key]
    each_out_data = output_data
    with open(each_out_file, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            writer.writerows(each_out_data)
    print('Done')


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


def _write_single_line(csvwriter, shp_rec, relative_loc, origin=None):
    if len(shp_rec.points) != len(shp_rec.z):
        raise BaseException('[ERROR] len(shp_rec.points) != len(shp_rec.z)')

    for i in range(len(shp_rec.points)):
        e = shp_rec.points[i][0]
        n = shp_rec.points[i][1]
        z = shp_rec.z[i]

        if relative_loc:
            e = e - origin[0]
            n = n - origin[1]
            z = z - origin[2]
        
        csvwriter.writerow([e,n,z])     


if __name__ == u'__main__':
    main()
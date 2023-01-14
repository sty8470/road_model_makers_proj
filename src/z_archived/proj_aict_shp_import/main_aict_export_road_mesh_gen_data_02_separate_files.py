"""
융기원에서 제공한 판교 맵에 대한 데이터(shape 포맷으로 되어있음)를
읽고 csv 파일로 출력한다.
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import lib.common.shp_common as shp_common
import shapefile
import csv
import numpy as np


def main():
    input_path = '../../rsc/map_data/aict_shp_pangyo/1st2ndIntg_TM_Mid'
    output_path = '../../output/aict_shp_pangyo/'
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
    map_info = shp_common.read_shp_files(input_path)


    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 C1_NODE 중 ID가 206I10440403 인 데이터를 원점으로 한다.
    NGII SHP2 데이터에서 같은 위치의 ID는 A119AS305498 이다.
    """
    sf = map_info['C1_NODE']
    shapes = sf.shapes()
    records = sf.records()
    fields = sf.fields

    for i in range(len(sf)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        if dbf_rec['NODEID'] == '206I10440403':
            e = shp_rec.points[0][0]
            n = shp_rec.points[0][1] 
            z = shp_rec.z[0]
            origin = [e, n ,z]
            break

    origin = np.array([e, n ,z])
    print('[INFO] Origin =', origin.tolist())
    # 이렇게 구한 Origin은 다음과 같다 (TM좌표계임에 유의)
    # [INFO] Origin = [209402.0923992687, 533433.0495021925, 39.684636742713245]


    """
    출력 파일 Dict 만들기
    """
    output_file_name_list = dict()
    output_file_name_list['A1LANE_CenterLine'] = 'A1LANE_CenterLine.csv'
    output_file_name_list['A1LANE_NormalLane'] = 'A1LANE_NormalLane.csv'
    output_file_name_list['A1LANE_MiscLane'] = 'A1LANE_MiscLane.csv'
    output_file_name_list['A1LANE_RoadEdge'] = 'A1LANE_RoadEdge.csv'
    output_file_name_list['A1LANE_Barrier'] = 'A1LANE_Barrier.csv'
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


    """ A1_LANE 처리 """
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



    """ B2_SURFSIGN_LINE 처리 """
    center_path = map_info['B2_SURFSIGN_LINE']

    # TODO(sglee): 함수로 변경
    sf = center_path
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    key = 'B2_SURFSIGN_LINE'
    # 파일에 쓸 데이터를 큰 Array로 만든다
    output_data = list()
    for i in range(len(shapes)):
        print('Inspecting B2_SURFSIGN_LINE : {} / {}'.format(i+1, len(shapes)), end='\r')
        shp_rec = shapes[i]
        _append_list_of_points(output_data, shp_rec, relative_loc, origin)
    print('')

    # 파일에 쓰기
    print('Exporting B2_SURFSIGN_LINE to a file...', end='')
    fileOpenMode = 'a'
    each_out_file = output_file_name_list[key]
    each_out_data = output_data
    with open(each_out_file, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            writer.writerows(each_out_data)
    print('Done')

    print('[INFO] Ended Successfully.')


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
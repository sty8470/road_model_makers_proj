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
import lib.common.shp_csv_export as shp_csv_export
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

    # csv로 변경할 key 종류들
    key_list = ['A1_LANE', 'B2_SURFSIGN_LINE']

    for key in key_list:
        input_shape = map_info[key]
        
        # shp data -> exportable data
        export_data = shp_csv_export.to_csv_exportable_data(input_shape, origin)

        # exportable data -> csv file
        output_file = os.path.join(output_path, key) + '.csv'
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            writer.writerows(export_data)

if __name__ == u'__main__':
    main()
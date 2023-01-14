"""
융기원에서 제공한 판교 맵에 대한 데이터(shape 포맷으로 되어있음)를
읽고 road object 배치를 위한 파일을 생성한다
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import lib.common.shp_common as shp_common
import lib.common.shp_csv_export as shp_csv_export
import lib_ngii_shp1.morai_sim_build_data_exporter as ngii_shp1_exporter

import shapefile
import csv
import numpy as np


def main():
    input_path = '../../rsc/map_data/aict_shp_pangyo/1st2ndIntg_TM_Mid'
    output_path = '../../output/aict_shp_pangyo/'

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

    print('[INFO] Export TL & PS...')
    ngii_shp1_exporter.export_tl(output_path, map_info['B1_SIGNAL_POINT'], origin)
    print('[INFO]   >> DONE OK')

    print('[INFO] Export TS ...')
    aict_export_ts(output_path, map_info['B1_SIGN_POINT'], map_info['A3_LINK'], origin)
    print('[INFO]   >> DONE OK')

    print('[INFO] Export SM ...')
    ngii_shp1_exporter.export_sm(output_path, map_info['B2_SURFSIGN_POINT'], origin)
    print('[INFO]   >> DONE OK')


def aict_export_ts(output_path, sf_ts, sf_link, origin):
    """융기원 데이터에서 표지판은 신호등이나 노면표시와 달리, 별도 함수로 처리해야 한다. 
    왜냐하면, 우선 표지판은 생성할 때 LINK정보를 참조해야하는데 (최대 속도 제한 같은 표지판 때문)
    융기원 데이터는 LINK정보를 참조하는 방식이 NGII SHP1 버전과 다르기 때문이다.
    (융기원 데이터에선 TL, TS 등에서 LINKID 앞 8자리와, 각 링크의 HDUFID 앞 8자리를 매치시켜야 함)
    """
    to_csv_list = []

    asset_path_root = 'Assets/1_Module/Map/MapCommonModule/RoadObject/Prefabs/'

    """ SIGNAL POINT 출력하기 """
    shapes = sf_ts.shapes()
    records  = sf_ts.records()
    fields = sf_ts.fields

    data_to_export = list() 

    for i in range(len(shapes)):
        # print('i = {}'.format(i))
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # [STEP #01] 우선 point 구하기
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        # SIGNAL_POINT같이 point인 데이터에서는,첫번째 값을 가져오면 된다.
        point = shp_rec.points[0]


        # INFO #1
        # signal의 타입으로부터 signal prefab 파일을 찾는다
        idx = dbf_rec['HDUFID']
        result, file_path, file_name =\
            get_traffic_sign_asset_path_and_name(dbf_rec, sf_link)
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue

        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path

        # INFO #2
        pos = __local_utm_to_sim_coord(point) # 시뮬레이터 좌표계로 변환이 필요
        position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

        # INFO #3
        orientation_string = '0.0/0.0/0.0'

        # csv 파일 출력을 위한 리스트로 추가
        to_csv_list.append([file_path, file_name, position_string, orientation_string, idx])

    # 신호등 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'road_obj_gen_data_traffic_sign.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)


def get_traffic_sign_asset_path_and_name(dbf_rec, sf_link):
    """
    NOTE: 융기원 데이터에서 표지판은 신호등이나 노면표시와 달리, 별도 함수로 처리해야 한다. 
    왜냐하면, 우선 표지판은 생성할 때 LINK정보를 참조해야하는데 (최대 속도 제한 같은 표지판 때문)
    융기원 데이터는 LINK정보를 참조하는 방식이 NGII SHP1 버전과 다르기 때문이다.
    (융기원 데이터에선 TL, TS 등에서 LINKID 앞 8자리와, 각 링크의 HDUFID 앞 8자리를 매치시켜야 함)
    
    NOTE: NGII SHP2 타입으로 변경한 후, 파일명에 매칭시킨다.
    왜냐하면 현재 표지판 Prefab 이름이 Shp Ver2 포맷의 정의대로 되어있기 때문. 
    """
    idx = dbf_rec['HDUFID']
    prop_type = dbf_rec['CODE']
    prop_sub_type = dbf_rec['SIGNTYPE']

    # NGII SHP2 버전의 Type으로 변경하는 함수
    prop_sub_type = ngii_shp1_exporter.shp1_sign_type_to_shp2_ts_type(prop_sub_type)

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
        
        # 최고 속도 제한 표지판
        if prop_sub_type == '224':
            # 링크 찾기
            find_result, max_speed = aict_find_matching_link_and_get_max_speed(dbf_rec['LINKID'], sf_link)
            if not find_result:
                print('[ERROR] @ get_traffic_sign_asset_path_and_name: Failed to find link for ts id = {}'.format(idx))
                return False, '', ''

            prop_sub_type = '{}_{}kph'.format(prop_sub_type, max_speed)
        
        file_name = '02_Restriction_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '3':
        file_path = '01_MapCommon_Signs/03_Indication_Beam'
        file_name = '03_Indication_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '4':
        file_path = '01_MapCommon_Signs/04_Aux_Beam'
        file_name = '04_Aux_{}_Beam.prefab'.format(prop_sub_type)

    else:
        raise BaseException('[ERROR] @ __get_traffic_sign_asset_path_and_name: unexpected prop_type! (you passed = {}) (ts id = {})'.format(prop_type, idx))

    return True, file_path, file_name


def aict_find_matching_link_and_get_max_speed(link_id, sf_link):
    """NOTE: 융기원 데이터에서는 전달받은 link_id의 앞 8자리만 사용한다.
    또한, 이 link_id와 비교하는 각 링크의 실제 id에서도 앞 8자리만 사용한다. 
    """
    link_id = link_id[:8] # 앞자리만 비교한다 (융기원 데이터 특성)

    shapes = sf_link.shapes()
    records  = sf_link.records()
    fields = sf_link.fields

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        if link_id == dbf_rec['LINKID'][:8]:
            return True, dbf_rec['SPEED']

    return False, 0

    
def __local_utm_to_sim_coord(local_utm):
    # Local UTM  X, Y, Z = East, North, Up
    # Simulation X, Y, Z = West, Up, South
    
    sim_x = -1 * local_utm[0]
    sim_y = local_utm[2]
    sim_z = -1 * local_utm[1]

    return np.array([sim_x, sim_y, sim_z])


if __name__ == u'__main__':
    main()
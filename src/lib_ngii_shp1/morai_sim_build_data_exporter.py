import os
import csv 
import numpy as np


def export_tl(output_path, sf, origin):
    to_csv_list = []

    asset_path_root = 'Assets/1_Module/Map/MapCommonModule/RoadObject/Prefabs/'

    """ SIGNAL POINT 출력하기 """
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

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
        signal_type = dbf_rec['SIGNTYPE']         
        result, file_path, file_name =\
            __get_traffic_light_asset_path_and_name(dbf_rec)
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
    output_file_name = os.path.join(output_path, 'road_obj_gen_data_traffic_light.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)


def export_sm(output_path, sf, origin):
    to_csv_list = []

    asset_path_root = 'Assets/1_Module/Map/MapCommonModule/RoadObject/Prefabs/'

    """ SIGNAL POINT 출력하기 """
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

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
        signal_type = dbf_rec['SIGNTYPE']         
        result, file_path, file_name =\
            __get_surface_marking_asset_path_and_name(dbf_rec)
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
    output_file_name = os.path.join(output_path, 'road_obj_gen_data_surface_marking.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)


def __get_traffic_light_asset_path_and_name(dbf_rec):
    """NGII Shp1 포맷의 B1_SIGNAL_POINT의 dbf_rec에 대해서 파일명을 생성한다"""

    idx = dbf_rec['HDUFID']
    signal_type = dbf_rec['SIGNTYPE']

    if signal_type == '501': # 횡형 이색등
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '502': # 횡형 삼색등
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Hor_RYG.prefab'
        return True, file_path, file_name

    elif signal_type == '503': # 횡형 자전거삼색등
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '504': # 횡형 버스삼색등
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '505': # 횡형 사색등 A
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Hor_RYLgG.prefab'
        return True, file_path, file_name

    elif signal_type == '506': # 횡형 사색등B
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '507': # 종형 이색등
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '508': # 보행등
        file_path = '01_MapCommon_PS'
        file_name = 'PS_RG.prefab'
        return True, file_path, file_name

    elif signal_type == '509': # 자전거 이색등
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '510': # 종형 삼색등
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '511': # 차량 보조등
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '512': # 버스 삼색등
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '513': # 자전거 삼색등
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '514': # 종형 사색등
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '515': # 경보형 경보등
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    elif signal_type == '519': # 기타 
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this signal_type = {} (id = {})'.format(signal_type, idx))
        return False, '', ''

    else:
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: unexpected signal_type = {} (not in the documentation) (id = {})'.format(signal_type, idx))
        return False, '', ''


def __get_surface_marking_asset_path_and_name(dbf_rec):
    idx = dbf_rec['HDUFID']
    prop_type = dbf_rec['SIGNTYPE']

    prop_type = shp1_sign_type_to_shp2_sm_type(prop_type)

    if prop_type in ['599']:
        # 599: Misc.

        print('[WARNING] @ __get_surface_marking_asset_path_and_name: no supported model for this prop_type = {} (sm id = {})'.format(prop_type, idx))
        return False, '', ''

    file_path = 'KR_SurfaceMarking'
    file_name = '05_SurfMark_{}.fbx'.format(prop_type)
    
    return True, file_path, file_name


def shp1_sign_type_to_shp2_ts_type(sign_type):
    sign_type = int(sign_type)
    sign_mapping_table = [
        [101, 110], [102, 125], [103, 132],
        [104, 133], [105, 134], [106, 138],
        [107, 1832], [108, 126], [109, 128],
        [110, 129], [199, 199],
        [201, 201], [202, 202], [203, 203],
        [204, 204], [205, 205], [206, 206],
        [207, 207], [208, 208], [209, 211],
        [210, 212], [211, 213], [212, 214],
        [213, 215], [214, 217], [215, 218],
        [216, 219], [217, 220], [218, 221],
        [219, 222], [220, 223], [221, 224],
        [222, 225], [223, 226], [224, 227],
        [225, 228], [226, 230], [227, 231],
        [299, 299],
        [301, 304], [302, 305], [303, 306],
        [304, 307], [305, 308], [306, 309],
        [307, 3092], [308, 310], [309, 311],
        [310, 312], [311, 313], [312, 314],
        [313, 315], [314, 316], [315, 329],
        [316, 326], [317, 327], [318, 328],
        [319, 321], [320, 322], [321, 323],
        [322, 324], [323, 3242], [399, 399],
        [499, 499]
    ]

    for mapping in sign_mapping_table:
        if sign_type == mapping[0]:
            return str(mapping[1])

    raise BaseException('[ERROR] @ shp1_sign_type_to_shp2_ts_type: Unexpected input value {}'.format(sign_type))


def shp1_sign_type_to_shp2_sm_type(sign_type):
    sign_type = int(sign_type)
    sign_mapping_table = [
        [101, 5371], [102, 5373], [103, 5372],
        [104, 5382], [105, 5381], [106, 5392],
        [107, 5391], [108, 5379], [109, 5374],
        [110, 5383],
        [201, 5431], [202, 5432],
    ]

    for mapping in sign_mapping_table:
        if sign_type == mapping[0]:
            return str(mapping[1])

    raise BaseException('[ERROR] @ shp1_sign_type_to_shp2_sm_type: Unexpected input value {}'.format(sign_type))    

    
def __local_utm_to_sim_coord(local_utm):
    # Local UTM  X, Y, Z = East, North, Up
    # Simulation X, Y, Z = West, Up, South
    
    sim_x = -1 * local_utm[0]
    sim_y = local_utm[2]
    sim_z = -1 * local_utm[1]

    return np.array([sim_x, sim_y, sim_z])
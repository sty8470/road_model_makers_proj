import os
import csv
import numpy as np


def export_ts(output_path, ts_set, link_set):
    to_csv_list = []

    asset_path_root = 'Assets/1_Module/Map/MapCommonModule/RoadObject/Prefabs/'

    for idx, item in ts_set.signals.items():
        # REFACTOR(sglee) >> value 설정 (type = 224인 케이스에 대해)
        if item.sub_type == '224':
            # value가 설정되어있지 않을때만 설정해준다
            if (item.value is None) or (item.value == '') or (item.value == 0):
                # NOTE: link_id_list 중에서 첫번째 것을 사용하여 값을 찾는다
                if len(item.link_list) == 0:
                    print('ERROR')
                related_link = item.link_list[0]
                item.value = related_link.get_max_speed_kph()
         
        # signal의 타입으로부터 signal prefab 파일을 찾는다         
        result, file_path, file_name =\
            __get_traffic_sign_asset_path_and_name(item)
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue
        
        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path

        # INFO #2
        pos = item.point
        pos = __local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
        position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

        # INFO #3
        orientation_string = '0.0/0.0/0.0'

        # csv 파일 출력을 위한 리스트로 추가
        to_csv_list.append([file_path, file_name, position_string, orientation_string, idx])

    # 표지판 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'sim_build_data_traffic_sign.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)


def export_tl(output_path, tl_set, link_set):
    to_csv_list = []

    asset_path_root = 'Assets/1_Module/Map/MapCommonModule/RoadObject/Prefabs/'

    for idx, item in tl_set.signals.items():
        
        # INFO #1
        # signal의 타입으로부터 signal prefab 파일을 찾는다         
        result, file_path, file_name =\
            __get_traffic_light_asset_path_and_name(item)
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue
        
        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path

        # INFO #2
        pos = item.point
        pos = __local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
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


def export_sm(output_path, sm_set, link_set):
    to_csv_list = []

    asset_path_root = 'Assets/1_Module/Map/MapCommonModule/RoadObject/Models/'
    print('[DEBUG] export_sm')
    for idx, item in sm_set.data.items():
        
        # INFO #1
        # signal의 타입으로부터 signal prefab 파일을 찾는다         
        result, file_path, file_name =\
            __get_surface_marking_asset_path_and_name(item, inspect_model_exists=False)
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue
        
        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path

        # INFO #2
        # 마지막 점을 제외하고, center of mass를 구한다.
        # 마지막 점을 제외하는 이유: 첫번째 점과 같은 점이다.
        ceteroid = __calculate_centeroid_in_polygon(item.points[0:-1])

        # NOTE: centeroid를 link로 snap 시켜보려고했는데 좋지 않은 결과가 나옴
        # 향후 다시 살펴볼 필요가 있음. (proj_code42_sample_import/main_mgeo_export_road_objects.py 내 코드 남아있음. 참조.)

        pos = __local_utm_to_sim_coord(ceteroid) # 시뮬레이터 좌표계로 변환이 필요
        position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

        # INFO #3
        orientation_string = '0.0/0.0/0.0'

        # csv 파일 출력을 위한 리스트로 추가
        to_csv_list.append([file_path, file_name, position_string, orientation_string, idx])

    # 신호등 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'sim_build_data_surface_marking.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)


def __get_traffic_sign_asset_path_and_name(ts):
    """NGII Shp Ver2 포맷으로 제공된 표지판 정보를 담고있는 MGeo Signal 인스턴스에서 시뮬레이터 배치용 csv 파일을 생성하는 메소드"""
    prop_type = ts.type
    prop_sub_type = ts.sub_type
    prop_value = ts.value

    # UPDATE(sglee): 지원 안 되는 prop_sub_type 지속적으로 업데이트
    if prop_sub_type in ['199', '299', '399', '499', '225']:
        # 225: 최저 속도 제한 >> 최저 속도 값을 link에서 받아와야 모델을 특정할 수 있는데, link에 최저 속도 값이 없음 

        print('[WARNING] @ __get_traffic_sign_asset_path_and_name: no supported model for this prop_sub_type = {} (ts id = {})'.format(prop_sub_type, ts.idx))
        return False, '', ''

    # NOTE: 현재 prop_type 2와 3이 반대로 되어있는 것 같음
    # if prop_type == '2':
    #     prop_type = '3'
    # elif prop_type == '3':
    #     prop_type = '2' 


    if prop_type == '1':
        file_path = '01_MapCommon_Signs/01_Caution_Beam'
        file_name = '01_Caution_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '2':
        file_path = '01_MapCommon_Signs/02_Restriction_Beam'
        
        if prop_sub_type == '224':
            if (prop_value is None) or (prop_value is '') or (prop_value is 0):
                raise BaseException('[WARNING] @ __get_traffic_sign_asset_path_and_name: value is not set for traffic sign object with sub_type = {} (ts id = {})'.format(prop_sub_type, ts.idx))
            # prop_subtype을 변경해준다
            prop_sub_type = '{}_{}kph'.format(prop_sub_type, prop_value)
        
        file_name = '02_Restriction_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '3':
        file_path = '01_MapCommon_Signs/03_Indication_Beam'
        file_name = '03_Indication_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '4':
        file_path = '01_MapCommon_Signs/04_Aux_Beam'
        file_name = '04_Aux_{}_Beam.prefab'.format(prop_sub_type)

    else:
        raise BaseException('[ERROR] @ __get_traffic_sign_asset_path_and_name: unexpected prop_type! (you passed = {}) (ts id = {})'.format(prop_type, ts.idx))

    return True, file_path, file_name


def __get_traffic_light_asset_path_and_name(tl):
    """NGII Shp Ver2 포맷으로 제공된 신호등 정보를 담고있는 MGeo Signal 인스턴스에서 시뮬레이터 배치용 csv 파일을 생성하는 메소드"""
    prop_type = tl.type

    if prop_type in ['99']:
        print('[WARNING] @ __get_traffic_light_asset_path_and_name: no supported model for this prop_type = {} (tl id = {})'.format(prop_type, tl.idx))
        return False, '', ''

    # 
    if prop_type == '1':
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Hor_RYG.prefab'

    elif prop_type == '2':
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Hor_RYLgG.prefab'
    
    elif prop_type == '5':
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Ver_RYG.prefab'

    elif prop_type == '11':
        # 보행자 신호등 (NGII)
        file_path = '01_MapCommon_PS'
        file_name = 'PS_RG.prefab'

    else:
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Misc_NGII_Shp2_{}.prefab'.format(prop_type)
        print('[ERROR] @ __get_traffic_light_asset_path_and_name: unexpected prop_type! (you passed = {} (tl id = {}))'.format(prop_type, tl.idx))

    return True, file_path, file_name


def __get_surface_marking_asset_path_and_name(sm, inspect_model_exists=True):
    if int(sm.type) == 5: # 횡단보도인 경우임
        print('[WARNING] @ __get_surface_marking_asset_path_and_name: crosswalk is not supported (sm id = {})'.format(sm.idx))
        return False, '', ''

    prop_type = int(sm.sub_type)

    # UPDATE(sglee): 지원 안 되는 prop_subtype 지속적으로 업데이트
    if prop_type in [599]:
        # 599: Misc.

        print('[WARNING] @ __get_surface_marking_asset_path_and_name: no supported model for this prop_type = {} (sm id = {})'.format(prop_type, sm.idx))
        return False, '', ''

    file_path = 'KR_SurfaceMarking'
    file_name = '05_SurfMark_{}.fbx'.format(prop_type)

    if inspect_model_exists:
        # 개발 PC에서의 경로를 입력해준다
        abs_path = 'D:\\workspace\\sim_platform\\MasterSimulator\\Assets\\0_Master\\3_Prefabs\\RoadObjects\\KR_SurfaceMarking'
        linked_file_full_path = os.path.join(abs_path, file_name)

        print('[DEBUG] linked_file_full_path: ', linked_file_full_path)
        if not (os.path.exists(linked_file_full_path) and os.path.isfile(linked_file_full_path)):
            # 해당 모델이 존재하지 않음
            raise BaseException('[ERROR] @ __get_surface_marking_asset_path_and_name: Unsupported model file (sm id = {})'.format(sm.idx))
    
    return True, file_path, file_name


# TODO(sglee): Refactor this! Polygon 인 Surface Marking의 Point를 계산하는데 사용되는 함수 
def __calculate_centeroid_in_polygon(point_list):
    '''
    polygon을 구성하는 점들로부터 centeroid를 계산한다.
    밀도가 균일하다면 center of mass와 동일하며,
    이 점은 각 좌표의 산술 평균이다.
    '''
    x = point_list[:,0]
    y = point_list[:,1]
    z = point_list[:,2]

    return np.array([np.mean(x), np.mean(y), np.mean(z)])


# TODO(sglee): Refactor this! Polygon 인 Surface Marking의 Point를 계산하는데 사용되는 함수 
def __find_nearest_node_in_link(ref_point, link_points, distance_using_xy_only, dist_threshold=10):
    '''
    link_points 내부의 많은 점들 가운데서, ref_point와 가장 가까운 point를 찾아준다
    '''
    # 가장 가까운 노드와, 노드까지의 거리를 찾는다
    min_dist = np.inf
    nearest_point = None

    for point in link_points:       
        if distance_using_xy_only:
            pos_vect = point[0:2] - ref_point[0:2]
        else:
            pos_vect = point - ref_point
        
        dist = np.linalg.norm(pos_vect, ord=2)
        if dist < min_dist:
            min_dist = dist
            nearest_point = point
    
    # 가장 가까운 노드까지의 거리가 정한 값보다 작으면, 적합한 노드가 있는 것이다
    if min_dist < dist_threshold:
        return True, nearest_point
    else:
        return False, None


def __local_utm_to_sim_coord(local_utm):
    # Local UTM  X, Y, Z = East, North, Up
    # Simulation X, Y, Z = West, Up, South
    
    sim_x = -1 * local_utm[0]
    sim_y = local_utm[2]
    sim_z = -1 * local_utm[1]

    return np.array([sim_x, sim_y, sim_z])
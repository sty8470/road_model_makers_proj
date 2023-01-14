import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # 프로젝트 Root 경로

from lib.mgeo.class_defs import *
import lib.mgeo.utils.lane_change_link_creation as mgeo_lane_ch_link_gen
import lib.mgeo.utils.error_fix as error_fix

import numpy as np
import json


def read_geojson_files(input_path):
    file_list = os.listdir(input_path)
    map_info = {}

    for each_file in file_list:
        file_full_path = os.path.join(input_path, each_file)
        
        # 디렉토리는 Skip
        if os.path.isdir(file_full_path):
            continue
        
        # geojson인지 체크
        filename, file_extension = os.path.splitext(each_file)
        if file_extension == '.geojson':
            # 처리
            with open(file_full_path) as input_file:
                map_info[filename] = json.load(input_file)

    return map_info


def get_traffic_sign_asset_path_and_name(prop_type, prop_subtype, link=None):
    '''
    CODE42 GeoJSON의 B1_SAFETYSIGN 데이터의 Type, SubType으로부터,
    시뮬레이터 내 자동 배치를 위한 csv 파일을 생성한다.
    '''

    prop_type = int(prop_type)
    prop_subtype = int(prop_subtype)

    # UPDATE(sglee): 지원 안 되는 prop_subtype 지속적으로 업데이트
    if prop_subtype in [199, 299, 399, 499, 225]:
        # 225: 최저 속도 제한 >> 최저 속도 값을 link에서 받아와야 모델을 특정할 수 있는데, link에 최저 속도 값이 없음 

        print('[WARNING] @ get_traffic_sign_asset_path_and_name: no supported model for this prop_subtype = {}'.format(prop_subtype))
        return False, '', ''

    # NOTE: 현재 prop_type 2와 3이 반대로 되어있는 것 같음
    if prop_type == 2:
        prop_type = 3
    elif prop_type == 3:
        prop_type = 2 


    if prop_type == 1:
        file_path = 'KR_TrafficSign/01_Caution_Beam'
        file_name = '01_Caution_{}_Beam.prefab'.format(prop_subtype)


    elif prop_type == 2:
        file_path = 'KR_TrafficSign/02_Restriction_Beam'
        
        if prop_subtype == 224:
            if link is None:
                raise BaseException('[WARNING] @ get_traffic_sign_asset_path_and_name: no link is found for B1_SAFETYSIGN with prop_subtype = {}'.format(prop_subtype))
            
            # prop_subtype을 변경해준다
            prop_subtype = '{}_{}kph'.format(prop_subtype, link.get_max_speed_kph())

        file_name = '02_Restriction_{}_Beam.prefab'.format(prop_subtype)


    elif prop_type == 3:
        file_path = 'KR_TrafficSign/03_Indication_Beam'
        file_name = '03_Indication_{}_Beam.prefab'.format(prop_subtype)


    elif prop_type == 4:
        file_path = 'KR_TrafficSign/04_Aux_Beam'
        file_name = '04_Aux_{}_Beam.prefab'.format(prop_subtype)

    else:
        raise BaseException('[ERROR] @ get_traffic_sign_asset_path_and_name: unexpected prop_type! (you passed = {})'.format(prop_type))

    return True, file_path, file_name


def get_surface_marking_asset_path_and_name(prop_type, inspect_model_exists=True):
    prop_type = int(prop_type)

    # UPDATE(sglee): 지원 안 되는 prop_subtype 지속적으로 업데이트
    if prop_type in [599]:
        # 599: Misc.

        print('[WARNING] @ get_surface_marking_asset_path_and_name: no supported model for this prop_type = {}'.format(prop_type))
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
            raise BaseException('[ERROR] @ get_surface_marking_asset_path_and_name: Unsupported model file')
    
    return True, file_path, file_name


def surfline_kind_code_to_str(num):
    if num == '501':
        return 'Lane_Center'
    elif num == '502':
        return 'Lane_Uturn'
    elif num == '503':
        return 'Lane_Normal'
    elif num == '505':
        return 'Lane_Border'
    elif num == '515':
        return 'Lane_NoParking'
    elif num == '525':
        return 'Lane_Guide'
    elif num == '530':
        return 'Lane_StopLine'
    elif num == '531':
        return 'Lane_SafeArea'
    elif num == '599':
        return 'Lane_Undef'
    else:
        raise BaseException('[ERROR] Undefined kind value')


def surfline_type_code_to_str(num):
    if num == '111':
        return 'YSS'
    elif num == '112':
        return 'YSB'
    elif num == '121':
        return 'YDS'

    elif num == '211':
        return 'WSS'
    elif num == '212':
        return 'WSB'
    elif num == '214':
        return 'WhiteUndef'
    elif num == '999':
        return 'Undef'
    else:
        raise BaseException('[ERROR] Undefined type value')


def get_origin(map_info):
    """
    이 중에서 우리가 관심을 갖는 대상은 다음과 같고, 
    특히 'features'가 주요 관심의 대상이다. 
    이를 surf_line_list로 지정하자
    """
    b2 =  map_info['B2_SURFACELINEMARK']
    b2['crs']
    b2['features']
    b2['name']
    b2['type']

    surf_line_list = map_info['B2_SURFACELINEMARK']['features']

    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 surf_line_list에서 검색되는 첫번째 포인트로한다
    """
    line0 = surf_line_list[0]
    line0_point0 = line0['geometry']['coordinates'][0]
    origin = line0_point0
    return origin


def find_obj_using_id(geojson_layer, _id):
    """
    id를 이용해서 object를 찾아준다.
    예를들면 A2_LINK에서 특정 ID를 갖는 LINK를 검색해준다
    """
    return find_obj_using_property(geojson_layer, 'ID', _id)


def find_obj_using_property(geojson_layer, prop_name, prop_value):
    """
    특정 property (prop_name)이 prop_value인 object를 찾아준다 
    """
    for i, item in enumerate(geojson_layer['features']):
        obj_prop = item['properties'] # item와 매우 유사
        if obj_prop[prop_name] == prop_value:
            return item
    
    raise BaseException('[ERROR] Cannot find obj with {} = {}'.format(prop_name, prop_value))


def create_node_set_and_link_set(map_info, origin):
    '''
    CODE42의 GeoJSON으로부터 node_set과 link_set을 생성하여 리턴한다.
    '''

    """ GeoJSON의 A1_NODE로부터 NodeSet 타입 생성하기 """
    a1_node = map_info['A1_NODE']
    node_set = NodeSet()
    for i, item in enumerate(a1_node['features']):
        obj_prop = item['properties'] # item와 매우 유사
        
        coord_obj = np.array(item['geometry']['coordinates'])

        if coord_obj.shape != (3,):
            raise BaseException('[ERROR] @ create_node_set_and_link_set, coord_obj.shape is not (3,).')

        coord_obj = coord_obj - origin
        
        node = Node(obj_prop['ID'])
        node.point = coord_obj
        node_set.nodes[node.idx] = node


    """ GeoJSON의 A2_LINK로 부터 LinkSetDict 타입 생성하기 """
    a2_link = map_info['A2_LINK']
    link_set = LineSet()
    for i, item in enumerate(a2_link['features']):
        obj_prop = item['properties'] # item와 매우 유사
        
        coord_obj = np.array(item['geometry']['coordinates'])
        coord_obj = coord_obj - origin

        # 현재는 전부 바로 point가 init되는 Link를 생성
        link = Link(points=coord_obj, idx=obj_prop['ID'], lazy_point_init=False, link_type=obj_prop['LinkType'])
        
        # 링크의 최대 속도, 최저 속도 설정 >> 최저 속도는 keys에 현재 없는 것 같아 조건문으로 처리함.
        link.set_max_speed_kph(int(obj_prop['MaxSpeed']))
        if 'MinSpeed' in obj_prop.keys():
            link.set_min_speed_kph(int(obj_prop['MinSpeed']))

        error_link_from_node = False
        error_link_to_node = False
        
        # link의 끝점 또는 시작점이 FromNode, ToNode 시작점과 같은 위치에 있는지 
        # 판단할 때 사용하는 거리 기준값
        dist_threshold = 0.3 

        # FromNode를 찾을 수 없는 경우가 있으므로 이렇게 체크
        error_msg1 = '  ERROR  >> '  
        if obj_prop['FromNodeID'] in node_set.nodes:          
            from_node = node_set.nodes[obj_prop['FromNodeID']]

            # 노드가 있더라도, 우선 위치가 맞는지 검색해본다
            # NOTE: 가끔 z좌표가 이상한 경우가 있어, x,y 좌표만 거리 계산에 사용    
            point = link.points[0] # 링크의 시작점
            dist = np.linalg.norm(point[0:2] - from_node.point[0:2], ord=2)
            if dist > dist_threshold:
                error_msg1 += 'Incorrect FromNode = {} (distance = {:.2f} m)'.format(obj_prop['FromNodeID'], dist)
                error_link_from_node = True
            else:
                # 정상인 경우 -> from_node로 설정해준다
                link.set_from_node(from_node)
            
        else:
            error_msg1 += 'Cannot find FromNode = {}'.format(obj_prop['FromNodeID'])
            error_link_from_node = True
            
        # ToNode를 찾을 수 없는 경우가 있으므로 이렇게 체크
        error_msg2 = '  ERROR  >> '
        if obj_prop['ToNodeID'] in node_set.nodes:
            to_node = node_set.nodes[obj_prop['ToNodeID']]

            # 노드가 있더라도, 우선 위치가 맞는지 검색해본다
            # NOTE: 가끔 z좌표가 이상한 경우가 있어, x,y 좌표만 거리 계산에 사용    
            point = link.points[-1] # 링크의 끝점
            dist = np.linalg.norm(point[0:2] - to_node.point[0:2], ord=2)
            if dist > dist_threshold:
                error_msg2 += 'Incorrect ToNode = {} (distance = {:.2f} m)'.format(obj_prop['ToNodeID'], dist)
                error_link_to_node = True
            else:
                # 정상인 경우 -> to_node로 설정해준다
                link.set_to_node(to_node)
        else:
            error_msg2 += 'Cannot find ToNode = {}'.format(obj_prop['ToNodeID'])
            error_link_to_node = True
            

        solved_msg1 = '  SOLVED >> '
        if error_link_from_node:
            find_result, node_idx = error_fix.search_for_a_from_node_and_set(link, node_set, from_node)
            if find_result:
                solved_msg1 += 'Connected to an existing node = {}'.format(node_idx)
            else:
                solved_msg1 += 'Created a new node = {}'.format(node_idx)

        solved_msg2 = '  SOLVED >> '
        if error_link_to_node:
            find_result, node_idx = error_fix.search_for_a_to_node_and_set(link, node_set, to_node)
            if find_result:
                solved_msg2 += 'Connected to an existing node = {}'.format(node_idx)
            else:
                solved_msg2 += 'Created a new node = {}'.format(node_idx)


        # 에러 발생한 경우 리포트
        if error_link_from_node or error_link_to_node:
            print('[ERROR in Link = {}]'.format(obj_prop['ID']))
            if error_link_from_node:
                print(error_msg1)
                print(solved_msg1)
            if error_link_to_node:
                print(error_msg2)
                print(solved_msg2)

            print('----------------------------------')

        # [NOTE] ERROR 있는 링크 visualization 따로 할 경우 주석 해제
        if error_link_from_node or error_link_to_node:
            link.set_vis_mode_manual_appearance(1, 'r')
        else:
            link.set_vis_mode_manual_appearance(1, 'k')

        link_set.lines[link.idx] = link


    """ 위에서 설정이 안 된 차선 변경 정보를 입력하기 """
    set_lane_change_info_into_link_set(map_info, link_set)

    return node_set, link_set


def set_lane_change_info_into_link_set(map_info, link_set):
    '''
    현재의 A2_LINK 데이터를 참조하여, 생성된 link_set에
    차선 변경으로 진입 가능한 link 정보를 기록한다
    '''
    a2_link = map_info['A2_LINK']
    lane_ch_link_set = LineSet()
    for i, item in enumerate(a2_link['features']):
        obj_prop = item['properties'] # item와 매우 유사

        src_line = link_set.lines[obj_prop['ID']]
        
        if obj_prop['LinkType'] in ['1', '2', '3']:
            continue

        if obj_prop['L_LinkID'] is not None:
            dst_line = link_set.lines[obj_prop['L_LinkID']]

            # [ERROR CHECK] dst_line의 R_LinkID가 src_line의 ID이어야한다
            related_link = find_obj_using_id(a2_link, obj_prop['L_LinkID'])
            if related_link['properties']['R_LinkID'] != obj_prop['ID']:
                print('[ERROR @ GeoJSON Data] LinkID={} has L_LinkID={}, but LinkID={} has R_LinkID={}'.format(
                    obj_prop['ID'],
                    obj_prop['L_LinkID'],
                    related_link['properties']['ID'],
                    related_link['properties']['R_LinkID']))
                continue

            to_node = dst_line.get_to_node()
            from_node = src_line.get_from_node()

            # Check: 분기하는 경우 or 합류하는 경우가 있으므로, 이런 경우는 생성할 필요가 없다
            if (to_node is src_line.get_to_node()) or (from_node is dst_line.get_from_node()):
                continue

            # 차선 변경으로 진입할 선으로 등록
            src_line.set_left_lane_change_dst_link(dst_line)

        
        if obj_prop['R_LinkID'] is not None:
            dst_line = link_set.lines[obj_prop['R_LinkID']]

            # [ERROR CHECK] dst_line의 L_LinkID가 src_line의 ID이어야한다
            related_link = find_obj_using_id(a2_link, obj_prop['R_LinkID'])
            if related_link['properties']['L_LinkID'] != obj_prop['ID']:
                print('[ERROR @ GeoJSON Data] LinkID={} has R_LinkID={}, but LinkID={} has L_LinkID={}'.format(
                    obj_prop['ID'],
                    obj_prop['R_LinkID'],
                    related_link['properties']['ID'],
                    related_link['properties']['L_LinkID']))
                continue

            to_node = dst_line.get_to_node()
            from_node = src_line.get_from_node()

            # Check: 분기하는 경우 or 합류하는 경우가 있으므로, 이런 경우는 생성할 필요가 없다
            if (to_node is src_line.get_to_node()) or (from_node is dst_line.get_from_node()):
                continue

            # 차선 변경으로 진입할 선으로 등록
            src_line.set_right_lane_change_dst_link(dst_line)